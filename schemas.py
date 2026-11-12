"""
schemas.py - The shape of the data we expect from the AI.
Pydantic checks that the AI's answers match these shapes.
"""
from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    """What we extract from a resume."""
    name: str
    skills: list[str]
    projects: list[str]
    experience: list[str]
    years_of_experience: float = Field(ge=0, le=50)


class JobProfile(BaseModel):
    """What we extract from a job description."""
    job_title: str
    required_skills: list[str]
    nice_to_have_skills: list[str]
    responsibilities: list[str]