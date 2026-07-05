import json
import os
import logging
import google.generativeai as genai
from ai.prompts import SYSTEM_PROMPT
from config.settings import AIConfig

logger = logging.getLogger(__name__)


class AIAnalyzer:

    @staticmethod
    def analyze(candidate, jd, comparison, rule_result = None, use_ai: bool = True) -> dict:
        """
        Analyze candidate resume details against JD and rule engine results using Gemini AI.
        If Gemini API key is missing, fails, or use_ai is False, falls back to rule-based evaluation.
        """
        if not use_ai:
            return AIAnalyzer._fallback(candidate, comparison, rule_result, is_fast_mode=True)

        api_key = os.getenv("GEMINI_API_KEY") or AIConfig.API_KEY

        if not api_key:
            return AIAnalyzer._fallback(candidate, comparison, rule_result, is_fast_mode=False)

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=AIConfig.MODEL_NAME,
                system_instruction=SYSTEM_PROMPT
            )

            # Format JD details
            jd_skills_str = ", ".join(str(s) for s in jd.required_skills)
            jd_pref_str = ", ".join(str(s) for s in jd.preferred_skills)
            jd_resp_str = "\n".join(f"- {r}" for r in jd.responsibilities)
            jd_info = (
                f"Job Title: {jd.job_title}\n"
                f"Required Skills: {jd_skills_str}\n"
                f"Preferred Skills: {jd_pref_str}\n"
                f"Education Requirement: {jd.education_requirement}\n"
                f"Experience Requirement: {jd.experience_required}\n"
                f"Responsibilities:\n{jd_resp_str}"
            )

            # Format Candidate details (Stripped Email and Phone for privacy and performance)
            cand_skills_str = ", ".join(str(s) for s in candidate.skills)
            cand_certs_str = ", ".join(candidate.certifications)
            cand_proj_str = "\n".join(f"- {p}" for p in candidate.projects)
            candidate_info = (
                f"Candidate Name: {candidate.name}\n"
                f"Education: {candidate.education}\n"
                f"Experience Years: {candidate.experience_years}\n"
                f"Experience Summary: {candidate.experience_summary}\n"
                f"Certifications: {cand_certs_str}\n"
                f"Projects:\n{cand_proj_str}\n"
                f"Extracted Skills: {cand_skills_str}"
            )

            # Format Matching data
            matched_str = ", ".join(comparison.get("matched", []))
            missing_str = ", ".join(comparison.get("missing", []))
            extra_str = ", ".join(comparison.get("extra", []))
            comparison_info = (
                f"Matched Skills: {matched_str}\n"
                f"Missing Skills: {missing_str}\n"
                f"Extra Skills: {extra_str}\n"
                f"Skill Match Percentage: {comparison.get('skill_match_score', 0)}%\n"
                f"Full-text Cosine Similarity: {comparison.get('semantic_similarity', 0)}%"
            )

            # Format Rule engine checks
            rule_info = "No rule engine verification completed."
            if rule_result:
                rule_info = (
                    f"Rule Engine Overall Score: {rule_result.rule_score}/100\n"
                    f"Mandatory Check: {rule_result.mandatory_skills}\n"
                    f"Education Match: {rule_result.education_status}\n"
                    f"Experience Match: {rule_result.experience_status}\n"
                    f"Verdicts Checklist:\n" + "\n".join(f"- {r}" for r in rule_result.reasons)
                )

            prompt = (
                f"--- JOB DESCRIPTION ---\n{jd_info}\n\n"
                f"--- CANDIDATE PROFILE ---\n{candidate_info}\n\n"
                f"--- METADATA COMPARISON ---\n{comparison_info}\n\n"
                f"--- RULE ENGINE RESULTS ---\n{rule_info}\n\n"
                f"Please conduct your assessment and return the strict JSON schema."
            )

            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "", 1)
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            result = json.loads(raw_text)

            return {
                "ai_fit_score": float(result.get("overall_fit_rating", 50.0)),
                "strengths": result.get("strengths", []),
                "weaknesses": result.get("concerns", []),
                "red_flags": result.get("concerns", []),
                "matched_projects": result.get("suggested_interview_focus", []),
                "missing_skills": result.get("missing_skills", []),
                "improvement_suggestions": result.get("development_recommendations", []),
                "hiring_recommendation": result.get("hiring_recommendation", "REVIEW LATER"),
                "confidence": result.get("confidence_level", "MEDIUM"),
                "recruiter_notes": result.get("executive_summary", ""),
                "summary": result.get("executive_summary", "No summary provided by AI.")
            }

        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}. Falling back to rules.")
            return AIAnalyzer._fallback(candidate, comparison, rule_result)

    @staticmethod
    def _fallback(candidate, comparison, rule_result = None, is_fast_mode: bool = False) -> dict:
        """Fallback rule-based assessment of candidate strengths and gaps."""
        strengths = []
        weaknesses = []
        red_flags = []
        projects = ["Discuss applicant's hands-on project work in experience timeline."]

        matched = comparison.get("matched", [])
        missing = comparison.get("missing", [])

        if matched:
            strengths.append(f"Matches required skills: {', '.join(matched[:5])}")
        if candidate.experience_years > 0:
            strengths.append(f"Has {candidate.experience_years} years of experience.")
        if candidate.github:
            strengths.append("GitHub profile is available for code evaluation.")

        if missing:
            weaknesses.append(f"Lacks key required technology tools: {', '.join(missing[:5])}")
            red_flags.append(f"Missing core competencies: {', '.join(missing[:3])}")
        if rule_result and rule_result.experience_status == "FAIL":
            red_flags.append(f"Candidate's experience ({candidate.experience_years} years) does not meet target requirements.")

        rec = "REVIEW LATER"
        if rule_result:
            if rule_result.final_status == "SHORTLISTED":
                rec = "SHORTLIST"
            elif rule_result.final_status == "REJECTED":
                rec = "REJECT"

        prefix = "Fast Screening Mode" if is_fast_mode else "Rule-Based Fallback Analysis"
        summary = (
            f"{prefix}: Candidate has a skill match of {comparison.get('skill_match_score', 0)}% "
            f"and overall text overlap of {comparison.get('semantic_similarity', 0)}%."
        )

        return {
            "ai_fit_score": float(comparison.get("match_percentage", 50.0)),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "red_flags": red_flags,
            "matched_projects": projects,
            "missing_skills": missing,
            "improvement_suggestions": [f"Highlight candidate development in: {', '.join(missing[:2])}" if missing else "Focus on core technology stack."],
            "hiring_recommendation": rec,
            "confidence": "HIGH" if candidate.confidence_score >= 80 else "MEDIUM",
            "recruiter_notes": "Verify candidate experience checklist and educational degrees.",
            "summary": summary
        }