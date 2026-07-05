"""
Knowledge Extraction Engine

This module extracts structured technical knowledge
from resume or JD text using the knowledge base.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from models.skill import Skill
from config.settings import PathConfig


class KnowledgeExtractor:
    """
    Extracts categorized knowledge from text.
    """

    def __init__(self) -> None:
        knowledge_file = PathConfig.DATA_DIR / "knowledge_base.json"

        with open(
            knowledge_file,
            "r",
            encoding="utf-8"
        ) as file:
            self.knowledge_base = json.load(file)

        synonyms_file = PathConfig.DATA_DIR / "synonyms.json"
        self.synonyms = {}
        if synonyms_file.exists():
            try:
                with open(synonyms_file, "r", encoding="utf-8") as file:
                    self.synonyms = json.load(file)
            except Exception:
                pass

    def extract(self, text: str) -> dict:
        """
        Extract categorized knowledge.

        Parameters
        ----------
        text : str

        Returns
        -------
        dict
        """

        normalized_text = self._normalize(text)

        # Apply synonym substitutions
        for syn_key, syn_val in self.synonyms.items():
            pattern = r"\b" + re.escape(syn_key.lower()) + r"\b"
            normalized_text = re.sub(pattern, syn_val.lower(), normalized_text)

        profile = {}

        for category, technologies in self.knowledge_base.items():

            matches = []

            for skill_name, metadata in technologies.items():

                aliases = metadata["aliases"]

                for alias in aliases:

                    pattern = (
                        r"\b"
                        + re.escape(alias.lower())
                        + r"\b"
                    )

                    if re.search(pattern, normalized_text):

                        matches.append(
    {
        "skill": Skill(
            name=skill_name,
            category=category
        ),
        "matched_text": alias,
        "type": metadata.get("type", "")
    }
)

                        break

            if matches:
                profile[category] = matches

        return profile

    @staticmethod
    def _normalize(text: str) -> str:
        """
        Normalize extracted text.
        """

        text = text.lower()

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text