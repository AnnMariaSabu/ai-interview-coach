"""
app.py - The AI Interview Coach website.
Run it with: streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st

import config
from database import answers_to_details, load_interviews, save_interview
from extractor import extract_candidate, extract_job
from interviewer import decide_follow_up
from loaders import clean_text, read_document
from matcher import build_match_report
from planner import plan_interview
from report import LABELS, best_and_weakest, criterion_averages, overall_score, practice_list
from schemas import AnswerFeedback
from scorer import average_score, score_answer

SAMPLE_RESUMES = sorted(Path("data/samples/resumes").glob("*.txt"))
SAMPLE_JOBS = sorted(Path("data/samples/jds").glob("*.txt"))
PRIVATE_FOLDER = Path("data/private")  # real resumes go here (ignored by Git)

QUESTION_STARTS = (
    "which", "what", "who", "where", "when", "why", "how",
    "can you", "could you", "sorry", "pardon", "repeat", "clarify",
)

st.set_page_config(page_title="AI Interview Coach", page_icon="🎤")
st.title("🎤 AI Interview Coach")

# Which screen are we on? Start with "setup" the first time.
if "stage" not in st.session_state:
    st.session_state.stage = "setup"


# ---------- Helpers for the interview ----------

def add_message(role: str, content: str):
    """Save one chat message in memory."""
    st.session_state.messages.append({"role": role, "content": content})


def is_clarification(text: str) -> bool:
    """True if the candidate is asking a short question back, with or without a '?'."""
    text = text.strip().lower()
    words = text.split()
    if text.endswith("?") and len(words) <= 15:
        return True
    return len(words) <= 6 and text.startswith(QUESTION_STARTS)


def format_feedback(feedback: AnswerFeedback, average: float, question_type: str) -> str:
    """Turn the judge's feedback into a nice card (Markdown text)."""
    technical = "–" if question_type == "behavioural" else feedback.technical_accuracy.score
    good = "\n".join(f"- {point}" for point in feedback.what_was_good)
    improve = "\n".join(f"- {point}" for point in feedback.what_to_improve)
    return (
        f"### 📊 Feedback: {average} / 5\n\n"
        f"| Relevance | Structure | Specifics | Clarity | Technical |\n"
        f"|---|---|---|---|---|\n"
        f"| {feedback.relevance.score} | {feedback.structure.score} | {feedback.specifics.score} "
        f"| {feedback.clarity.score} | {technical} |\n\n"
        f"**💪 What was good**\n{good}\n\n"
        f"**📈 What to improve**\n{improve}\n\n"
        f"**😕 A weak answer:** {feedback.weak_example}\n\n"
        f"**🌟 A strong answer:** {feedback.strong_example}"
    )


def ask_current_question():
    """Add the current planned question (and its topic) to the chat and get ready for answers."""
    plan = st.session_state.plan
    number = st.session_state.question_index
    question = plan.questions[number]

    st.session_state.current_asked = question.question
    st.session_state.exchanges = []
    st.session_state.follow_up_count = 0
    add_message(
        "assistant",
        f"**Question {number + 1} of {len(plan.questions)}:** {question.question}\n\n"
        f"📌 *Topic: {question.based_on}*",
    )


def finish_current_question():
    """Save the answer. Score it now, or later if FEEDBACK_AT_END is on."""
    plan = st.session_state.plan
    question = plan.questions[st.session_state.question_index]

    if config.FEEDBACK_AT_END:
        st.session_state.answers.append({
            "question": question,
            "exchanges": st.session_state.exchanges,
            "feedback": None,  # scored later, at the end
            "average": None,
        })
    else:
        with st.spinner("Scoring your answer..."):
            feedback = score_answer(question, st.session_state.exchanges)
        average = average_score(feedback, question.type)
        st.session_state.answers.append({
            "question": question,
            "exchanges": st.session_state.exchanges,
            "feedback": feedback,
            "average": average,
        })
        add_message("assistant", format_feedback(feedback, average, question.type))

    st.session_state.question_index += 1
    if st.session_state.question_index < len(plan.questions):
        ask_current_question()


