import io
import datetime
import pandas as pd
import fitz  # PyMuPDF
from typing import List


def generate_csv(candidates: List) -> str:
    """Generate a CSV string containing the screening results of all candidates."""
    if not candidates:
        return ""

    data = []
    for c in candidates:
        data.append({
            "Name": c.name,
            "Email": c.email,
            "Phone": c.phone,
            "Education": c.education,
            "Experience Years": c.experience_years,
            "GitHub": c.github,
            "LinkedIn": c.linkedin,
            "Portfolio": c.portfolio,
            "Rule Score": c.rule_score,
            "Semantic Score": c.semantic_score,
            "AI Fit Score": c.ai_score,
            "Weighted Match Score": c.match_score,
            "Screen Status": c.status,
            "Mandatory Skills Check": c.rule_verdict,
            "Role Alignment": getattr(c, "role_alignment", 0.0),
            "Confidence Score": getattr(c, "confidence_score", 0.0),
            "Hiring Recommendation": getattr(c, "hiring_recommendation", "")
        })

    df = pd.DataFrame(data)
    return df.to_csv(index=False)


def generate_summary_report(candidates: List, jd) -> str:
    """Generate a markdown report summarizing the batch candidate screening."""
    if not candidates or not jd:
        return ""

    total = len(candidates)
    shortlisted = sum(1 for c in candidates if c.status == "SHORTLISTED")
    review = sum(1 for c in candidates if c.status == "REVIEW LATER")
    rejected = sum(1 for c in candidates if c.status == "REJECTED")

    avg_score = round(sum(c.match_score for c in candidates) / total, 2) if total > 0 else 0.0

    report = []
    report.append("# HireSense AI - Candidate Screening Summary Report")
    report.append(f"**Job Title:** {jd.job_title}")
    report.append(f"**Total Candidates Processed:** {total}")
    report.append(f"**Average Match Score:** {avg_score}%")
    report.append("")
    report.append("## Recruitment Pipeline Summary")
    report.append(f"- **🟢 Shortlisted:** {shortlisted}")
    report.append(f"- **🟡 Needs Review Later:** {review}")
    report.append(f"- **🔴 Rejected:** {rejected}")
    report.append("")
    report.append("## Shortlisted Candidates Details")
    report.append("| Name | Email | Score | Experience | Key Skills |")
    report.append("| --- | --- | --- | --- | --- |")

    shortlisted_candidates = [c for c in candidates if c.status == "SHORTLISTED"]
    shortlisted_candidates.sort(key=lambda x: x.match_score, reverse=True)

    for c in shortlisted_candidates:
        skills_str = ", ".join(s.name for s in c.skills[:5])
        report.append(f"| {c.name} | {c.email} | {c.match_score}% | {c.experience_years} Years | {skills_str} |")

    report.append("")
    report.append("## Required Skills Required by Job Description")
    report.append(", ".join(s.name for s in jd.required_skills))

    return "\n".join(report)


