"""
check_scorer.py - Does the judge give low scores to weak answers and high scores to strong ones?
Run it with: python check_scorer.py
"""
from schemas import Question
from scorer import average_score, score_answer

question = Question(
    question="Tell me about a project where you used RAG.",
    type="project",
    based_on="RAG",
    good_answer_includes=[
        "what the project did",
        "how retrieval worked",
        "how wrong answers were prevented",
        "a result or number",
    ],
)

test_answers = {
    "WEAK": "I made a chatbot with RAG. It worked well.",
    "STRONG": (
        "At my internship, employees could not find answers in 500 company documents. "
        "My task was to build an assistant for them. I split the documents into chunks, "
        "stored embeddings in ChromaDB and retrieved the top 3 chunks for each question. "
        "To stop made-up answers, the prompt says to answer only from the documents, and code "
        "returns 'I don't know' when nothing relevant is found. It reached 92% accuracy on 50 test questions."
    ),
}

for label, answer in test_answers.items():
    exchanges = [{"question": question.question, "answer": answer}]
    feedback = score_answer(question, exchanges)

    print(f"\n===== {label} ANSWER =====")
    print(f"Relevance {feedback.relevance.score} | Structure {feedback.structure.score} | "
          f"Specifics {feedback.specifics.score} | Clarity {feedback.clarity.score} | "
          f"Technical {feedback.technical_accuracy.score}  =  {average_score(feedback, question.type)} / 5")
    print(f"Specifics reason: {feedback.specifics.reason}")
    print(f"Good: {feedback.what_was_good}")
    print(f"Improve: {feedback.what_to_improve}")