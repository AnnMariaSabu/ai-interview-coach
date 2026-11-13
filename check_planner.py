"""
check_planner.py - Build an interview plan for one candidate and one job.
Run it with: python check_planner.py
"""
from extractor import extract_candidate, extract_job
from loaders import read_document
from matcher import build_match_report
from planner import check_plan, plan_interview

RESUME = "data/samples/resumes/rahul_data_analyst.txt"
JOB = "data/samples/jds/junior_ai_engineer.txt"

candidate = extract_candidate(read_document(RESUME))
job = extract_job(read_document(JOB))
report = build_match_report(candidate, job)

print("Planning the interview...")
plan = plan_interview(candidate, job, report)

print(f"\nINTERVIEW PLAN: {candidate.name} for {job.job_title}\n")
for number, q in enumerate(plan.questions, start=1):
    print(f"{number}. [{q.type}] {q.question}")
    print(f"   Based on: {q.based_on}")
    print(f"   Good answer includes: {', '.join(q.good_answer_includes)}\n")

problems = check_plan(plan, candidate, job, report)
if problems:
    print("PROBLEMS FOUND:")
    for problem in problems:
        print(f"  - {problem}")
else:
    print("All checks passed!")