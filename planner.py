"""
planner.py - Plan the interview questions.
Code chooses WHAT to ask about. The AI writes each question, one at a time.
"""
import config
from extractor import ask_for_valid_data
from schemas import CandidateProfile, InterviewPlan, JobProfile, MatchReport, Question, QuestionDraft

PLANNER_SYSTEM = "You are an experienced, friendly interviewer. Reply only with valid JSON."

# What we tell the AI for each type of question
TYPE_INSTRUCTIONS = {
    "project": "Ask about this project from the candidate's resume. Only use facts written in the project description.",
    "technical": "Ask a technical question that checks the candidate's knowledge of this skill.",
    "gap": "The candidate's resume does not show this skill. Politely ask what they know about it "
           "or how they would learn it. Do not assume they have used it.",
    "behavioural": "Ask a behavioural question that starts with 'Tell me about a time when...' "
                   "related to this job responsibility.",
}

QUESTION_PROMPT = """You are interviewing a candidate for the role: {job_title}.

Write ONE interview question.
Topic: {topic}
Instruction: {instruction}

Keep the question short and clear (one sentence). Ask about ONE thing only.
Also list 2 to 4 key points that a strong answer should mention.

Return ONLY JSON in this shape:
{{"question": "...", "good_answer_includes": ["...", "..."]}}
"""


def normalise(text: str) -> str:
    """Make text easy to compare: small letters, no extra spaces, no full stop at the end."""
    return text.lower().strip().rstrip(".")


def choose_topics(candidate: CandidateProfile, job: JobProfile, report: MatchReport) -> list[tuple[str, str]]:
    """Code decides what to ask about: a list of (type, topic) pairs."""
    required_strengths = [s for s in report.strengths if s in job.required_skills]
    other_strengths = [s for s in report.strengths if s not in job.required_skills]

    topics = []
    for project in candidate.projects[:2]:
        topics.append(("project", project))
    for skill in required_strengths[:3]:
        topics.append(("technical", skill))
    for skill in report.gaps[:2]:
        topics.append(("gap", skill))
    for duty in job.responsibilities[:2]:
        topics.append(("behavioural", duty))

    # Not enough questions yet? Add more from what is left over.
    leftovers = (
        [("technical", s) for s in required_strengths[3:] + other_strengths]
        + [("gap", s) for s in report.gaps[2:]]
        + [("behavioural", d) for d in job.responsibilities[2:]]
    )
    for item in leftovers:
        if len(topics) >= config.MIN_QUESTIONS:
            break
        topics.append(item)

    return topics[: config.MAX_QUESTIONS]


def plan_interview(candidate: CandidateProfile, job: JobProfile, report: MatchReport) -> InterviewPlan:
    """Build the interview plan: code picks the topics, the AI writes one question per topic."""
    questions = []
    topics = choose_topics(candidate, job, report)

    for number, (question_type, topic) in enumerate(topics, start=1):
        print(f"Writing question {number} of {len(topics)}...")
        prompt = QUESTION_PROMPT.format(
            job_title=job.job_title,
            topic=topic,
            instruction=TYPE_INSTRUCTIONS[question_type],
        )
        draft = ask_for_valid_data(prompt, QuestionDraft, system=PLANNER_SYSTEM)
        questions.append(
            Question(
                question=draft.question,
                type=question_type,
                based_on=topic,
                good_answer_includes=draft.good_answer_includes,
            )
        )

    return InterviewPlan(questions=questions)


def check_plan(plan: InterviewPlan, candidate: CandidateProfile, job: JobProfile, report: MatchReport) -> list[str]:
    """Extra checks that Pydantic cannot do. Returns a list of problems (empty = all good)."""
    problems = []

    allowed = (
        job.required_skills + job.responsibilities
        + candidate.skills + candidate.projects
        + report.strengths + report.gaps
    )
    allowed_clean = [normalise(item) for item in allowed]
    for number, q in enumerate(plan.questions, start=1):
        based_on = normalise(q.based_on)
        if based_on in ["", "none", "null"]:
            problems.append(f"Question {number}: based_on is empty.")
        elif not any(based_on in item for item in allowed_clean):
            problems.append(f"Question {number}: based_on '{q.based_on}' is not from the lists.")

    types = [q.type for q in plan.questions]
    for needed in ["technical", "behavioural", "project"]:
        if needed not in types:
            problems.append(f"There is no '{needed}' question.")
    if report.gaps and "gap" not in types:
        problems.append("There are gaps, but no 'gap' question.")

    return problems