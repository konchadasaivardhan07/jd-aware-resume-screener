"""
Candidate Data Model

Represents a candidate after resume parsing.
Every module in the project will update or read
information from this object.
"""

from dataclasses import dataclass, field
from typing import List

from models.skill import Skill


@dataclass(slots=True)
class Candidate:
    """
    Represents one candidate.
    """

    name: str = ""

    email: str = ""

    phone: str = ""

    education: str = ""

    github: str = ""

    linkedin: str = ""

    portfolio: str = ""

    resume_text: str = ""

    skills: List[Skill] = field(default_factory=list)

    projects: List[str] = field(default_factory=list)

    experience_years: float = 0.0

    experience_summary: str = ""

    certifications: List[str] = field(default_factory=list)

    soft_skills: List[str] = field(default_factory=list)

    match_score: float = 0.0

    rule_score: float = 0.0

    semantic_score: float = 0.0

    ai_score: float = 0.0

    role_alignment: float = 0.0

    resume_completeness: float = 0.0

    confidence_score: float = 0.0

    status: str = "Not Evaluated"

    rule_verdict: str = ""

    strengths: List[str] = field(default_factory=list)

    red_flags: List[str] = field(default_factory=list)

    matched_projects: List[str] = field(default_factory=list)

    missing_skills: List[str] = field(default_factory=list)

    improvement_suggestions: List[str] = field(default_factory=list)

    hiring_recommendation: str = ""

    recruiter_notes: str = ""