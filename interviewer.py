"""
interviewer.py - Decide whether to ask a follow-up question after an answer.
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

A STRONG ANSWER SHOULD MENTION:
{key_points}

CONVERSATION ABOUT THIS QUESTION SO FAR:
{conversation}

Decide if you should ask ONE follow-up question.
First check: did the candidate answer EVERY part of the main question?
If a part was not answered, ask about that missing part.
Also ask a follow-up if the answer is vague, too short, misses important key points,
or makes an interesting claim worth checking (for example a number or a result).
Do NOT ask a follow-up if the answer is already clear and complete.

The follow-up must be short, about what the candidate just said, and must not repeat
the main question or an earlier follow-up.
First write your reason, then your decision.
If you do not ask a follow-up, leave "follow_up_question" empty.
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


def decide_follow_up(question: Question, exchanges: list[dict]) -> FollowUpDecision:
    """Should we ask a follow-up? Code handles 'I don't know'; the AI decides the rest."""
    last_answer = exchanges[-1]["answer"]
    if is_dont_know(last_answer):
        return FollowUpDecision(
            reason="The candidate said they don't know, so we move on politely.",
            ask_follow_up=False,
            follow_up_question="",
        )

    prompt = FOLLOW_UP_PROMPT.format(
        question=question.question,
        key_points="\n".join(f"- {point}" for point in question.good_answer_includes),
        conversation=format_conversation(exchanges),
    )
    return ask_for_valid_data(prompt, FollowUpDecision, system=INTERVIEWER_SYSTEM)