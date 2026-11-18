"""
scorer.py - Score an answer with the rubric and write friendly feedback.
Very short answers are handled by code (no AI), so nothing gets invented.
Calibration examples (few-shot) show the judge what a 5, a 3 and a 1 look like.
"""
from extractor import ask_for_valid_data
from interviewer import format_conversation
from schemas import AnswerFeedback, CriterionScore, Question

MIN_WORDS_TO_JUDGE = 8  # shorter than this = too short for the AI to judge fairly

JUDGE_SYSTEM = (
    "You are a fair and friendly interview coach. You score answers using a rubric. "
    "Reply only with valid JSON. Keep every text field short."
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

# Calibration examples (few-shot). They use a DIFFERENT question from the eval set, to avoid data leakage.
CALIBRATION_EXAMPLES = """CALIBRATION EXAMPLES (a different question, only to show what each score looks like):

Question: "Tell me about a project where you used Python to automate a task."

Answer that deserves 5 on every criterion:
"At my college library, staff spent 3 hours every week copying book returns into a spreadsheet.
My task was to automate it. I wrote a Python script that reads the return logs, cleans the data
with pandas and updates the spreadsheet. I tested it on 4 weeks of old logs and it matched the
manual sheet exactly. Now the job takes 2 minutes instead of 3 hours."
Why 5: it answers every part, follows STAR, gives numbers, is clear, and uses Python and pandas correctly.

Answer that deserves about 3:
"I wrote a Python script that renames files in a folder automatically. It saved me some time."
Why 3: relevant and clear, but very little detail, no real structure and no numbers.

Answer that deserves 1 on every criterion:
"Python is a very useful language for automation and many companies use it."
Why 1: it does not describe any project, so it does not answer the question."""

SCORING_PROMPT = """Score the candidate's answer in this mock interview.

{examples}

NOW SCORE THIS ANSWER:

QUESTION:
{question}

A STRONG ANSWER SHOULD MENTION:
{key_points}

CONVERSATION (the main answer and any follow-ups):
{conversation}

{rubric}

Rules:
- Use the full range from 1 to 5. Give 5 when the answer is as good as the 5 example, and 1 when it is as weak as the 1 example.
- Check if the answer covers every part of the question.
- Judge the content only, not grammar or English level.
- Only praise or mention things the candidate ACTUALLY said in the conversation. Never invent anything.
- Never ask for things the answer already contains.
- Talk to the candidate directly, using "you". Be friendly and encouraging.

Keep it SHORT:
- Each "reason": ONE short sentence (maximum 15 words). Write the reason first, then the score.
- "what_was_good" and "what_to_improve": 1 or 2 points each, one short sentence per point.
- "weak_example" and "strong_example": 1 or 2 sentences each. Use technical terms correctly.
"""


def count_answer_words(exchanges: list[dict]) -> int:
    """How many words the candidate wrote in total for this question."""
    return sum(len(exchange["answer"].split()) for exchange in exchanges)


def too_short_feedback() -> AnswerFeedback:
    """An honest feedback card for very short answers. Made by code, so nothing is invented."""
    low = CriterionScore(reason="The answer was too short to judge.", score=1)
    return AnswerFeedback(
        relevance=low,
        structure=low,
        specifics=low,
        clarity=low,
        technical_accuracy=low,
        what_was_good=["You gave it a try. That's a start! 😊"],
        what_to_improve=["Give a full answer: the situation, what you did, how you did it, and the result."],
        weak_example="I don't know.",
        strong_example="Use STAR: describe the Situation, your Task, the Actions you took, and a Result with a number.",
    )


def score_answer(question: Question, exchanges: list[dict]) -> AnswerFeedback:
    """Score one answer. Code handles very short answers; the AI judge scores real ones."""
    if count_answer_words(exchanges) < MIN_WORDS_TO_JUDGE:
        return too_short_feedback()

    prompt = SCORING_PROMPT.format(
        examples=CALIBRATION_EXAMPLES,
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