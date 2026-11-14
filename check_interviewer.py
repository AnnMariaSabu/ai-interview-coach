"""
check_interviewer.py - Does the AI ask follow-ups for vague answers, but not for strong ones?
Run it with: python check_interviewer.py
"""
from interviewer import decide_follow_up
from schemas import Question

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
    "VAGUE": "I made a chatbot with RAG. It worked well.",
    "STRONG": (
        "I built an assistant that answers employee questions from 500 company documents. "
        "I split the documents into chunks, stored embeddings in ChromaDB and retrieved the "
        "top 3 chunks for each question. To stop made-up answers, the prompt says to answer "
        "only from the documents, and code returns 'I don't know' when nothing relevant is found. "
        "It reached 92% accuracy on 50 test questions."
    ),
}

for label, answer in test_answers.items():
    exchanges = [{"question": question.question, "answer": answer}]
    decision = decide_follow_up(question, exchanges)
    print(f"\n===== {label} ANSWER =====")
    print(f"Ask a follow-up? {decision.ask_follow_up}")
    print(f"Reason: {decision.reason}")
    print(f"Follow-up: {decision.follow_up_question or '(none)'}")