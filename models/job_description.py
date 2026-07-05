"""
Job Description Data Model

Represents a parsed Job Description.
"""

from dataclasses import dataclass, field
from typing import List

from models.skill import Skill


@dataclass(slots=True)
class JobDescription:
    """
    Represents one parsed Job Description.
    """

    job_title: str = ""

    raw_text: str = ""

    required_skills: List[Skill] = field(default_factory=list)

    preferred_skills: List[Skill] = field(default_factory=list)

    role_keywords: List[str] = field(default_factory=list)

    education_requirement: str = ""

    experience_required: str = ""

    experience_years_required: float = 0.0

    certifications_required: List[str] = field(default_factory=list)

    responsibilities: List[str] = field(default_factory=list)

    soft_skills_required: List[str] = field(default_factory=list)