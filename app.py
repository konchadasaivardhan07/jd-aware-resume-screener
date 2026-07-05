"""
HireSense AI
Main Application Entry Point & CLI Dry Run
"""
import sys
from pathlib import Path

# Add project root to python path to resolve imports
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from services.analysis_service import AnalysisService


def main():
    print("=" * 70)
    print("                    HIRESENSE AI")
    print("=" * 70)
    print("\n[NOTE] Streamlit Dashboard available! Run the following command:")
    print("       streamlit run frontend/ui.py")
    print("=" * 70)

    print("\nRunning CLI Dry Run on Sample Data...")
    
    result = AnalysisService.analyze(
        "data/resume_samples/sample_resume.docx",
        "data/jd_samples/sample_jd.docx"
    )

    comparison = result["comparison"]
    rule = result["rule_result"]
    ai = result["ai_result"]

    # ---------------------------------------------------------
    # MATCH SCORE
    # ---------------------------------------------------------

    print("\nMATCH SCORE")
    print("-" * 40)
    print(f"{comparison['match_percentage']} %")

    # ---------------------------------------------------------
    # MATCHED
    # ---------------------------------------------------------

    print("\nMATCHED SKILLS")
    print("-" * 40)

    if comparison["matched"]:
        for skill in comparison["matched"]:
            print(f"[OK] {skill}")
    else:
        print("None")

    # ---------------------------------------------------------
    # MISSING
    # ---------------------------------------------------------

    print("\nMISSING SKILLS")
    print("-" * 40)

    if comparison["missing"]:
        for skill in comparison["missing"]:
            print(f"[MISSING] {skill}")
    else:
        print("None")

    # ---------------------------------------------------------
    # EXTRA
    # ---------------------------------------------------------

    print("\nEXTRA SKILLS")
    print("-" * 40)

    if comparison["extra"]:
        for skill in comparison["extra"]:
            print(f"[EXTRA] {skill}")
    else:
        print("None")

    # ---------------------------------------------------------
    # RULE ENGINE
    # ---------------------------------------------------------

    print("\nRULE ENGINE CHECKLIST")
    print("-" * 40)

    print(f"Mandatory Skills : {rule.mandatory_skills}")
    print(f"GitHub           : {rule.github_present}")
    print(f"Education        : {rule.education_status}")
    print(f"Experience       : {rule.experience_status}")
    print(f"Rule Score       : {rule.rule_score} / 100")
    print(f"Final Decision   : {rule.final_status}")

    print("\nRule Verification Details:")
    for reason in rule.reasons:
        print(f"- {reason}")

    # ---------------------------------------------------------
    # AI ANALYSIS
    # ---------------------------------------------------------

    print("\nAI ASSESSMENT (GEMINI)")
    print("-" * 40)

    print(f"AI Fit Score: {ai.get('ai_fit_score', 0)}/100")

    print("\nStrengths:")
    if ai["strengths"]:
        for strength in ai["strengths"]:
            print(f"- {strength}")
    else:
        print("None")

    print("\nRed Flags:")
    if ai["red_flags"]:
        for flag in ai["red_flags"]:
            print(f"- {flag}")
    else:
        print("None")

    print("\nRelevant Projects:")
    if ai["matched_projects"]:
        for project in ai["matched_projects"]:
            print(f"- {project}")
    else:
        print("None")

    print("\nExecutive Summary:")
    print(ai["summary"])

    print("\n" + "=" * 70)
    print("          END OF ANALYSIS DRY RUN")
    print("=" * 70)


if __name__ == "__main__":
    is_streamlit = False
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is not None:
            is_streamlit = True
    except Exception:
        pass

    if is_streamlit:
        import sys
        import importlib
        # Reload custom project modules to pick up developer edits dynamically (excluding frontend.ui)
        for mod_name in list(sys.modules.keys()):
            if mod_name.startswith(("database", "frontend", "parser", "config")) and mod_name != "frontend.ui":
                try:
                    importlib.reload(sys.modules[mod_name])
                except Exception:
                    pass
        if "frontend.ui" in sys.modules:
            importlib.reload(sys.modules["frontend.ui"])
        else:
            import frontend.ui
    else:
        main()