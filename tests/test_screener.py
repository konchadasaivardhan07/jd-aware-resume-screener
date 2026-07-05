import sys
from pathlib import Path

# Add project root to python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import pytest
from services.analysis_service import AnalysisService
from services.parser_service import ParserService
from matcher.semantic_matcher import KnowledgeMatcher
from rules.rule_engine import RuleEngine


def test_parser_service():
    """Verify document parser extracts text from the sample files."""
    resume_path = "data/resume_samples/sample_resume.docx"
    jd_path = "data/jd_samples/sample_jd.docx"
    
    assert Path(resume_path).exists()
    assert Path(jd_path).exists()

    resume_text = ParserService.extract_text(resume_path)
    jd_text = ParserService.extract_text(jd_path)

    assert len(resume_text) > 0
    assert len(jd_text) > 0


def test_matching_and_rules():
    """Verify semantic matching and rule engine evaluation executes and outputs expected fields."""
    resume_path = "data/resume_samples/sample_resume.docx"
    jd_path = "data/jd_samples/sample_jd.docx"
    
    result = AnalysisService.analyze(resume_path, jd_path)

    # Verify keys are returned
    assert "resume" in result
    assert "jd" in result
    assert "comparison" in result
    assert "rule_result" in result
    assert "ai_result" in result

    # Check Candidate object fields
    candidate = result["resume"]
    assert candidate.name != ""
    assert candidate.match_score >= 0.0
    assert candidate.status in ["SHORTLISTED", "REVIEW LATER", "REJECTED"]

    # Check Comparison structure
    comparison = result["comparison"]
    assert "matched" in comparison
    assert "missing" in comparison
    assert "extra" in comparison
    assert "match_percentage" in comparison
    assert "overall_semantic_score" in comparison

    # Check RuleResult structure
    rule = result["rule_result"]
    assert rule.mandatory_skills in ["PASS", "FAIL"]
    assert rule.github_present in ["YES", "NO"]
    assert rule.final_status in ["SHORTLISTED", "REVIEW LATER", "REJECTED"]
    assert len(rule.reasons) > 0

    print("All screening unit tests passed successfully!")


if __name__ == "__main__":
    test_parser_service()
    test_matching_and_rules()
