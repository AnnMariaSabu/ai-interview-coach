"""
check_all_matches.py - Match every sample resume against every sample job.
Run it with: python check_all_matches.py  (takes a few minutes)
"""
from pathlib import Path

from extractor import extract_candidate, extract_job
from loaders import read_document
from matcher import build_match_report

print("Reading resumes and jobs with the AI...")
candidates = [
    extract_candidate(read_document(str(f)))
    for f in sorted(Path("data/samples/resumes").glob("*.txt"))
]
jobs = [
    extract_job(read_document(str(f)))
    for f in sorted(Path("data/samples/jds").glob("*.txt"))
]

print("\nMATCH SCORES")
for candidate in candidates:
    for job in jobs:
        report = build_match_report(candidate, job)
        print(f"{report.match_score:4}%  {candidate.name:12} vs  {job.job_title}")
        print(f"        Gaps: {', '.join(report.gaps) or 'none'}")