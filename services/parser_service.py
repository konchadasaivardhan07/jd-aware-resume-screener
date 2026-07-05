"""
Universal Document Parser Service

Reads PDF and DOCX documents
and returns plain extracted text.
"""

from pathlib import Path

import fitz
from docx import Document


class ParserService:
    """Utility class for document parsing."""

    @staticmethod
    def extract_text(file_path: str | Path) -> str:
        """
        Extract text from PDF or DOCX.

        Parameters
        ----------
        file_path : str | Path

        Returns
        -------
        str
            Extracted plain text.
        """

        file_path = Path(file_path)

        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return ParserService._read_pdf(file_path)

        if suffix == ".docx":
            return ParserService._read_docx(file_path)

        if suffix == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        raise ValueError(
            f"Unsupported file format: {suffix}"
        )

    @staticmethod
    def _read_pdf(file_path: Path) -> str:
        """Read PDF."""

        document = fitz.open(file_path)

        pages = []

        for page in document:
            pages.append(page.get_text())

        document.close()

        return "\n".join(pages)

    @staticmethod
    def _read_docx(file_path: Path) -> str:
        """Read DOCX."""

        document = Document(file_path)

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
        ]

        return "\n".join(paragraphs)