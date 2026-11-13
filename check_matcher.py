"""
check_matcher.py - Build a match report for Priya and the Junior AI Engineer job.
Run it with: python check_matcher.py
"""
from extractor import extract_candidate, extract_job
from loaders import read_document
from matcher import build_match_report

candidate = extract_candidate(read_document("data/samples/resumes/priya_ai_engineer.txt"))
job = extract_job(read_document("data/samples/jds/junior_ai_engineer.txt"))

report = build_match_report(candidate, job)

print(f"\n{report.candidate_name}  vs  {report.job_title}")
print(f"Match score: {report.match_score}%")
print(f"Strengths:   {', '.join(report.strengths)}")
print(f"Gaps:        {', '.join(report.gaps)}")

print("\nDetails:")
for result in report.details:
    mark = "YES" if result.matched else "NO "
    print(f"  {mark}  {result.similarity:.2f}  {result.job_skill}")