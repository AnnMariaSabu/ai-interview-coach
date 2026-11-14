"""
app.py - The AI Interview Coach website.
Run it with: streamlit run app.py
"""
from pathlib import Path

import streamlit as st

import config
from extractor import extract_candidate, extract_job
from interviewer import decide_follow_up
from loaders import clean_text, read_document
from matcher import build_match_report
from planner import plan_interview
from schemas import AnswerFeedback
from scorer import average_score, score_answer

SAMPLE_RESUMES = sorted(Path("data/samples/resumes").glob("*.txt"))
SAMPLE_JOBS = sorted(Path("data/samples/jds").glob("*.txt"))
PRIVATE_FOLDER = Path("data/private")  # real resumes go here (ignored by Git)

st.set_page_config(page_title="AI Interview Coach", page_icon="🎤")
st.title("🎤 AI Interview Coach")

# Which screen are we on? Start with "setup" the first time.
if "stage" not in st.session_state:
    st.session_state.stage = "setup"


# ---------- Helpers for the interview ----------

def add_message(role: str, content: str):
    """Save one chat message in memory."""
    st.session_state.messages.append({"role": role, "content": content})


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
    """Add the current planned question to the chat and get ready for answers."""
    plan = st.session_state.plan
    number = st.session_state.question_index
    question = plan.questions[number]

    st.session_state.current_asked = question.question
    st.session_state.exchanges = []
    st.session_state.follow_up_count = 0
    add_message("assistant", f"**Question {number + 1} of {len(plan.questions)}:** {question.question}")


def finish_current_question():
    """Score the answer, show the feedback card, then move to the next question."""
    plan = st.session_state.plan
    question = plan.questions[st.session_state.question_index]

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


def start_interview():
    """Prepare the chat: a welcome message and the first question."""
    report = st.session_state.report
    st.session_state.messages = []
    st.session_state.question_index = 0
    st.session_state.answers = []  # every question + conversation + feedback

    add_message(
        "assistant",
        f"Your match with this role: **{report.match_score}%**\n\n"
        f"💪 **Strengths:** {', '.join(report.strengths) or 'none'}\n\n"
        f"⚠️ **Gaps:** {', '.join(report.gaps) or 'none'}\n\n"
        "Let's begin! Answer each question as you would in a real interview. 😊",
    )
    ask_current_question()


# ---------- Screen 1: setup ----------

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


# ---------- Screen 2: the interview ----------

def show_interview():
    """The chat: one question at a time, with follow-ups and feedback cards."""
    plan = st.session_state.plan

    # Show the whole conversation so far
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # No questions left? The interview is finished.
    if st.session_state.question_index >= len(plan.questions):
        averages = [entry["average"] for entry in st.session_state.answers]
        overall = round(sum(averages) / len(averages), 1)
        st.success(f"🎉 That's the end of the interview! Your overall score: **{overall} / 5**")
        if st.button("Start over"):
            st.session_state.clear()
            st.rerun()
        return

    answer = st.chat_input("Type your answer...")
    if answer:
        # Show and save the answer
        with st.chat_message("user"):
            st.markdown(answer)
        add_message("user", answer)
        st.session_state.exchanges.append({"question": st.session_state.current_asked, "answer": answer})

        # Code checks the limit; the AI decides only if a follow-up is still allowed
        decision = None
        if st.session_state.follow_up_count < config.MAX_FOLLOW_UPS:
            question = plan.questions[st.session_state.question_index]
            with st.spinner("Thinking about your answer..."):
                decision = decide_follow_up(question, st.session_state.exchanges)

        if decision and decision.ask_follow_up and decision.follow_up_question.strip():
            st.session_state.follow_up_count += 1
            st.session_state.current_asked = decision.follow_up_question
            add_message("assistant", f"**Follow-up:** {decision.follow_up_question}")
        else:
            finish_current_question()
        st.rerun()


# Show the right screen for the current stage
if st.session_state.stage == "setup":
    show_setup()
elif st.session_state.stage == "interview":
    show_interview()