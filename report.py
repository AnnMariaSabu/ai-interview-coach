"""
report.py - Build the final interview report from the saved scores. No AI needed!
"""
CRITERIA = ["relevance", "structure", "specifics", "clarity", "technical_accuracy"]

LABELS = {
    "relevance": "Relevance",
    "structure": "Structure",
    "specifics": "Specifics",
    "clarity": "Clarity",
    "technical_accuracy": "Technical accuracy",
}

TIPS = {
    "relevance": "answer exactly what was asked, and cover every part of the question.",
    "structure": "use STAR: Situation, Task, Action, Result.",
    "specifics": "add concrete examples, numbers and results.",
    "clarity": "keep answers short and clear, and start with the main point.",
    "technical_accuracy": "revise the technical concepts behind your projects.",
}


def overall_score(details: list[dict]) -> float:
    """The average of all question scores."""
    averages = [entry["average"] for entry in details]
    return round(sum(averages) / len(averages), 1) if averages else 0.0


def criterion_averages(details: list[dict]) -> dict:
    """The average score for each rubric criterion across all questions."""
    result = {}
    for criterion in CRITERIA:
        scores = []
        for entry in details:
            # Technical accuracy does not count for behavioural questions
            if criterion == "technical_accuracy" and entry["question"]["type"] == "behavioural":
                continue
            scores.append(entry["feedback"][criterion]["score"])
        result[criterion] = round(sum(scores) / len(scores), 1) if scores else None
    return result


def best_and_weakest(details: list[dict]) -> tuple[dict, dict]:
    """The question with the highest score and the one with the lowest."""
    best = max(details, key=lambda entry: entry["average"])
    weakest = min(details, key=lambda entry: entry["average"])
    return best, weakest


def practice_list(details: list[dict], gaps: list[str]) -> list[str]:
    """What to practise next: weakest criterion, weakest question, and the job's gaps."""
    items = []

    averages = {c: v for c, v in criterion_averages(details).items() if v is not None}
    weakest_criterion = min(averages, key=averages.get)
    items.append(f"{LABELS[weakest_criterion]} is your weakest area: {TIPS[weakest_criterion]}")

    _, weakest = best_and_weakest(details)
    items.append(f"Practise this question again: \"{weakest['question']['question']}\"")

    for gap in gaps:
        items.append(f"Learn the basics of {gap}. It is required for this job.")
    return items