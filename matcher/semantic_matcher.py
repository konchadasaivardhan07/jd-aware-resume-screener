import json
import re
from pathlib import Path
from rapidfuzz import fuzz
from config.settings import PathConfig


class KnowledgeMatcher:

    @staticmethod
    def compare(resume_profile: dict, jd_profile: dict, resume_text: str = "", jd_text: str = "", jd = None) -> dict:
        """
        Compare Resume Knowledge with JD Knowledge using exact, fuzzy, and hierarchical rules,
        differentiating between required and preferred skills, plus text cosine similarity.
        """
        # Load Knowledge Base for implicit relationship resolution
        knowledge_file = PathConfig.DATA_DIR / "knowledge_base.json"
        knowledge_base = {}
        if knowledge_file.exists():
            try:
                with open(knowledge_file, "r", encoding="utf-8") as f:
                    knowledge_base = json.load(f)
            except Exception:
                pass

        # Load Synonyms
        synonyms_file = PathConfig.DATA_DIR / "synonyms.json"
        synonyms = {}
        if synonyms_file.exists():
            try:
                with open(synonyms_file, "r", encoding="utf-8") as f:
                    synonyms = json.load(f)
            except Exception:
                pass

        # 1. Section-aware splitting with strict newline-constrained regex patterns
        sections = KnowledgeMatcher.split_resume_sections(resume_text)

        # 2. Extract candidate skills and calculate evidence weighting
        resume_skills = set()
        resume_skills_lower = {} # lowercase_name -> original_name
        skills_evidence = {}     # lowercase_name -> {"sources": [], "multiplier": 1.0}

        for category, skills in resume_profile.items():
            for item in skills:
                skill_name = item["skill"].name
                resume_skills.add(skill_name)
                resume_skills_lower[skill_name.lower()] = skill_name

                # Gather aliases from knowledge base for evidence checking
                aliases = [skill_name]
                if category in knowledge_base and skill_name in knowledge_base[category]:
                    aliases += knowledge_base[category][skill_name].get("aliases", [])

                # Calculate evidence
                evidence_info = KnowledgeMatcher.calculate_skill_evidence(skill_name, aliases, sections)
                skills_evidence[skill_name.lower()] = evidence_info

        # Segment JD required and preferred skills
        required_names = []
        preferred_names = []

        if jd:
            required_names = [s.name for s in jd.required_skills]
            preferred_names = [s.name for s in jd.preferred_skills]
        else:
            jd_skills = set()
            for _, skills in jd_profile.items():
                for item in skills:
                    jd_skills.add(item["skill"].name)
            required_names = list(jd_skills)

        required_set = set(required_names)
        preferred_set = set(preferred_names)

        # Build dynamic category mappings from knowledge_base (Category Ontology)
        category_mappings = {} # category_lower -> list of child_skill_names_lower
        skill_to_category = {}  # skill_lower -> category_name
        for cat, technologies in knowledge_base.items():
            cat_lower = cat.lower()
            category_mappings[cat_lower] = []
            for skill_name, metadata in technologies.items():
                s_lower = skill_name.lower()
                category_mappings[cat_lower].append(s_lower)
                skill_to_category[s_lower] = cat
                for alias in metadata.get("aliases", []):
                    category_mappings[cat_lower].append(alias.lower())

        # Resolve category pluralization differences
        for cat_lower in list(category_mappings.keys()):
            if cat_lower.endswith("s"):
                category_mappings[cat_lower[:-1]] = category_mappings[cat_lower]
            else:
                category_mappings[cat_lower + "s"] = category_mappings[cat_lower]

        # Helper to normalize required competency names by stripping filler words
        def normalize_competency_name(name: str) -> str:
            cleaned = name.lower()
            fillers = ["languages", "frameworks", "technologies", "development", "applications", "skills", "knowledge", "experience", "restful", "apis", "api"]
            for filler in fillers:
                cleaned = re.sub(r"\b" + re.escape(filler) + r"\b", "", cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            
            if cleaned == "web":
                cleaned = "frontend"
            return cleaned

        # 3. Match Evaluation Flow
        direct_req = resume_skills & required_set
        remaining_req = required_set - direct_req

        fuzzy_req = {}
        fuzzy_threshold = 85.0
        for jd_sk in list(remaining_req):
            for res_sk in resume_skills:
                if res_sk in direct_req:
                    continue
                ratio = fuzz.ratio(jd_sk.lower(), res_sk.lower())
                if ratio >= fuzzy_threshold:
                    fuzzy_req[jd_sk] = {"matched_with": res_sk, "ratio": round(ratio, 2)}
                    remaining_req.remove(jd_sk)
                    break

        def get_related_skills(skill_name):
            for _, technologies in knowledge_base.items():
                if skill_name in technologies:
                    return technologies[skill_name].get("related", [])
            return []

        implicit_req = {}
        recruiter_evidence = {}

        # Evaluate competencies against dynamic category and related-skill graph
        for jd_sk in list(remaining_req):
            jd_sk_lower = jd_sk.lower()
            cleaned_jd = normalize_competency_name(jd_sk_lower)

            # A. Dynamic Category Competency matching (e.g. JD asks for "Databases")
            matched_category = None
            for cat in category_mappings.keys():
                if cleaned_jd == cat or cleaned_jd == cat[:-1] or (cat.endswith("s") and cleaned_jd == cat[:-1]):
                    matched_category = cat
                    break

            if matched_category:
                satisfying = [s for s in category_mappings[matched_category] if s in resume_skills_lower]
                if satisfying:
                    matched_list = [resume_skills_lower[s] for s in satisfying]
                    implicit_req[jd_sk] = matched_list
                    remaining_req.remove(jd_sk)
                    continue

            # B. Substring match to skills / aliases (e.g. "RESTful APIs" -> "REST APIs")
            satisfying_skills = []
            for s_lower, orig_name in resume_skills_lower.items():
                if cleaned_jd and cleaned_jd in s_lower:
                    satisfying_skills.append(orig_name)
            
            if satisfying_skills:
                implicit_req[jd_sk] = satisfying_skills
                remaining_req.remove(jd_sk)
                continue

            # C. Ecosystem / Parent-Child related matching (e.g. JD asks for "Java")
            related = get_related_skills(jd_sk)
            related_present = [r for r in related if r.lower() in resume_skills_lower]
            if related_present:
                implicit_req[jd_sk] = related_present
                remaining_req.remove(jd_sk)
                continue

            # D. Bidirectional mapping (equivalent tool swap)
            if jd_sk_lower in skill_to_category:
                cat_of_sk = skill_to_category[jd_sk_lower]
                equivalent_tools = [resume_skills_lower[s] for s in category_mappings.get(cat_of_sk.lower(), []) if s in resume_skills_lower]
                if equivalent_tools:
                    implicit_req[jd_sk] = equivalent_tools
                    remaining_req.remove(jd_sk)
                    continue

            # E. Direct check against raw resume text (General or custom competencies fallback)
            jd_aliases = [jd_sk_lower]
            for syn_key, syn_val in synonyms.items():
                if syn_val.lower() == jd_sk_lower:
                    jd_aliases.append(syn_key.lower())
                    
            found_in_text = []
            for alias in jd_aliases:
                pattern = r"\b" + re.escape(alias) + r"\b"
                if re.search(pattern, resume_text.lower()):
                    found_in_text.append(alias)
                    
            if cleaned_jd:
                pattern = r"\b" + re.escape(cleaned_jd) + r"\b"
                if re.search(pattern, resume_text.lower()):
                    found_in_text.append(cleaned_jd)

            if found_in_text:
                evidence_info = KnowledgeMatcher.calculate_skill_evidence(jd_sk, found_in_text, sections)
                implicit_req[jd_sk] = [resume_skills_lower.get(f.lower(), jd_sk) for f in found_in_text]
                skills_evidence[jd_sk.lower()] = evidence_info
                remaining_req.remove(jd_sk)
                continue

        # Preferred Skills Matches
        direct_pref = resume_skills & preferred_set
        remaining_pref = preferred_set - direct_pref

        fuzzy_pref = {}
        for jd_sk in list(remaining_pref):
            for res_sk in resume_skills:
                if res_sk in (direct_req | direct_pref):
                    continue
                ratio = fuzz.ratio(jd_sk.lower(), res_sk.lower())
                if ratio >= fuzzy_threshold:
                    fuzzy_pref[jd_sk] = {"matched_with": res_sk, "ratio": round(ratio, 2)}
                    remaining_pref.remove(jd_sk)
                    break

        implicit_pref = {}
        for jd_sk in list(remaining_pref):
            jd_sk_lower = jd_sk.lower()
            cleaned_jd = normalize_competency_name(jd_sk_lower)

            matched_category = None
            for cat in category_mappings.keys():
                if cleaned_jd == cat or cleaned_jd == cat[:-1] or (cat.endswith("s") and cleaned_jd == cat[:-1]):
                    matched_category = cat
                    break

            if matched_category:
                satisfying = [s for s in category_mappings[matched_category] if s in resume_skills_lower]
                if satisfying:
                    implicit_pref[jd_sk] = [resume_skills_lower[s] for s in satisfying]
                    remaining_pref.remove(jd_sk)
                    continue

            satisfying_skills = []
            for s_lower, orig_name in resume_skills_lower.items():
                if cleaned_jd and cleaned_jd in s_lower:
                    satisfying_skills.append(orig_name)
            
            if satisfying_skills:
                implicit_pref[jd_sk] = satisfying_skills
                remaining_pref.remove(jd_sk)
                continue

            related = get_related_skills(jd_sk)
            related_present = [r for r in related if r.lower() in resume_skills_lower]
            if related_present:
                implicit_pref[jd_sk] = related_present
                remaining_pref.remove(jd_sk)
                continue

            if jd_sk_lower in skill_to_category:
                cat_of_sk = skill_to_category[jd_sk_lower]
                equivalent_tools = [resume_skills_lower[s] for s in category_mappings.get(cat_of_sk.lower(), []) if s in resume_skills_lower]
                if equivalent_tools:
                    implicit_pref[jd_sk] = equivalent_tools
                    remaining_pref.remove(jd_sk)
                    continue

            # Raw text check for preferred
            jd_aliases = [jd_sk_lower]
            for syn_key, syn_val in synonyms.items():
                if syn_val.lower() == jd_sk_lower:
                    jd_aliases.append(syn_key.lower())
                    
            found_in_text = []
            for alias in jd_aliases:
                pattern = r"\b" + re.escape(alias) + r"\b"
                if re.search(pattern, resume_text.lower()):
                    found_in_text.append(alias)
                    
            if cleaned_jd:
                pattern = r"\b" + re.escape(cleaned_jd) + r"\b"
                if re.search(pattern, resume_text.lower()):
                    found_in_text.append(cleaned_jd)

            if found_in_text:
                evidence_info = KnowledgeMatcher.calculate_skill_evidence(jd_sk, found_in_text, sections)
                implicit_pref[jd_sk] = [resume_skills_lower.get(f.lower(), jd_sk) for f in found_in_text]
                skills_evidence[jd_sk.lower()] = evidence_info
                remaining_pref.remove(jd_sk)
                continue

        # 4. Generate Recruiter Confidence & Match Evidence details
        # Exact/Fuzzy required evidence
        for jd_sk in list(direct_req):
            ev_info = skills_evidence.get(jd_sk.lower(), {"sources": ["Resume Text"], "multiplier": 1.0})
            confidence_pct = min(int(100 * ev_info["multiplier"]), 100)
            recruiter_evidence[jd_sk] = {
                "confidence": f"High ({confidence_pct}%)" if confidence_pct >= 120 else "Medium (100%)" if confidence_pct >= 100 else "Low (80%)",
                "details": [f"{jd_sk} ({src})" for src in ev_info["sources"]]
            }

        for jd_sk, fuzzy_data in fuzzy_req.items():
            matched_name = fuzzy_data["matched_with"]
            ev_info = skills_evidence.get(matched_name.lower(), {"sources": ["Resume Text"], "multiplier": 1.0})
            confidence_pct = min(int(90 * ev_info["multiplier"]), 100)
            recruiter_evidence[jd_sk] = {
                "confidence": f"High ({confidence_pct}%)" if confidence_pct >= 90 else "Medium (80%)",
                "details": [f"{matched_name} ({src}) - exact match equivalent" for src in ev_info["sources"]]
            }

        # Implicit/Category required evidence
        for jd_sk, matched_list in implicit_req.items():
            details = []
            best_mult = 1.0
            for m_sk in matched_list:
                ev_info = skills_evidence.get(m_sk.lower(), {"sources": ["Resume Text"], "multiplier": 1.0})
                best_mult = max(best_mult, ev_info["multiplier"])
                for src in ev_info["sources"]:
                    details.append(f"{m_sk} ({src})")
            
            confidence_pct = min(int(85 * best_mult), 100)
            conf_str = "High" if confidence_pct >= 90 else "Medium" if confidence_pct >= 75 else "Low"
            recruiter_evidence[jd_sk] = {
                "confidence": f"{conf_str} ({confidence_pct}%)",
                "details": details
            }

        # Handle preferred evidence
        for jd_sk in list(direct_pref):
            ev_info = skills_evidence.get(jd_sk.lower(), {"sources": ["Resume Text"], "multiplier": 1.0})
            confidence_pct = min(int(100 * ev_info["multiplier"]), 100)
            recruiter_evidence[jd_sk] = {
                "confidence": f"High ({confidence_pct}%)",
                "details": [f"{jd_sk} ({src}) - preferred" for src in ev_info["sources"]]
            }

        for jd_sk, fuzzy_data in fuzzy_pref.items():
            matched_name = fuzzy_data["matched_with"]
            ev_info = skills_evidence.get(matched_name.lower(), {"sources": ["Resume Text"], "multiplier": 1.0})
            confidence_pct = min(int(90 * ev_info["multiplier"]), 100)
            recruiter_evidence[jd_sk] = {
                "confidence": f"Medium ({confidence_pct}%)",
                "details": [f"{matched_name} ({src}) - preferred" for src in ev_info["sources"]]
            }

        for jd_sk, matched_list in implicit_pref.items():
            details = []
            best_mult = 1.0
            for m_sk in matched_list:
                ev_info = skills_evidence.get(m_sk.lower(), {"sources": ["Resume Text"], "multiplier": 1.0})
                best_mult = max(best_mult, ev_info["multiplier"])
                for src in ev_info["sources"]:
                    details.append(f"{m_sk} ({src}) - preferred")
            
            confidence_pct = min(int(80 * best_mult), 100)
            recruiter_evidence[jd_sk] = {
                "confidence": f"Medium ({confidence_pct}%)",
                "details": details
            }

        # 5. Missing Skill Explanations
        missing_explanations = {}
        for jd_sk in list(remaining_req | remaining_pref):
            jd_sk_lower = jd_sk.lower()
            related = get_related_skills(jd_sk)
            
            if related:
                missing_explanations[jd_sk] = f"No direct mentions, or related frameworks ({', '.join(related[:3])}) found in candidate profiles."
            else:
                missing_explanations[jd_sk] = "No matching keywords or category competencies detected in candidate profile."

        # Combine matches for displays
        matched = sorted(list(direct_req | direct_pref))
        fuzzy_matches = {**fuzzy_req, **fuzzy_pref}
        fuzzy_list = [f"{k} (Fuzzy via {v['matched_with']})" for k, v in fuzzy_matches.items()]
        
        implicit_matches = {**implicit_req, **implicit_pref}
        implicit_list = [f"{k} (Implicit via {', '.join(v)})" for k, v in implicit_matches.items()]

        all_matched = matched + fuzzy_list + implicit_list
        missing = sorted(list(remaining_req | remaining_pref))
        extra = sorted(list(resume_skills - (direct_req | direct_pref) - set(v["matched_with"] for v in fuzzy_matches.values()) - set(sum(implicit_matches.values(), []))))

        # Weighted Skill match calculation (Differentiated scoring weights)
        # Required: 85% weight, Preferred: 15% weight
        num_req = len(required_set)
        if num_req == 0:
            req_score = 100.0
        else:
            # Scale matches based on evidence multipliers
            scaled_direct = 0.0
            for sk in direct_req:
                mult = skills_evidence.get(sk.lower(), {}).get("multiplier", 1.0)
                scaled_direct += min(1.0 * mult, 1.25)  # Cap boost to prevent score inflation

            scaled_fuzzy = 0.0
            for sk, val in fuzzy_req.items():
                mult = skills_evidence.get(val["matched_with"].lower(), {}).get("multiplier", 1.0)
                scaled_fuzzy += min(0.9 * mult, 1.1)

            scaled_implicit = 0.0
            for sk, val in implicit_req.items():
                best_mult = max([skills_evidence.get(m.lower(), {}).get("multiplier", 1.0) for m in val])
                scaled_implicit += min(0.85 * best_mult, 1.0) # Upgraded implicit match score weight to 0.85

            req_score = round(
                ((scaled_direct + scaled_fuzzy + scaled_implicit) / num_req) * 100,
                2
            )
            req_score = min(req_score, 100.0)

        num_pref = len(preferred_set)
        if num_pref == 0:
            pref_score = 100.0
            skill_score = req_score
        else:
            scaled_direct_p = sum(min(1.0 * skills_evidence.get(sk.lower(), {}).get("multiplier", 1.0), 1.25) for sk in direct_pref)
            scaled_fuzzy_p = sum(min(0.9 * skills_evidence.get(val["matched_with"].lower(), {}).get("multiplier", 1.0), 1.1) for sk, val in fuzzy_pref.items())
            scaled_implicit_p = sum(min(0.85 * max([skills_evidence.get(m.lower(), {}).get("multiplier", 1.0) for m in val]), 1.0) for sk, val in implicit_pref.items())

            pref_score = round(
                ((scaled_direct_p + scaled_fuzzy_p + scaled_implicit_p) / num_pref) * 100,
                2
            )
            pref_score = min(pref_score, 100.0)
            skill_score = round((req_score * 0.85) + (pref_score * 0.15), 2)

        # Cosine similarity
        cosine_sim = KnowledgeMatcher._calculate_cosine_similarity(resume_text, jd_text)

        # Combined Semantic Score (75% Skill Match, 25% Cosine text similarity)
        overall_score = round((skill_score * 0.75) + (cosine_sim * 0.25), 2)
        overall_score = min(overall_score, 100.0)

        return {
            "matched": all_matched,
            "direct_matched": matched,
            "fuzzy_matched": fuzzy_matches,
            "implicit_matched": implicit_matches,
            "missing": missing,
            "extra": extra,
            "skill_match_score": skill_score,
            "required_score": req_score,
            "preferred_score": pref_score,
            "semantic_similarity": cosine_sim,
            "match_percentage": overall_score,
            "overall_semantic_score": overall_score,
            "recruiter_evidence": recruiter_evidence,
            "missing_explanations": missing_explanations
        }

    @staticmethod
    def split_resume_sections(text: str) -> dict:
        """Split resume into functional segments to track source locations."""
        sections = {"experience": "", "projects": "", "skills": "", "certifications": "", "other": ""}
        normalized = text.lower()
        
        headers = {
            "experience": ["work experience", "experience", "employment", "professional experience", "internships", "work history"],
            "projects": ["projects", "personal projects", "academic projects"],
            "skills": ["skills", "technical skills", "competencies", "expertise", "technologies"],
            "certifications": ["certifications", "licenses", "courses", "credentials"]
        }
        
        indices = []
        for key, keywords in headers.items():
            for keyword in keywords:
                pattern = r"(?:^|\n)\s*" + re.escape(keyword) + r"\s*(?:\n|$)"
                match = re.search(pattern, normalized)
                if match:
                    indices.append((match.start(), key))
                    break
                    
        indices.sort()
        if not indices:
            sections["other"] = text
            return sections
            
        first_idx, first_key = indices[0]
        sections["other"] = text[:first_idx]
        
        for i in range(len(indices)):
            start_idx, key = indices[i]
            end_idx = indices[i+1][0] if i + 1 < len(indices) else len(text)
            sections[key] = text[start_idx:end_idx]
            
        return sections

    @staticmethod
    def calculate_skill_evidence(skill_name: str, aliases: list, sections: dict) -> dict:
        """Assess the section origin and credibility weighting multiplier for a skill."""
        evidence = []
        score_mult = 1.0
        
        for alias in aliases:
            pattern = r"\b" + re.escape(alias.lower()) + r"\b"
            if sections["experience"] and re.search(pattern, sections["experience"].lower()):
                if "Work Experience" not in evidence:
                    evidence.append("Work Experience")
                score_mult = max(score_mult, 1.25)
            if sections["projects"] and re.search(pattern, sections["projects"].lower()):
                if "Project Work" not in evidence:
                    evidence.append("Project Work")
                score_mult = max(score_mult, 1.15)
            if sections["certifications"] and re.search(pattern, sections["certifications"].lower()):
                if "Certification" not in evidence:
                    evidence.append("Certification")
                score_mult = max(score_mult, 1.1)
            if sections["skills"] and re.search(pattern, sections["skills"].lower()):
                if "Skills List" not in evidence:
                    evidence.append("Skills List")
                score_mult = max(score_mult, 1.0)
                
        if not evidence:
            evidence.append("Resume Text")
            
        return {
            "sources": evidence,
            "multiplier": score_mult
        }

    @staticmethod
    def _calculate_cosine_similarity(text1: str, text2: str) -> float:
        """Calculate word-level TF Cosine Similarity between two texts."""
        if not text1 or not text2:
            return 0.0

        words1 = re.findall(r"\w+", text1.lower())
        words2 = re.findall(r"\w+", text2.lower())

        freq1 = {}
        for w in words1:
            freq1[w] = freq1.get(w, 0) + 1

        freq2 = {}
        for w in words2:
            freq2[w] = freq2.get(w, 0) + 1

        all_words = set(freq1.keys()) | set(freq2.keys())
        dot_product = sum(freq1.get(w, 0) * freq2.get(w, 0) for w in all_words)
        mag1 = sum(val**2 for val in freq1.values())**0.5
        mag2 = sum(val**2 for val in freq2.values())**0.5

        if mag1 * mag2 == 0:
            return 0.0

        return round((dot_product / (mag1 * mag2)) * 100, 2)
