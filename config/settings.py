"""
HireSense AI - Application Configuration

Author: Konchada Sai Vardhan
Project: HireSense AI (JD-Aware Resume Screener)

Purpose:
---------
This module acts as the single source of truth for the entire application.
All configurable values, paths, thresholds and environment variables
should be managed here.

Every module in the project should import configuration values
from this file instead of hardcoding them.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

# -------------------------------------------------------------------
# Load Environment Variables
# -------------------------------------------------------------------


# -------------------------------------------------------------------
# Environment Variable Helper
# Works both locally (.env) and on Streamlit Cloud (Secrets)
# -------------------------------------------------------------------
load_dotenv()

try:
    import streamlit as st

    def get_env(key: str, default: str = "") -> str:
        try:
            if key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass

        return os.getenv(key, default)

except ImportError:

    def get_env(key: str, default: str = "") -> str:
        return os.getenv(key, default)


# -------------------------------------------------------------------
# Project Paths
# -------------------------------------------------------------------


class PathConfig:
    """Centralized project directory paths."""

    PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

    DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
    ASSETS_DIR: Final[Path] = PROJECT_ROOT / "assets"
    DOCS_DIR: Final[Path] = PROJECT_ROOT / "docs"
    LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"
    TEMP_DIR: Final[Path] = PROJECT_ROOT / "temp"


# -------------------------------------------------------------------
# Application Information
# -------------------------------------------------------------------


class ApplicationConfig:
    """Application metadata."""

    APP_NAME: Final[str] = "HireSense AI"

    REPOSITORY_NAME: Final[str] = "jd-aware-resume-screener"

    VERSION: Final[str] = "1.0.0"

    AUTHOR: Final[str] = "Konchada Sai Vardhan"

    DESCRIPTION: Final[str] = (
        "Explainable JD-Aware Resume Screening Platform"
    )

    DEBUG: Final[bool] = False

    DEFAULT_ENCODING: Final[str] = "utf-8"


# -------------------------------------------------------------------
# File Configuration
# -------------------------------------------------------------------


class FileConfig:
    """Resume and JD upload configuration."""

    SUPPORTED_EXTENSIONS: Final[tuple[str, ...]] = (
        ".pdf",
        ".docx",
    )

    MAX_UPLOAD_FILES: Final[int] = 20

    MAX_FILE_SIZE_MB: Final[int] = 10

    MAX_RESUME_PAGES: Final[int] = 5


# -------------------------------------------------------------------
# Gemini AI Configuration
# -------------------------------------------------------------------


class AIConfig:
    """Gemini model configuration."""

    MODEL_NAME: Final[str] = "gemini-2.5-flash"

    API_KEY: Final[str] = get_env("GEMINI_API_KEY")

    TEMPERATURE: Final[float] = 0.1

    MAX_OUTPUT_TOKENS: Final[int] = 1024


# -------------------------------------------------------------------
# Matching Configuration
# -------------------------------------------------------------------


class MatchingConfig:
    """Thresholds used during candidate evaluation."""

    SHORTLIST_THRESHOLD: Final[int] = 80

    REVIEW_THRESHOLD: Final[int] = 60

    MIN_SCORE: Final[int] = 0

    MAX_SCORE: Final[int] = 100

    RULE_ENGINE_WEIGHT: Final[float] = 0.45

    SEMANTIC_MATCH_WEIGHT: Final[float] = 0.35

    AI_WEIGHT: Final[float] = 0.20


# -------------------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------------------


class LoggingConfig:
    """Application logging configuration."""

    LOG_LEVEL: Final[str] = "INFO"

    LOG_FILE: Final[Path] = PathConfig.LOGS_DIR / "hiresense.log"

    LOG_FORMAT: Final[str] = (
        "%(asctime)s | %(levelname)s | %(message)s"
    )


# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------


def validate_environment() -> tuple[bool, str]:
    """
    Validate required environment variables.

    Returns
    -------
    tuple
        (True, "") if configuration is valid.

        (False, "Reason") otherwise.
    """

    if not AIConfig.API_KEY:
        return (
            False,
            "Gemini API Key not found. "
            "Please configure GEMINI_API_KEY in your .env file or Streamlit Secrets.",
        )

    return True, ""


def create_required_directories() -> None:
    """
    Create required project directories
    if they do not already exist.
    """

    directories = [
        PathConfig.DATA_DIR,
        PathConfig.ASSETS_DIR,
        PathConfig.DOCS_DIR,
        PathConfig.LOGS_DIR,
        PathConfig.TEMP_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)