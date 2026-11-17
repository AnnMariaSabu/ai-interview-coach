"""
run_eval.py - Measure how often the AI judge agrees with the human scores.
Run it with:  python run_eval.py      (all answers, takes a while)
         or:  python run_eval.py 6    (only the first 6 answers, a quick test)
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

from schemas import Question
from scorer import average_score, score_answer

EVAL_FILE = Path("data/evals/eval_answers.csv")
RESULTS_FOLDER = Path("data/evals")


def load_rows(limit: int | None) -> list[dict]:
    """Read the test set. Only rows with a human score are used."""
    with open(EVAL_FILE, encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    rows = [row for row in rows if (row.get("human_score") or "").strip()]
    return rows[:limit] if limit else rows


def judge_row(row: dict) -> dict:
    """Ask the AI judge to score one answer, and compare it with the human score."""
    question = Question(
        question=row["question"],
        type=row["type"],
        based_on=row["type"],
        good_answer_includes=[point.strip() for point in row["key_points"].split("|")],
    )
    exchanges = [{"question": row["question"], "answer": row["answer"]}]

    feedback = score_answer(question, exchanges)
    ai = average_score(feedback, question.type)
    human = float(row["human_score"])

    return {
        "id": row["id"],
        "type": row["type"],
        "human_score": human,
        "ai_score": ai,
        "difference": round(ai - human, 1),
        "unsure": (row.get("unsure") or "").strip().lower() == "yes",
        "ai_what_to_improve": " / ".join(feedback.what_to_improve),
    }


def summarise(results: list[dict], title: str):
    """Print the 3 key numbers for a group of results."""
    if not results:
        return
    n = len(results)
    within_one = sum(1 for r in results if abs(r["difference"]) <= 1)
    average_difference = sum(abs(r["difference"]) for r in results) / n
    direction = sum(r["difference"] for r in results) / n

    print(f"\n{title} ({n} answers)")
    print(f"  Within 1 point of the human: {within_one}/{n} = {within_one / n:.0%}   (target: 80%)")
    print(f"  Average difference:          {average_difference:.2f} points")
    print(f"  Direction:                   {direction:+.2f}  (+ = AI too generous, - = AI too harsh)")


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    rows = load_rows(limit)
    print(f"Judging {len(rows)} answers. This can take a while...\n")

    results = []
    for number, row in enumerate(rows, start=1):
        result = judge_row(row)
        results.append(result)
        flag = "   <-- big disagreement" if abs(result["difference"]) > 1 else ""
        print(f"[{number}/{len(rows)}] id {result['id']:>2}  human {result['human_score']:.0f}  AI {result['ai_score']:.1f}{flag}")

    summarise(results, "ALL ANSWERS")
    if any(r["unsure"] for r in results):
        summarise([r for r in results if not r["unsure"]], "WITHOUT 'UNSURE' ANSWERS")
    for question_type in sorted({r["type"] for r in results}):
        summarise([r for r in results if r["type"] == question_type], f"Type: {question_type}")

    output = RESULTS_FOLDER / f"results_{datetime.now():%Y%m%d_%H%M}.csv"
    with open(output, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"\nSaved detailed results to {output}")


if __name__ == "__main__":
    main()