def score_remaining_answers():
    """Score every answer that has no feedback yet, with a progress bar."""
    answers = st.session_state.answers
    progress = st.progress(0.0, text="Scoring your answers...")
    for number, entry in enumerate(answers, start=1):
        if entry["feedback"] is None:
            entry["feedback"] = score_answer(entry["question"], entry["exchanges"])
            entry["average"] = average_score(entry["feedback"], entry["question"].type)
        progress.progress(number / len(answers), text=f"Scoring answer {number} of {len(answers)}...")
    progress.empty()


def start_interview():
    """Prepare the chat: a welcome message and the first question."""
    report = st.session_state.report
    st.session_state.messages = []
    st.session_state.question_index = 0
    st.session_state.answers = []  # every question + conversation + feedback

    feedback_note = (
        "📋 *You'll get your feedback for every question at the end of the interview.*"
        if config.FEEDBACK_AT_END else ""
    )
    add_message(
        "assistant",
        f"Your match with this role: **{report.match_score}%**\n\n"
        f"💪 **Strengths:** {', '.join(report.strengths) or 'none'}\n\n"
        f"⚠️ **Gaps:** {', '.join(report.gaps) or 'none'}\n\n"
        "Let's begin! Answer each question as you would in a real interview. 😊\n\n"
        "💡 *If a question is unclear, just ask me (for example: \"Which project?\").*\n\n"
        f"{feedback_note}",
    )
    ask_current_question()


def finish_interview():
    """Score anything not scored yet, save the interview ONCE, then show the report."""
    score_remaining_answers()
    details = answers_to_details(st.session_state.answers)
    st.session_state.details = details
    save_interview(
        candidate_name=st.session_state.candidate.name,
        job_title=st.session_state.job.job_title,
        match_score=st.session_state.report.match_score,
        overall_score=overall_score(details),
        details=details,
    )
    st.session_state.stage = "report"  # change stage right away, so we never save twice
    st.rerun()


# ---------- Practice screen 1: setup ----------

def show_setup():
    """Pick a resume and a job, then prepare the interview."""
    st.write("Pick a resume and a job, and I'll prepare a mock interview for you.")

    st.subheader("📄 Resume")
    uploaded = st.file_uploader("Upload your resume (PDF, Word or TXT)", type=["pdf", "docx", "txt"])
    sample_resume = st.selectbox("...or use a sample resume", SAMPLE_RESUMES, format_func=lambda p: p.name)

    st.subheader("💼 Job description")
    pasted_jd = st.text_area("Paste a job description", height=150)
    sample_job = st.selectbox("...or use a sample job", SAMPLE_JOBS, format_func=lambda p: p.name)

    if st.button("Prepare my interview", type="primary"):
        if uploaded:
            PRIVATE_FOLDER.mkdir(parents=True, exist_ok=True)
            resume_path = PRIVATE_FOLDER / uploaded.name
            resume_path.write_bytes(uploaded.getvalue())
        else:
            resume_path = sample_resume

        if pasted_jd.strip():
            jd_text = clean_text(pasted_jd)
        else:
            jd_text = read_document(str(sample_job))

        with st.spinner("Reading the resume and the job..."):
            candidate = extract_candidate(read_document(str(resume_path)))
            job = extract_job(jd_text)
        with st.spinner("Comparing your skills with the job..."):
            report = build_match_report(candidate, job)
        with st.spinner("Planning your interview questions..."):
            plan = plan_interview(candidate, job, report)

        st.session_state.candidate = candidate
        st.session_state.job = job
        st.session_state.report = report
        st.session_state.plan = plan
        start_interview()
        st.session_state.stage = "interview"
        st.rerun()


# ---------- Practice screen 2: the interview ----------

def show_interview():
    """The chat: one question at a time, with follow-ups."""
    plan = st.session_state.plan

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # No questions left? Score (if needed), save and go to the report.
    if st.session_state.question_index >= len(plan.questions):
        finish_interview()
        return

    answer = st.chat_input("Type your answer...")
    if answer:
        question = plan.questions[st.session_state.question_index]

        # 🙋‍♀️ The candidate asked a question back: explain the topic, do NOT score it
        if is_clarification(answer):
            add_message("user", answer)
            add_message(
                "assistant",
                f"Good question! 😊 This question is about:\n\n📌 **{question.based_on}**\n\n"
                "Take your time, and answer when you're ready.",
            )
            st.rerun()

        # 💬 A normal answer
        with st.chat_message("user"):
            st.markdown(answer)
        add_message("user", answer)
        st.session_state.exchanges.append({"question": st.session_state.current_asked, "answer": answer})

        # Code checks the limit; the AI decides only if a follow-up is still allowed
        decision = None
        if st.session_state.follow_up_count < config.MAX_FOLLOW_UPS:
            with st.spinner("Thinking about your answer..."):
                decision = decide_follow_up(question, st.session_state.exchanges)

        if decision and decision.ask_follow_up and decision.follow_up_question.strip():
            st.session_state.follow_up_count += 1
            st.session_state.current_asked = decision.follow_up_question
            add_message("assistant", f"**Follow-up:** {decision.follow_up_question}")
        else:
            finish_current_question()
        st.rerun()