def generate_candidate_pdf(candidate, jd) -> bytes:
    """Generate a professional, executive-grade candidate assessment PDF report."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 Size

    # Top Header Banner
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(0, 0, 595, 80))
    shape.finish(color=None, fill=(0.09, 0.13, 0.22))  # Slate dark #172237
    shape.commit()

    page.insert_text(fitz.Point(30, 45), "HIRESENSE AI", fontsize=20, color=(1, 1, 1), fontname="helvetica-bold")
    page.insert_text(fitz.Point(30, 62), "EXECUTIVE CANDIDATE ASSESSMENT REPORT", fontsize=10, color=(0.7, 0.7, 0.7), fontname="helvetica")

    page.insert_text(fitz.Point(400, 45), f"Job: {jd.job_title[:30]}", fontsize=10, color=(1, 1, 1), fontname="helvetica-bold")
    date_str = datetime.date.today().strftime("%B %d, %Y")
    page.insert_text(fitz.Point(400, 62), f"Date: {date_str}", fontsize=9, color=(0.7, 0.7, 0.7), fontname="helvetica")

    # Candidate info Block
    page.insert_text(fitz.Point(30, 115), f"Candidate Name: {candidate.name}", fontsize=14, color=(0.1, 0.15, 0.25), fontname="helvetica-bold")
    page.insert_text(fitz.Point(30, 133), f"Email: {candidate.email or 'N/A'}    |    Phone: {candidate.phone or 'N/A'}", fontsize=10, color=(0.3, 0.3, 0.3), fontname="helvetica")
    page.insert_text(fitz.Point(30, 148), f"GitHub: {candidate.github or 'N/A'}    |    LinkedIn: {candidate.linkedin or 'N/A'}", fontsize=10, color=(0.3, 0.3, 0.3), fontname="helvetica")

    shape = page.new_shape()
    shape.draw_line(fitz.Point(30, 165), fitz.Point(565, 165))
    shape.finish(color=(0.85, 0.85, 0.85), width=1)
    shape.commit()

    # Scores
    page.insert_text(fitz.Point(30, 188), "SCREENING ASSESSMENT SUMMARY", fontsize=11, color=(0.09, 0.13, 0.22), fontname="helvetica-bold")

    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(30, 202, 160, 272))
    shape.finish(color=(0.8, 0.8, 0.8), fill=(0.95, 0.96, 0.98), width=1)
    shape.commit()
    page.insert_text(fitz.Point(45, 222), "OVERALL SCORE", fontsize=8, color=(0.5, 0.5, 0.5), fontname="helvetica")
    page.insert_text(fitz.Point(45, 252), f"{candidate.match_score}%", fontsize=22, color=(0.09, 0.13, 0.22), fontname="helvetica-bold")

    page.insert_text(fitz.Point(180, 218), f"Rule Engine Score: {candidate.rule_score} / 100", fontsize=10, color=(0.2, 0.2, 0.2), fontname="helvetica")
    page.insert_text(fitz.Point(180, 235), f"Semantic Match Score: {candidate.semantic_score} %", fontsize=10, color=(0.2, 0.2, 0.2), fontname="helvetica")
    page.insert_text(fitz.Point(180, 252), f"AI Alignment Fit Score: {candidate.ai_score} %", fontsize=10, color=(0.2, 0.2, 0.2), fontname="helvetica")

    status = candidate.status.upper()
    if status == "SHORTLISTED":
        bg_col = (0.9, 0.97, 0.92)
        txt_col = (0.06, 0.46, 0.25)
    elif status == "REVIEW LATER":
        bg_col = (1.0, 0.96, 0.9)
        txt_col = (0.7, 0.45, 0.05)
    else:
        bg_col = (1.0, 0.92, 0.92)
        txt_col = (0.76, 0.09, 0.09)

    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(400, 212, 550, 258))
    shape.finish(color=txt_col, fill=bg_col, width=1.5)
    shape.commit()

    page.insert_text(fitz.Point(415, 240), status, fontsize=10, color=txt_col, fontname="helvetica-bold")

    shape = page.new_shape()
    shape.draw_line(fitz.Point(30, 290), fitz.Point(565, 290))
    shape.finish(color=(0.85, 0.85, 0.85), width=1)
    shape.commit()

    # Strengths vs Red Flags Columns
    page.insert_text(fitz.Point(30, 315), "STRENGTHS & KEY COMPETENCIES", fontsize=11, color=(0.06, 0.46, 0.25), fontname="helvetica-bold")
    y_str = 335
    for strg in candidate.strengths[:4]:
        page.insert_text(fitz.Point(30, y_str), "*", fontsize=12, color=(0.06, 0.46, 0.25), fontname="helvetica-bold")
        page.insert_textbox(fitz.Rect(45, y_str - 10, 290, y_str + 25), strg, fontsize=9, color=(0.2, 0.2, 0.2), fontname="helvetica")
        y_str += 35

    page.insert_text(fitz.Point(310, 315), "RISKS & QUALIFICATION GAPS", fontsize=11, color=(0.76, 0.09, 0.09), fontname="helvetica-bold")
    y_red = 335
    for flag in candidate.red_flags[:4]:
        page.insert_text(fitz.Point(310, y_red), "*", fontsize=12, color=(0.76, 0.09, 0.09), fontname="helvetica-bold")
        page.insert_textbox(fitz.Rect(325, y_red - 10, 565, y_red + 25), flag, fontsize=9, color=(0.2, 0.2, 0.2), fontname="helvetica")
        y_red += 35

    y_max = max(y_str, y_red) + 10

    shape = page.new_shape()
    shape.draw_line(fitz.Point(30, y_max), fitz.Point(565, y_max))
    shape.finish(color=(0.85, 0.85, 0.85), width=1)
    shape.commit()

    # Recruiter notes & Candidate Experience Summary
    page.insert_text(fitz.Point(30, y_max + 20), "EXECUTIVE SCREENING SUMMARY", fontsize=11, color=(0.09, 0.13, 0.22), fontname="helvetica-bold")
    
    summary_text = getattr(candidate, "experience_summary", "") or "No professional experience summary parsed."
    if candidate.recruiter_notes:
        summary_text = f"{candidate.recruiter_notes}\n\nParsed Experience Summary:\n{summary_text}"
        
    page.insert_textbox(fitz.Rect(30, y_max + 32, 565, y_max + 140), summary_text[:500], fontsize=9, color=(0.25, 0.25, 0.25), fontname="helvetica")

    # Footer
    page.insert_text(fitz.Point(30, 810), "Confidential - Generated by HireSense AI Recruitment Portal", fontsize=8, color=(0.6, 0.6, 0.6), fontname="helvetica")
    page.insert_text(fitz.Point(500, 810), "Page 1 of 1", fontsize=8, color=(0.6, 0.6, 0.6), fontname="helvetica")

    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes
