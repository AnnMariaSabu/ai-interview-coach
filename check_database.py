"""
check_database.py - Save two fake interviews and read them back.
Uses a separate TEST database, so your real history stays clean.
Run it with: python check_database.py
"""
import config

config.DB_PATH = "data/test_interviews.db"  # use a test file, not the real one

from database import load_interviews, save_interview

save_interview("Priya Nair", "Junior AI Engineer", 67, 3.5, details=[{"note": "fake test"}])
save_interview("Priya Nair", "Junior AI Engineer", 67, 4.1, details=[{"note": "fake test"}])

for interview in load_interviews():
    print(
        f"#{interview['id']}  {interview['date']}  {interview['candidate_name']}  "
        f"{interview['job_title']}  match {interview['match_score']}%  "
        f"score {interview['overall_score']}  details: {interview['details']}"
    )