# ---------- Practice screen 3: the report ----------

def show_report():
    """The final report: scores, feedback per question, best and weakest answers, practice list."""
    details = st.session_state.details
    match = st.session_state.report

    st.header("📋 Your interview report")
    st.write(f"**{st.session_state.candidate.name}** · {st.session_state.job.job_title}")
    st.success(f"🏆 Overall score: **{overall_score(details)} / 5**  ·  Match with the role: **{match.match_score}%**")
    st.caption("✅ This interview has been saved to your history.")

    st.subheader("📏 Score per criterion")
    rows = "\n".join(
        f"| {LABELS[criterion]} | {value if value is not None else '–'} |"
        for criterion, value in criterion_averages(details).items()
    )
    st.markdown("| Criterion | Average (1-5) |\n|---|---|\n" + rows)

    best, weakest = best_and_weakest(details)
    st.subheader("🌟 Best answer")
    st.write(f"{best['question']['question']}  **({best['average']} / 5)**")
    st.subheader("📈 Weakest answer")
    st.write(f"{weakest['question']['question']}  **({weakest['average']} / 5)**")

    st.subheader("🎯 Your practice list")
    for item in practice_list(details, match.gaps):
        st.write(f"- {item}")

    st.subheader("📝 Feedback for each question")
    for number, entry in enumerate(st.session_state.answers, start=1):
        with st.expander(f"Question {number}: {entry['average']} / 5 · {entry['question'].question}"):
            st.markdown(format_feedback(entry["feedback"], entry["average"], entry["question"].type))

    with st.expander("💬 See the full interview"):
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.button("Start a new interview", type="primary"):
        st.session_state.clear()
        st.rerun()


# ---------- History page ----------

def show_history():
    """All saved interviews for one person, with a progress chart."""
    st.header("📈 Your progress")
    interviews = load_interviews()

    if not interviews:
        st.info("No interviews yet. Finish one, and it will appear here! 😊")
        return

    names = sorted({interview["candidate_name"] for interview in interviews})
    name = st.selectbox("Whose history?", names)
    mine = [interview for interview in interviews if interview["candidate_name"] == name]

    first, latest = mine[0]["overall_score"], mine[-1]["overall_score"]
    change = round(latest - first, 1)
    st.success(
        f"**{len(mine)}** interview(s) so far  ·  Latest score: **{latest} / 5**  ·  "
        f"Change since the first: **{change:+} points**"
    )

    st.subheader("Overall score per interview (1-5)")
    if len(mine) < 2:
        st.caption("Finish at least 2 interviews to see your progress line. 📈")
    else:
        chart_data = pd.DataFrame({
            "Interview number": list(range(1, len(mine) + 1)),
            "Overall score": [interview["overall_score"] for interview in mine],
        })
        st.line_chart(chart_data, x="Interview number", y="Overall score")

    st.subheader("All interviews")
    table_data = pd.DataFrame({
        "#": list(range(1, len(mine) + 1)),
        "Date": [interview["date"] for interview in mine],
        "Job": [interview["job_title"] for interview in mine],
        "Match": [f"{interview['match_score']}%" for interview in mine],
        "Overall score": [interview["overall_score"] for interview in mine],
    })
    st.dataframe(table_data, hide_index=True, use_container_width=True)


# ---------- Which page to show ----------

page = st.sidebar.radio("Menu", ["🎤 Practice", "📈 History"])

if page == "📈 History":
    show_history()
elif st.session_state.stage == "setup":
    show_setup()
elif st.session_state.stage == "interview":
    show_interview()
elif st.session_state.stage == "report":
    show_report()