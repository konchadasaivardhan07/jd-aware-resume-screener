from dataclasses import dataclass
from models.candidate import Candidate
from models.job_description import JobDescription
from config.settings import MatchingConfig


@dataclass
class RuleResult:
    mandatory_skills: str
    skill_match_score: float
    github_present: str
    education_status: str
    experience_status: str
    rule_score: float
    final_status: str
    reasons: list


class RuleEngine:

    @staticmethod
    def evaluate(candidate: Candidate, comparison: dict, jd: JobDescription = None) -> RuleResult:
        """
        Evaluate candidate against JD using rules on skills, education, experience, and profile presence.
        Returns a RuleResult with an overall rule score and step-by-step explanations.
        """
        reasons = []
        
        # -------------------------------------------------------------
        # 1. Required Skill Match Score (Max 35 points)
        # -------------------------------------------------------------
        req_score = comparison.get("required_score", 0.0)
        req_points = round((req_score / 100.0) * 35.0, 2)
        reasons.append(f"Awarded {req_points}/35 points for required skills match ({req_score}% match rate).")

        # Mandatory Skills Pass/Fail Check
        # If JD is provided, we can look at true required missing skills.
        missing_req = []
        if jd:
            req_set = set(s.name for s in jd.required_skills)
            matched_set = set(comparison.get("direct_matched", []))
            # Include fuzzy & implicit in matched
            for k in comparison.get("fuzzy_matched", {}).keys():
                matched_set.add(k)
            for k in comparison.get("implicit_matched", {}).keys():
                matched_set.add(k)
            missing_req = list(req_set - matched_set)
        else:
            missing_req = comparison.get("missing", [])

        if not missing_req:
            mandatory = "PASS"
            reasons.append("Core Skills: All required competencies are met.")
        else:
            mandatory = "FAIL"
            reasons.append(f"Core Skills: Gaps detected in required competencies: {', '.join(missing_req)}.")

        # -------------------------------------------------------------
        # 2. Preferred Skill Match Score (Max 10 points)
        # -------------------------------------------------------------
        pref_score = comparison.get("preferred_score", 0.0)
        pref_points = round((pref_score / 100.0) * 10.0, 2)
        if jd and jd.preferred_skills:
            reasons.append(f"Preferred Skills: Awarded {pref_points}/10 points for matches ({pref_score}% match rate).")
        else:
            pref_points = 10.0
            reasons.append("Preferred Skills: No preferred skills specified by JD; full credit awarded.")

        # -------------------------------------------------------------
        # 3. Education Check (Max 15 points)
        # -------------------------------------------------------------
        edu_status = "PASS"
        edu_points = 15.0

        if jd and jd.education_requirement and jd.education_requirement.lower() != "not specified":
            jd_edu = jd.education_requirement.lower()
            cand_edu = getattr(candidate, "education", "").lower()

            if not cand_edu:
                edu_status = "FAIL"
                edu_points = 0.0
                reasons.append("Education Match: Job description requires education credentials, but none detected in resume.")
            else:
                # Check for degree level match
                levels = {
                    "phd": ["phd", "ph.d", "doctorate"],
                    "master": ["master", "ms", "m.s.", "mtech", "m.tech", "mba"],
                    "bachelor": ["bachelor", "bs", "b.s.", "btech", "b.tech", "degree", "undergrad"]
                }
                
                required_level = "bachelor"
                for level, keywords in levels.items():
                    if any(k in jd_edu for k in keywords):
                        required_level = level
                        break

                candidate_has_required = False
                if required_level == "phd":
                    candidate_has_required = any(k in cand_edu for k in levels["phd"])
                elif required_level == "master":
                    candidate_has_required = any(k in cand_edu for k in levels["master"] + levels["phd"])
                else:
                    candidate_has_required = any(k in cand_edu for k in levels["bachelor"] + levels["master"] + levels["phd"])

                if candidate_has_required:
                    edu_status = "PASS"
                    edu_points = 15.0
                    reasons.append(f"Education Match: Candidate credentials align with the required level ({required_level.capitalize()}).")
                else:
                    edu_status = "FAIL"
                    edu_points = 5.0
                    reasons.append(f"Education Match: Candidate credentials may not meet the required level ({required_level.capitalize()}).")
        else:
            reasons.append("Education Match: No education requirements specified by JD.")

        # -------------------------------------------------------------
        # 4. Experience Check (Max 20 points)
        # -------------------------------------------------------------
        exp_status = "PASS"
        exp_points = 20.0
        cand_exp = getattr(candidate, "experience_years", 0.0)

        if jd and jd.experience_years_required > 0:
            req_exp = jd.experience_years_required
            if cand_exp >= req_exp:
                exp_status = "PASS"
                exp_points = 20.0
                reasons.append(f"Experience Match: Candidate has {cand_exp} years of experience, meeting the required {req_exp} years.")
            elif cand_exp > 0:
                exp_status = "FAIL"
                exp_points = round((cand_exp / req_exp) * 20.0, 2)
                reasons.append(f"Experience Match: Candidate has {cand_exp} years of experience, which is short of the required {req_exp} years.")
            else:
                exp_status = "FAIL"
                exp_points = 0.0
                reasons.append(f"Experience Match: Experience not specified or detected, required: {req_exp} years.")
        else:
            if cand_exp > 0:
                reasons.append(f"Experience Match: Candidate has {cand_exp} years of experience (JD did not specify requirement).")
                exp_points = 20.0
            else:
                reasons.append("Experience Match: Experience not specified in JD or Resume; baseline credit awarded.")
                exp_points = 15.0

        # -------------------------------------------------------------
        # 5. Online Presence Check (Max 10 points)
        # -------------------------------------------------------------
        presence_points = 0.0
        github = "NO"
        
        # GitHub
        if getattr(candidate, "github", "").strip():
            github = "YES"
            presence_points += 3.33
        # LinkedIn
        if getattr(candidate, "linkedin", "").strip():
            presence_points += 3.33
        # Portfolio
        if getattr(candidate, "portfolio", "").strip():
            presence_points += 3.34
            
        presence_points = round(presence_points, 2)
        reasons.append(f"Awarded {presence_points}/10 points for online profile links (GitHub, LinkedIn, Portfolio).")

        # -------------------------------------------------------------
        # 6. Profile & Resume Completeness (Max 10 points)
        # -------------------------------------------------------------
        completeness_score = 0.0
        if candidate.name: completeness_score += 2.0
        if candidate.email: completeness_score += 2.0
        if candidate.phone: completeness_score += 2.0
        if candidate.skills: completeness_score += 2.0
        if candidate.projects: completeness_score += 2.0
        
        candidate.resume_completeness = completeness_score * 10.0 # scale to 100%
        reasons.append(f"Awarded {completeness_score}/10 points for overall profile completeness ({candidate.resume_completeness}% filled).")

        # Calculate Final Rule Score
        total_rule_score = round(req_points + pref_points + edu_points + exp_points + presence_points + completeness_score, 2)
        reasons.append(f"Total Rule Engine Score: {total_rule_score}/100.")

        # Candidate alignment & confidence scores
        candidate.role_alignment = req_score
        
        # Confidence score based on presence of key parsing details
        confidence = 100.0
        if not candidate.email: confidence -= 15.0
        if not candidate.phone: confidence -= 15.0
        if not candidate.experience_years and not candidate.experience_summary: confidence -= 20.0
        if not candidate.education: confidence -= 20.0
        candidate.confidence_score = max(confidence, 10.0)

        # Final Status Decision based on settings thresholds
        shortlist_thresh = MatchingConfig.SHORTLIST_THRESHOLD
        review_thresh = MatchingConfig.REVIEW_THRESHOLD

        if total_rule_score >= shortlist_thresh and mandatory == "PASS":
            status = "SHORTLISTED"
        elif total_rule_score >= review_thresh:
            status = "REVIEW LATER"
        else:
            status = "REJECTED"

        return RuleResult(
            mandatory_skills=mandatory,
            skill_match_score=req_score,
            github_present=github,
            education_status=edu_status,
            experience_status=exp_status,
            rule_score=total_rule_score,
            final_status=status,
            reasons=reasons
        )