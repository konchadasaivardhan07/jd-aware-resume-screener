import os
import re
import json
import logging
import google.generativeai as genai
from models.candidate import Candidate
from services.parser_service import ParserService
from config.settings import AIConfig

logger = logging.getLogger(__name__)


class ResumeParser:
    """Resume parsing operations with regex heuristic baseline and Gemini AI extraction."""

    @staticmethod
    def parse(file_path: str) -> Candidate:
        """
        Parse a resume file.
        """
        candidate = Candidate()
        candidate.resume_text = ParserService.extract_text(file_path)

        # 1. Apply Baseline Heuristics / Regex
        ResumeParser._extract_heuristics(candidate)

        # 2. Refine with Gemini AI if key is present
        api_key = os.getenv("GEMINI_API_KEY") or AIConfig.API_KEY
        if api_key:
            try:
                ResumeParser._extract_with_ai(candidate, api_key)
            except Exception as e:
                logger.error(f"Failed to refine resume with Gemini: {e}")

        return candidate

    @staticmethod
    def _extract_heuristics(candidate: Candidate):
        """Extract details using regex and text patterns."""
        text = candidate.resume_text
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Heuristic Name (first non-empty line is usually candidate name)
        if lines:
            # Clean name (remove symbols, email addresses, etc.)
            first_line = lines[0]
            if len(first_line) < 50 and "@" not in first_line and "resume" not in first_line.lower():
                candidate.name = first_line

        # Email
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        if email_match:
            candidate.email = email_match.group(0)

        # Phone
        phone_match = re.search(r"(\+?\d[\d\-\s\(\)]{8,}\d)", text)
        if phone_match:
            candidate.phone = phone_match.group(0).strip()

        # GitHub
        github_match = re.search(r"(github\.com/[a-zA-Z0-9_-]+)", text, re.IGNORECASE)
        if github_match:
            candidate.github = "https://" + github_match.group(1)

        # LinkedIn
        linkedin_match = re.search(r"(linkedin\.com/in/[a-zA-Z0-9_-]+)", text, re.IGNORECASE)
        if linkedin_match:
            candidate.linkedin = "https://" + linkedin_match.group(1)

        # Portfolio/Website (generic fallback)
        portfolio_match = re.search(r"(portfolio|website|personal-site)\s*[:\-]?\s*([^\s,]+)", text, re.IGNORECASE)
        if portfolio_match:
            candidate.portfolio = portfolio_match.group(2)

        # Education Heuristics
        edu_keywords = [
            "university", "college", "institute", "school", "academy", "degree", 
            "bachelor", "master", "phd", "b.tech", "m.tech", "b.e.", "m.e.", 
            "b.s.", "m.s.", "bsc", "msc", "diploma", "education", "engineering", 
            "technology", "ssc", "cbse", "hsc", "intermediate"
        ]
        edu_lines = []
        for line in lines:
            if any(keyword in line.lower() for keyword in edu_keywords):
                # Avoid duplicates
                if line not in edu_lines:
                    edu_lines.append(line)
        if edu_lines:
            candidate.education = " | ".join(edu_lines[:3])

        # Experience Heuristics (look for years of experience)
        exp_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?\s+(?:of\s+)?experience", text, re.IGNORECASE)
        if exp_match:
            candidate.experience_years = float(exp_match.group(1))

        # Soft skills heuristics
        soft_keywords = ["communication", "leadership", "problem solving", "teamwork", "collaboration", "management", "mentoring", "critical thinking"]
        soft_found = []
        for line in lines:
            for keyword in soft_keywords:
                if keyword in line.lower() and keyword.title() not in soft_found:
                    soft_found.append(keyword.title())
        candidate.soft_skills = soft_found[:5]

        # Certifications Heuristics
        cert_lines = []
        in_cert_section = False
        for line in lines:
            if any(h in line.lower() for h in ["certification", "certifications", "certified in", "licenses"]):
                in_cert_section = True
                continue
            if in_cert_section:
                # If we hit another main header, stop
                if any(h in line.lower() for h in ["experience", "education", "skills", "projects", "summary"]):
                    in_cert_section = False
                elif len(line) < 80:
                    cert_lines.append(line)
        candidate.certifications = cert_lines[:5]

    @staticmethod
    def _extract_with_ai(candidate: Candidate, api_key: str):
        """Use Gemini AI to extract clean, structured candidate profiles."""
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(AIConfig.MODEL_NAME)

        prompt = f"""
You are an expert resume parsing system.
Extract candidate details from the following resume text into a valid JSON object.
Return ONLY the raw JSON. Do not write markdown blocks, headers, or any other explanations.

JSON Schema:
{{
    "name": "Candidate's Full Name (or leave blank if unknown)",
    "email": "Email Address",
    "phone": "Phone Number",
    "github": "GitHub profile URL",
    "linkedin": "LinkedIn profile URL",
    "portfolio": "Portfolio/Personal website URL",
    "education": "Brief description of education (e.g. Master of Science in Computer Science from Stanford University)",
    "experience_years": 4.5,  // float number representing total years of experience, or 0.0 if not specified
    "experience_summary": "Brief summary of work experience",
    "certifications": ["Cert 1", "Cert 2"],
    "soft_skills": ["Soft Skill 1", "Soft Skill 2"],
    "projects": ["Brief summary of Project 1", "Brief summary of Project 2"]
}}

Resume Text:
{candidate.resume_text}
"""
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        try:
            # Clean markdown JSON wraps if present
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "", 1)
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            data = json.loads(raw_text)

            # Update candidate if fields are extracted
            if data.get("name"):
                candidate.name = data["name"]
            if data.get("email"):
                candidate.email = data["email"]
            if data.get("phone"):
                candidate.phone = data["phone"]
            if data.get("github"):
                candidate.github = data["github"]
            if data.get("linkedin"):
                candidate.linkedin = data["linkedin"]
            if data.get("portfolio"):
                candidate.portfolio = data["portfolio"]
            if data.get("education"):
                candidate.education = data["education"]
            if data.get("experience_years") is not None:
                candidate.experience_years = float(data["experience_years"])
            if data.get("experience_summary"):
                candidate.experience_summary = data["experience_summary"]
            if data.get("certifications"):
                candidate.certifications = data["certifications"]
            if data.get("soft_skills"):
                candidate.soft_skills = data["soft_skills"]
            if data.get("projects"):
                candidate.projects = data["projects"]

        except Exception as e:
            logger.warning(f"Error parsing Gemini response in ResumeParser: {e}. Raw text: {response.text}")