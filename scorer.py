"""
scorer.py - Score an answer with the rubric and write friendly feedback.
"""
from extractor import ask_for_valid_data
from interviewer import format_conversation
from schemas import AnswerFeedback, Question

JUDGE_SYSTEM = (
    "You are a fair and friendly interview coach. You score answers using a rubric. "
    "Reply only with valid JSON."
)

RUBRIC = """Score each criterion from 1 to 5:

RELEVANCE - Does the answer respond to EVERY part of the question that was asked?
  1 = off-topic, 3 = answers only some parts of the question, 5 = answers every part
  If any part of the question is not answered, relevance is at most 3.
STRUCTURE - Is there a clear order, for example STAR (Situation, Task, Action, Result)?
  1 = random and confusing, 3 = some order, 5 = clear situation, action and result
SPECIFICS - Are there concrete examples, numbers and results?
  1 = only general words, 3 = one example, 5 = concrete examples with numbers or results
CLARITY - Is it easy to follow, not too long or vague?
  1 = very hard to follow, 3 = understandable but vague in places, 5 = clear and concise
TECHNICAL ACCURACY - Are technical concepts used correctly?
  1 = wrong, 3 = partly correct or shallow, 5 = correct and precise"""

SCORING_PROMPT = """Score the candidate's answer in this mock interview.

QUESTION:
{question}

A STRONG ANSWER SHOULD MENTION:
{key_points}

CONVERSATION (the main answer and any follow-ups):
{conversation}

{rubric}

Rules:
- First list each part of the question, and check if the answer covers it.
- Judge the content only, not grammar or English level.
- Very short or empty answers (like "test" or "I don't know") get 1 for most criteria.
- Before saying something is missing, check the conversation. Never ask for things the answer already contains.
- Give 5 when the answer matches the description of 5. A score of 5 does not mean perfect.
- For each criterion, write the reason first, then the score.
- Talk to the candidate directly, using "you". Be friendly and encouraging.
- "what_was_good" and "what_to_improve": 1 to 3 short points each.
  If a part of the question was not answered, say so in "what_to_improve".
- "weak_example": a short example of a weak answer to the same question.
- "strong_example": a short example of a strong answer to the same question, using STAR where it fits.
  Use technical terms correctly.
"""


def score_answer(question: Question, exchanges: list[dict]) -> AnswerFeedback:
    """Ask the AI judge to score one answer (including its follow-ups)."""
    prompt = SCORING_PROMPT.format(
        question=question.question,
        key_points="\n".join(f"- {point}" for point in question.good_answer_includes),
        conversation=format_conversation(exchanges),
        rubric=RUBRIC,
    )
    return ask_for_valid_data(prompt, AnswerFeedback, system=JUDGE_SYSTEM)


def average_score(feedback: AnswerFeedback, question_type: str) -> float:
    """Code calculates the average. Technical accuracy is skipped for behavioural questions."""
    scores = [
        feedback.relevance.score,
        feedback.structure.score,
        feedback.specifics.score,
        feedback.clarity.score,
    ]
    if question_type != "behavioural":
        scores.append(feedback.technical_accuracy.score)
    return round(sum(scores) / len(scores), 1)