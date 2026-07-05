"""
Skill Data Model

Represents a single skill identified from either
a Job Description or a Resume.
"""

from dataclasses import dataclass


@dataclass(slots=True)
class Skill:
    """
    Represents a normalized technical skill.
    """

    name: str
    category: str = "General"

    def __str__(self) -> str:
        return self.name