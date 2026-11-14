"""
schemas.py - The shape of the data we expect from the AI.
Pydantic checks that the AI's answers match these shapes.
"""
from typing import Literal

from pydantic import BaseModel, Field

import config


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


class SkillMatch(BaseModel):
    """The result of checking one job skill against the candidate."""
    job_skill: str     # what the job asks for
    evidence: str      # the closest item from the resume
    similarity: float  # how similar they are (higher = closer)
    matched: bool      # True if similarity is above the threshold


class MatchReport(BaseModel):
    """How well a candidate fits a job."""
    candidate_name: str
    job_title: str
    match_score: int = Field(ge=0, le=100)  # a percentage
    strengths: list[str]                    # job skills the candidate has
    gaps: list[str]                         # required skills the candidate is missing
    details: list[SkillMatch]               # the full result for every skill


class QuestionDraft(BaseModel):
    """What the AI writes for ONE topic: a question and its answer key."""
    question: str
    good_answer_includes: list[str] = Field(min_length=2, max_length=4)


class Question(BaseModel):
    """One planned interview question."""
    question: str
    type: Literal["technical", "behavioural", "project", "gap"]
    based_on: str                                          # the job skill or resume item it is about
    good_answer_includes: list[str] = Field(min_length=1)  # key points of a strong answer


class InterviewPlan(BaseModel):
    """The full list of questions for one interview."""
    questions: list[Question] = Field(
        min_length=config.MIN_QUESTIONS,
        max_length=config.MAX_QUESTIONS,
    )



class FollowUpDecision(BaseModel):
    """The AI's decision after hearing an answer."""
    reason: str                # why: written FIRST, so the AI thinks before deciding
    ask_follow_up: bool        # True = ask a follow-up, False = move on
    follow_up_question: str    # the follow-up question (empty if not asking)