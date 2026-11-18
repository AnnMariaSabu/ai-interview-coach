"""
review_followups.py - Check the quality of the AI's follow-up decisions.
  python review_followups.py generate   (the AI decides on 20 sample answers)
  python review_followups.py auto       (automatic checks, no human rating needed)
  python review_followups.py summary    (count human ratings, if you added any)
"""
import csv
import random
import sys
from pathlib import Path

from interviewer import decide_follow_up
from llm import embed
from matcher import cosine_similarity
from schemas import Question

EVAL_FILE = Path("data/evals/eval_answers.csv")
REVIEW_FILE = Path("data/evals/followup_review.csv")
SAMPLE_SIZE = 20
SEED = 42               # fixed seed = the same "random" 20 answers every time
REPEAT_THRESHOLD = 0.85  # follow-up this similar to the main question = probably a repeat


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def generate():
    """Let the AI decide on follow-ups for 20 sample answers, and save them for review."""
    rows = read_csv(EVAL_FILE)
    sample = random.Random(SEED).sample(rows, SAMPLE_SIZE)
    sample.sort(key=lambda row: int(row["id"]))

    reviewed = []
    for number, row in enumerate(sample, start=1):
        question = Question(
            question=row["question"],
            type=row["type"],
            based_on=row["type"],
            good_answer_includes=[point.strip() for point in row["key_points"].split("|")],
        )
        decision = decide_follow_up(question, [{"question": row["question"], "answer": row["answer"]}])
        print(f"[{number}/{SAMPLE_SIZE}] id {row['id']}: {'FOLLOW-UP' if decision.ask_follow_up else 'no follow-up'}")

        reviewed.append({
            "id": row["id"],
            "question": row["question"],
            "answer": row["answer"],
            "ai_asked": "yes" if decision.ask_follow_up else "no",
            "follow_up": decision.follow_up_question,
            "ai_reason": decision.reason,
            "missing_key_points": " | ".join(decision.missing_key_points),
            "rating": "",
        })

    with open(REVIEW_FILE, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(reviewed[0].keys()))
        writer.writeheader()
        writer.writerows(reviewed)
    print(f"\nSaved to {REVIEW_FILE}.")


def auto():
    """Automatic (proxy) checks: follow-up rate, unnecessary follow-ups, and repeated questions."""
    rows = read_csv(REVIEW_FILE)
    human_scores = {row["id"]: (row.get("human_score") or "").strip() for row in read_csv(EVAL_FILE)}
    n = len(rows)

    # 1. How often did the AI ask a follow-up?
    asked = [row for row in rows if row["ai_asked"] == "yes"]
    print(f"Follow-up check ({n} answers)\n")
    print(f"1. Follow-up rate: the AI asked a follow-up for {len(asked)}/{n} answers ({len(asked) / n:.0%})")

    # 2. Did it ask on answers the human already scored 5 (complete answers)?
    strong = [row for row in rows if human_scores.get(row["id"]) in ("5", "5.0")]
    unnecessary = [row for row in strong if row["ai_asked"] == "yes"]
    if strong:
        print(f"2. Unnecessary follow-ups: on {len(unnecessary)}/{len(strong)} answers you scored 5 "
              f"({len(unnecessary) / len(strong):.0%})")
        for row in unnecessary:
            print(f"     id {row['id']}: {row['follow_up']}")
            if row.get("missing_key_points"):
                print(f"        AI thought missing: {row['missing_key_points']}")

    # 3. Is the follow-up almost the same as the main question? (embeddings + cosine similarity)
    if asked:
        texts = []
        for row in asked:
            texts += [row["question"], row["follow_up"]]
        vectors = embed(texts)
        repeats = []
        for index, row in enumerate(asked):
            similarity = cosine_similarity(vectors[2 * index], vectors[2 * index + 1])
            if similarity >= REPEAT_THRESHOLD:
                repeats.append((row, similarity))
        print(f"3. Similar to the main question: {len(repeats)}/{len(asked)} follow-ups "
              f"(remember: these can still be good, so check them by eye)")
        for row, similarity in repeats:
            print(f"     id {row['id']} ({similarity:.2f}): {row['follow_up']}")

    # 4. Which answers moved on without a follow-up?
    skipped = [row for row in rows if row["ai_asked"] == "no"]
    print(f"4. No follow-up for {len(skipped)}/{n} answers: ids {', '.join(row['id'] for row in skipped) or 'none'}")


def summary():
    """Count human ratings (good / okay / bad), if you added any."""
    rows = [row for row in read_csv(REVIEW_FILE) if (row.get("rating") or "").strip()]
    if not rows:
        print("No ratings yet.")
        return
    counts = {"good": 0, "okay": 0, "bad": 0}
    for row in rows:
        rating = row["rating"].strip().lower()
        if rating in counts:
            counts[rating] += 1
    n = len(rows)
    print(f"Follow-up review ({n} rated)")
    for rating, count in counts.items():
        print(f"  {rating:5}: {count:2}  ({count / n:.0%})")
    print(f"  Good or okay: {(counts['good'] + counts['okay']) / n:.0%}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "generate":
        generate()
    elif mode == "auto":
        auto()
    elif mode == "summary":
        summary()
    else:
        print("Use: python review_followups.py generate | auto | summary")