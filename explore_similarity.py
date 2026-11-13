"""
explore_similarity.py - Experiment: which skill pairs does the AI see as similar?
Run it with: python explore_similarity.py
"""
from llm import embed
from matcher import cosine_similarity

pairs = [
    # Pairs that SHOULD match (same skill, different words)
    ("RAG", "Experience with LLMs and retrieval systems (RAG)"),
    ("FastAPI", "Working with APIs (REST, FastAPI or Flask)"),
    ("SQL", "SQL (complex queries, joins)"),
    ("Python", "3+ years of Python"),
    ("Power BI", "Power BI or Tableau dashboards"),
    # Pairs that should NOT match (different skills)
    ("Excel", "Docker"),
    ("pandas", "Kubernetes"),
    ("Streamlit", "Finance domain knowledge"),
    ("Git", "SQL and basic databases"),
    ("vector databases (ChromaDB)", "SQL and basic databases"),
]

for resume_skill, job_skill in pairs:
    vectors = embed([resume_skill, job_skill])
    score = cosine_similarity(vectors[0], vectors[1])
    print(f"{score:.2f}  {resume_skill:12} vs  {job_skill}")