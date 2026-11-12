"""
check_extractor.py - Run the AI extractor on all sample resumes and JDs.
Run it with: python check_extractor.py  (it takes a few minutes)
"""
from pathlib import Path

from extractor import extract_candidate, extract_job
from loaders import read_document

for file in sorted(Path("data/samples/resumes").glob("*.txt")):
    print(f"\n===== RESUME: {file.name} =====")
    profile = extract_candidate(read_document(str(file)))
    print(profile.model_dump_json(indent=2))

for file in sorted(Path("data/samples/jds").glob("*.txt")):
    print(f"\n===== JOB: {file.name} =====")
    job = extract_job(read_document(str(file)))
    print(job.model_dump_json(indent=2))