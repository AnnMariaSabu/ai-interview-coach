"""
extractor.py - Ask the AI to turn resume and JD text into checked, structured data.
"""
from pydantic import BaseModel, ValidationError

from llm import ask_ai
from schemas import CandidateProfile, JobProfile

SYSTEM_PROMPT = "You extract information from documents. Reply only with valid JSON."

RESUME_PROMPT = """Read the resume below and extract information as JSON.

Return ONLY a JSON object with exactly these keys:
- "name": the person's full name (text)
- "skills": a list of skills (list of short texts)
- "projects": a list of projects, each with a short description (list of texts)
- "experience": a list of jobs, each written as "Job title - Company" (list of texts)
- "years_of_experience": total years of work experience (a number)

Only use information written in the resume. Do not invent anything.

RESUME:
{resume_text}
"""


JD_PROMPT = """Read the job description below and extract information as JSON.

Return ONLY a JSON object with exactly these keys:
- "job_title": the job title (text)
- "required_skills": skills the job says are required (list of short texts)
- "nice_to_have_skills": skills the job says are optional or a bonus (list of short texts)
- "responsibilities": what the person will do in the job (list of texts)

Only use information written in the job description. Do not invent anything.

JOB DESCRIPTION:
{jd_text}
"""

def remove_duplicates(items: list[str]) -> list[str]:
    """Remove repeated items but keep the original order."""
    return list(dict.fromkeys(items))


def ask_for_valid_data(prompt: str, schema: type[BaseModel]) -> BaseModel:
    """Ask the AI for JSON, check it with Pydantic, and retry once if it is invalid."""
    for attempt in [1, 2]:
        raw_answer = ask_ai(prompt, system=SYSTEM_PROMPT, json_mode=True)
        try:
            return schema.model_validate_json(raw_answer)
        except ValidationError as error:
            print(f"Attempt {attempt}: the AI's answer was not valid.")
            prompt = (
                prompt
                + "\n\nYour previous answer had these errors:\n"
                + str(error)
                + "\nPlease fix them and return valid JSON."
            )
    raise ValueError("The AI did not return valid data after 2 attempts.")


def extract_candidate(resume_text: str) -> CandidateProfile:
    """Turn resume text into a checked CandidateProfile."""
    prompt = RESUME_PROMPT.format(resume_text=resume_text)
    profile = ask_for_valid_data(prompt, CandidateProfile)

    profile.skills = remove_duplicates(profile.skills)
    profile.projects = remove_duplicates(profile.projects)
    profile.experience = remove_duplicates(profile.experience)
    return profile



def extract_job(jd_text: str) -> JobProfile:
    """Turn job description text into a checked JobProfile."""
    prompt = JD_PROMPT.format(jd_text=jd_text)
    job = ask_for_valid_data(prompt, JobProfile)

    job.required_skills = remove_duplicates(job.required_skills)
    job.nice_to_have_skills = remove_duplicates(job.nice_to_have_skills)
    job.responsibilities = remove_duplicates(job.responsibilities)
    return job