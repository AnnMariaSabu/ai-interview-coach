"""
interviewer.py - Decide whether to ask a follow-up question after an answer.
The AI first lists the missing key points. Code then decides: nothing missing = no follow-up.
"""
from extractor import ask_for_valid_data
from schemas import FollowUpDecision, Question

INTERVIEWER_SYSTEM = "You are an experienced, friendly interviewer. Reply only with valid JSON."

DONT_KNOW_PHRASES = [
    "don't know", "dont know", "do not know", "no idea", "not sure",
    "no experience", "never used", "skip", "pass",
]

FOLLOW_UP_PROMPT = """You are interviewing a candidate.

MAIN QUESTION:
{question}

KEY POINTS A STRONG ANSWER SHOULD COVER:
{key_points}

CONVERSATION ABOUT THIS QUESTION SO FAR:
{conversation}

Step 1: Compare the candidate's answers with the key points.
In "missing_key_points", list ONLY the key points the candidate did NOT cover. Copy them from the list above.
If the candidate covered every key point, leave "missing_key_points" empty.
Read carefully: never list a key point the candidate already talked about.

Step 2: If an important key point is missing, ask ONE short follow-up question about it.
If nothing important is missing, do not ask a follow-up and leave "follow_up_question" empty.
The follow-up must not repeat the main question or an earlier follow-up.
Write your reason before your decision.
"""


def is_dont_know(answer: str) -> bool:
    """True if the answer is a short 'I don't know' (no AI needed)."""
    text = answer.lower().strip()
    return len(text.split()) <= 8 and any(phrase in text for phrase in DONT_KNOW_PHRASES)


def format_conversation(exchanges: list[dict]) -> str:
    """Turn the questions and answers into a simple script."""
    lines = []
    for exchange in exchanges:
        lines.append(f"Interviewer: {exchange['question']}")
        lines.append(f"Candidate: {exchange['answer']}")
    return "\n".join(lines)


def no_follow_up(reason: str) -> FollowUpDecision:
    """A 'move on' decision made by code."""
    return FollowUpDecision(missing_key_points=[], reason=reason, ask_follow_up=False, follow_up_question="")


def decide_follow_up(question: Question, exchanges: list[dict]) -> FollowUpDecision:
    """The AI lists what is missing; code makes the final decision."""
    last_answer = exchanges[-1]["answer"]
    if is_dont_know(last_answer):
        return no_follow_up("The candidate said they don't know, so we move on politely.")

    prompt = FOLLOW_UP_PROMPT.format(
        question=question.question,
        key_points="\n".join(f"- {point}" for point in question.good_answer_includes),
        conversation=format_conversation(exchanges),
    )
    decision = ask_for_valid_data(prompt, FollowUpDecision, system=INTERVIEWER_SYSTEM)

    # 🐍 Code rule: no missing key points = the answer is complete, so no follow-up
    if not decision.missing_key_points or not decision.follow_up_question.strip():
        decision.ask_follow_up = False
        decision.follow_up_question = ""
    return decision