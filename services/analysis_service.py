from parser.resume_parser import ResumeParser
from parser.jd_parser import JDParser
from ai.ai_analyzer import AIAnalyzer
from extractor.skill_extractor import KnowledgeExtractor
from matcher.semantic_matcher import KnowledgeMatcher
from rules.rule_engine import RuleEngine
from config.settings import MatchingConfig


class AnalysisService:

    @staticmethod
    def analyze(resume_path: str, jd_path: str, use_ai: bool = True) -> dict:
        """
        Coordinate the full resume screening pipeline:
        1. Parse JD & Resume.
        2. Extract skills using the Knowledge Base.
        3. Perform fuzzy, exact, and implicit semantic matching.
        4. Evaluate structured rule engine checklist.
        5. Run Gemini AI fit analysis (if use_ai is True).
        6. Compute the composite weighted match score.
        """
        # Parse Resume & JD
        resume = ResumeParser.parse(resume_path)
        jd = JDParser.parse(jd_path)

        # Extract Resume Skills using KnowledgeExtractor
        extractor = KnowledgeExtractor()
        resume_profile = extractor.extract(resume.resume_text)
        
        # Populate candidate skills list
        cand_skills = []
        for _, skills in resume_profile.items():
            for item in skills:
                cand_skills.append(item["skill"])
        resume.skills = cand_skills

        # For JD, extract skills to build jd_profile if not already populated
        jd_profile = extractor.extract(jd.raw_text)

        # Compare Resume profile against JD profile
        comparison = KnowledgeMatcher.compare(
            resume_profile,
            jd_profile,
            resume.resume_text,
            jd.raw_text,
            jd
        )

        # Evaluate rule-based status
        rule_result = RuleEngine.evaluate(
            resume,
            comparison,
            jd
        )

        # Run AI analysis
        ai_result = AIAnalyzer.analyze(
            resume,
            jd,
            comparison,
            rule_result,
            use_ai
        )

        # Calculate final weighted composite score
        rule_wt = MatchingConfig.RULE_ENGINE_WEIGHT
        sem_wt = MatchingConfig.SEMANTIC_MATCH_WEIGHT
        ai_wt = MatchingConfig.AI_WEIGHT

        rule_score = rule_result.rule_score
        semantic_score = comparison["overall_semantic_score"]
        ai_score = ai_result["ai_fit_score"]

        final_score = round(
            (rule_score * rule_wt) +
            (semantic_score * sem_wt) +
            (ai_score * ai_wt),
            2
        )

        # Authoritative decision derived from final Overall Fit score
        shortlist_thresh = MatchingConfig.SHORTLIST_THRESHOLD
        review_thresh = MatchingConfig.REVIEW_THRESHOLD
        if final_score >= shortlist_thresh:
            status = "SHORTLISTED"
        elif final_score >= review_thresh:
            status = "REVIEW LATER"
        else:
            status = "REJECTED"

        # Populate candidate summary details
        resume.match_score = final_score
        resume.rule_score = rule_score
        resume.semantic_score = semantic_score
        resume.ai_score = ai_score
        resume.status = status
        resume.hiring_recommendation = status
        rule_result.final_status = status

        resume.rule_verdict = rule_result.mandatory_skills
        resume.strengths = ai_result["strengths"]
        resume.red_flags = ai_result["red_flags"]
        resume.matched_projects = ai_result["matched_projects"]
        
        # Extended ATS fields mapping
        if ai_result.get("soft_skills"):
            resume.soft_skills = ai_result["soft_skills"]
        resume.missing_skills = ai_result.get("missing_skills", [])
        resume.improvement_suggestions = ai_result.get("improvement_suggestions", [])
        resume.hiring_recommendation = ai_result.get("hiring_recommendation", "REVIEW LATER")
        resume.recruiter_notes = ai_result.get("recruiter_notes", "")

        # If name is still empty, fallback to filename
        if not resume.name:
            import os
            resume.name = os.path.splitext(os.path.basename(resume_path))[0].replace("_", " ").title()

        return {
            "resume": resume,
            "jd": jd,
            "comparison": comparison,
            "rule_result": rule_result,
            "ai_result": ai_result
        }