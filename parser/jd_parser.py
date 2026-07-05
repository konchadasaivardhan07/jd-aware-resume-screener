import os
import re
import json
import logging
import google.generativeai as genai
from models.job_description import JobDescription
from models.skill import Skill
from services.parser_service import ParserService
from extractor.skill_extractor import KnowledgeExtractor
from config.settings import AIConfig

logger = logging.getLogger(__name__)


class JDParser:
    """JD parsing operations with regex heuristic baseline and Gemini AI extraction."""

    @staticmethod
    def parse(file_path_or_text: str, is_raw_text: bool = False) -> JobDescription:
        """
        Parse a JD document or raw text.
        """
        jd = JobDescription()
        if is_raw_text:
            jd.raw_text = file_path_or_text
        else:
            jd.raw_text = ParserService.extract_text(file_path_or_text)

        # 1. Baseline Heuristic Extraction
        JDParser._extract_heuristics(jd)

        # 2. Refine with Gemini AI if key is present
        api_key = os.getenv("GEMINI_API_KEY") or AIConfig.API_KEY
        if api_key:
            try:
                JDParser._extract_with_ai(jd, api_key)
            except Exception as e:
                logger.error(f"Failed to refine JD with Gemini: {e}")

        return jd

    @staticmethod
    def _extract_heuristics(jd: JobDescription):
        """Extract job details using regex and basic text processing."""
        text = jd.raw_text
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        # Heuristic Job Title
        if lines:
            first_line = lines[0]
            if len(first_line) < 60 and "job" not in first_line.lower() and "description" not in first_line.lower():
                jd.job_title = first_line
            else:
                jd.job_title = "Software Engineer"  # Default fallback

        # Extract all skills from text using KnowledgeExtractor
        extractor = KnowledgeExtractor()
        extracted_profile = extractor.extract(text)
        
        req_skills = []
        soft_skills = []
        
        for category, skills in extracted_profile.items():
            for s in skills:
                skill_obj = s["skill"]
                if category == "Soft Skills":
                    soft_skills.append(skill_obj.name)
                else:
                    req_skills.append(skill_obj)

        jd.required_skills = req_skills
        jd.preferred_skills = []
        jd.soft_skills_required = soft_skills

        # Education requirements
        edu_keywords = ["degree", "bachelor", "master", "phd", "computer science", "engineering"]
        edu_lines = []
        for line in lines:
            if any(k in line.lower() for k in edu_keywords):
                edu_lines.append(line)
        if edu_lines:
            jd.education_requirement = " | ".join(edu_lines[:2])

        # Experience requirements
        exp_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?\s+(?:of\s+)?experience", text, re.IGNORECASE)
        if exp_match:
            jd.experience_years_required = float(exp_match.group(1))
            jd.experience_required = f"{exp_match.group(0)}"
        else:
            jd.experience_required = "Not Specified"

        # Heuristic responsibilities
        resp_lines = []
        in_resp = False
        for line in lines:
            if any(k in line.lower() for k in ["responsibility", "responsibilities", "what you will do", "duties"]):
                in_resp = True
                continue
            if in_resp:
                if any(k in line.lower() for k in ["requirement", "qualification", "what we look for", "skills", "experience"]):
                    in_resp = False
                elif len(line) < 150 and (line.startswith("-") or line.startswith("*") or line.strip()[0].isdigit() if line.strip() else False):
                    resp_lines.append(line.lstrip("-*0123456789. "))
        jd.responsibilities = resp_lines[:6]

    @staticmethod
    def _extract_with_ai(jd: JobDescription, api_key: str):
        """Use Gemini AI to extract clean, structured Job Description requirements."""
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(AIConfig.MODEL_NAME)

        prompt = f"""
You are an expert Job Description parsing system.
Extract job requirements from the following job description text into a valid JSON object.
Return ONLY the raw JSON. Do not write markdown blocks, headers, or any other explanations.

JSON Schema:
{{
    "job_title": "Job Title (e.g. Senior Software Engineer)",
    "required_skills": ["Skill 1", "Skill 2"],   // technical skills explicitly required (e.g. Python, Docker, React)
    "preferred_skills": ["Skill 1", "Skill 2"],  // nice-to-have or preferred technical skills
    "soft_skills_required": ["Communication", "Leadership"], // soft skills listed in the job description
    "education_requirement": "Education requirement (e.g. BS in Computer Science)",
    "experience_years_required": 5.0,  // float number representing minimum years of experience required
    "experience_required": "Experience requirement summary (e.g. 5+ years of software development experience)",
    "certifications_required": ["AWS Certified...", "Scrum Master"],
    "responsibilities": ["Responsibility 1", "Responsibility 2"]
}}

Job Description Text:
{jd.raw_text}
"""
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        try:
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "", 1)
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            data = json.loads(raw_text)

            if data.get("job_title"):
                jd.job_title = data["job_title"]
            if data.get("education_requirement"):
                jd.education_requirement = data["education_requirement"]
            if data.get("experience_years_required") is not None:
                jd.experience_years_required = float(data["experience_years_required"])
            if data.get("experience_required"):
                jd.experience_required = data["experience_required"]
            if data.get("certifications_required"):
                jd.certifications_required = data["certifications_required"]
            if data.get("responsibilities"):
                jd.responsibilities = data["responsibilities"]
            if data.get("soft_skills_required"):
                jd.soft_skills_required = data["soft_skills_required"]

            # Map skills back to Skill models using standard categories
            extractor = KnowledgeExtractor()
            
            def resolve_skills(skill_names):
                resolved = []
                for name in skill_names:
                    found = False
                    for category, technologies in extractor.knowledge_base.items():
                        if name in technologies:
                            resolved.append(Skill(name=name, category=category))
                            found = True
                            break
                        for sk_name, meta in technologies.items():
                            if name.lower() in [a.lower() for a in meta.get("aliases", [])]:
                                resolved.append(Skill(name=sk_name, category=category))
                                found = True
                                break
                        if found:
                            break
                    if not found:
                        resolved.append(Skill(name=name, category="General"))
                return resolved

            if data.get("required_skills"):
                jd.required_skills = resolve_skills(data["required_skills"])
            if data.get("preferred_skills"):
                jd.preferred_skills = resolve_skills(data["preferred_skills"])

        except Exception as e:
            logger.warning(f"Error parsing Gemini response in JDParser: {e}. Raw text: {response.text}")