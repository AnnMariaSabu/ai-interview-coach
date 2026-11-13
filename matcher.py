"""
matcher.py - Compare a candidate profile with a job profile.
"""
import math

import config
from llm import embed
from schemas import CandidateProfile, JobProfile, MatchReport, SkillMatch


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """How much two embeddings point the same way. Higher = more similar meaning."""
    dot_product = sum(x * y for x, y in zip(a, b))
    length_a = math.sqrt(sum(x * x for x in a))
    length_b = math.sqrt(sum(y * y for y in b))
    return dot_product / (length_a * length_b)


def candidate_items(candidate: CandidateProfile) -> list[str]:
    """Everything on the resume that can prove a skill: skills and projects."""
    return candidate.skills + candidate.projects


def match_skills(job_skills: list[str], candidate: CandidateProfile) -> list[SkillMatch]:
    """For each job skill, find the closest resume item and decide: match or gap."""
    items = candidate_items(candidate)
    if not job_skills or not items:
        return []

    job_vectors = embed(job_skills)
    item_vectors = embed(items)

    results = []
    for job_skill, job_vector in zip(job_skills, job_vectors):
        best_score = -1.0
        best_item = ""
        for item, item_vector in zip(items, item_vectors):
            score = cosine_similarity(job_vector, item_vector)
            if score > best_score:
                best_score = score
                best_item = item

        results.append(
            SkillMatch(
                job_skill=job_skill,
                evidence=best_item,
                similarity=round(best_score, 2),
                matched=best_score >= config.MATCH_THRESHOLD,
            )
        )
    return results


def build_match_report(candidate: CandidateProfile, job: JobProfile) -> MatchReport:
    """Compare a candidate with a job: score, strengths and gaps."""
    required = match_skills(job.required_skills, candidate)
    nice_to_have = match_skills(job.nice_to_have_skills, candidate)

    points = 0
    for result in required:
        if result.matched:
            points += config.REQUIRED_WEIGHT
    for result in nice_to_have:
        if result.matched:
            points += config.NICE_TO_HAVE_WEIGHT

    max_points = (
        len(required) * config.REQUIRED_WEIGHT
        + len(nice_to_have) * config.NICE_TO_HAVE_WEIGHT
    )
    score = round(points / max_points * 100) if max_points > 0 else 0

    return MatchReport(
        candidate_name=candidate.name,
        job_title=job.job_title,
        match_score=score,
        strengths=[r.job_skill for r in required + nice_to_have if r.matched],
        gaps=[r.job_skill for r in required if not r.matched],
        details=required + nice_to_have,
    )