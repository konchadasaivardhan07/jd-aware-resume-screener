import sys
from pathlib import Path
import os
import textwrap

# Add project root to python path to resolve ModuleNotFoundError
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
from config.settings import PathConfig, AIConfig, MatchingConfig
from services.analysis_service import AnalysisService
from parser.jd_parser import JDParser
from dashboard.charts import (
    plot_status_distribution,
    plot_score_distribution,
    plot_skill_frequency,
    plot_experience_distribution,
    plot_education_distribution,
    plot_candidate_quality_distribution
)
from dashboard.reports import generate_csv, generate_summary_report, generate_candidate_pdf
from frontend.components import (
    inject_custom_css,
    render_metric_card,
    render_candidate_header,
    get_status_badge_html
)
from frontend.auth_ui import render_auth_page

def build_local_hiring_insights(results, jd):
    """Build a high-quality local summary of results if AI is unavailable."""
    candidates = [r["resume"] for r in results]
    total = len(candidates)
    shortlisted = [c.name for c in candidates if c.status == "SHORTLISTED"]
    review = [c.name for c in candidates if c.status == "REVIEW LATER"]
    
    # Identify common missing skills
    missing_counts = {}
    for r in results:
        for m in r.get("comparison", {}).get("missing", []):
            missing_counts[m] = missing_counts.get(m, 0) + 1
    top_missing = sorted(missing_counts.items(), key=lambda x: x[1], reverse=True)[:2]
    missing_str = ", ".join(k for k, v in top_missing) if top_missing else "None detected"
    
    # Build markdown
    md = []
    md.append("### AI Hiring Insights")
    md.append(f"• **Executive Pool Summary**: Evaluated {total} candidates for the {jd.job_title} role.")
    
    if shortlisted:
        md.append(f"• **Key Matches**: {', '.join(shortlisted)} demonstrate strong alignment with required parameters.")
    else:
        md.append("• **Key Matches**: No candidates met the primary shortlist criteria in the initial scan.")
        
    if review:
        md.append(f"• **Talent Trends**: {len(review)} candidate(s) ({', '.join(review)}) show transferable skills but require validation of experience.")
        
    md.append(f"• **Skills Gaps**: {missing_str} are the most frequently missing requirements in this batch.")
    
    # Recommendation
    if shortlisted:
        rec = f"Proceed with interviewing the shortlisted candidates ({', '.join(shortlisted)}) and verify missing competencies."
    elif review:
        rec = f"Consider scheduling technical screen assessments for borderline candidates ({', '.join(review)}) to verify practical skills."
    else:
        rec = "Re-evaluate sourcing channels; current batch does not align with core job description competencies."
    md.append(f"• **Recommended Action**: {rec}")
    
    return "\n\n".join(md)


def generate_batch_ai_insights(results, jd, api_key):
    """Query Gemini to generate a batch recruiter summary for the applicants."""
    import google.generativeai as genai
    from config.settings import AIConfig
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(AIConfig.MODEL_NAME)
        
        candidate_briefs = []
        for r in results:
            c = r["resume"]
            ai = r["ai_result"]
            brief = (
                f"- Name: {c.name}\n"
                f"  Overall Fit Score: {c.match_score}%\n"
                f"  Status: {c.status}\n"
                f"  Key Strengths: {', '.join(ai.get('strengths', []))}\n"
                f"  Key Risks: {', '.join(ai.get('red_flags', []))}\n"
                f"  Missing Competencies: {', '.join(r.get('comparison', {}).get('missing', []))}\n"
            )
            candidate_briefs.append(brief)
            
        briefs_text = "\n".join(candidate_briefs)
        
        prompt = f"""
You are an expert executive talent recruiter.
Generate a concise, professional, recruiter-focused "AI Hiring Insights" summary for the following screened applicant batch.

Job Title: {jd.job_title}
Screened Candidates Briefs:
{briefs_text}

Provide your response in clean markdown using standard bullet points.
Include the following exact sections:
1. **Executive Pool Summary**: 2 sentences maximum summarizing candidate count and overall talent quality.
2. **Key Matches**: Identify the strongest candidate(s) by name and why they stand out.
3. **Common Talent Trends**: Common technical strengths or credentials shared across candidates.
4. **Skills Gaps & Missing Competencies**: The most frequently missing skills or requirements.
5. **Hiring Risks**: Potential risks to keep in mind (e.g. experience gap, missing specific tools).
6. **Recommended Next Steps**: Strategic recruiter recommendations (who to interview, what assessments to send, etc.).

Keep the response concise, punchy, and highly professional. Avoid generic filler.
"""
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        # Fallback to local builder if API fails
        return build_local_hiring_insights(results, jd)


def render_executive_summary_widget(results, candidates, jd):
    """Render a compact, executive-grade recruiter scorecard widget."""
    total_count = len(candidates)
    shortlisted_count = sum(1 for c in candidates if c.status == "SHORTLISTED")
    needs_review_count = sum(1 for c in candidates if c.status == "REVIEW LATER")
    rejected_count = sum(1 for c in candidates if c.status == "REJECTED")
    avg_score = round(sum(c.match_score for c in candidates) / total_count, 1) if total_count > 0 else 0.0

    # Best Candidate
    sorted_c = sorted(candidates, key=lambda x: x.match_score, reverse=True)
    best_cand = sorted_c[0].name if sorted_c else "N/A"
    best_score = sorted_c[0].match_score if sorted_c else 0.0

    # Pool Quality
    if avg_score >= 80:
        pool_text = "Exceptional Fit"
        pool_color = "#16a34a" # Green
    elif avg_score >= 70:
        pool_text = "Strong Fit"
        pool_color = "#2563eb" # Blue
    elif avg_score >= 55:
        pool_text = "Average Fit"
        pool_color = "#d97706" # Amber
    else:
        pool_text = "Low Fit"
        pool_color = "#dc2626" # Red

    # Overall Recommendation
    if shortlisted_count > 0:
        rec_text = "Proceed to Interview"
        rec_color = "#16a34a"
    elif needs_review_count > 0:
        rec_text = "Perform Screens"
        rec_color = "#d97706"
    else:
        rec_text = "Re-source Candidates"
        rec_color = "#dc2626"

    # Common Gaps
    missing_counts = {}
    for r in results:
        for m in r.get("comparison", {}).get("missing", []):
            missing_counts[m] = missing_counts.get(m, 0) + 1
    top_missing = sorted(missing_counts.items(), key=lambda x: x[1], reverse=True)[:2]
    gaps = ", ".join(k for k, v in top_missing) if top_missing else "None detected"

    # Common Strengths
    matched_counts = {}
    for r in results:
        for m in r.get("comparison", {}).get("direct_matched", []):
            matched_counts[m] = matched_counts.get(m, 0) + 1
    top_matched = sorted(matched_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    strengths = ", ".join(k for k, v in top_matched) if top_matched else "None detected"

    # Recommended Action
    if shortlisted_count > 0:
        action = f"Schedule interviews for {best_cand} and other shortlisted applicants."
    elif needs_review_count > 0:
        action = f"Initiate telephone screens for {', '.join([c.name for c in candidates if c.status == 'REVIEW LATER'][:2])}."
    else:
        action = "Revise Job Description parameters or sourcing filters to attract closer matches."

    html_content = f"""
    <div style="font-family: 'Inter', sans-serif; padding: 2px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="font-size: 0.72rem; font-weight: 700; color: #64748b; letter-spacing: 0.05em; text-transform: uppercase;">
                ⚡ Executive Hiring Summary
            </span>
            <span style="font-size: 0.68rem; font-weight: 700; color: {rec_color}; background-color: {rec_color}1a; padding: 2px 8px; border-radius: 4px; border: 1px solid {rec_color}33;">
                {rec_text}
            </span>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
            <div style="border: 1px solid rgba(128,128,128,0.12); padding: 10px; border-radius: 6px; background-color: rgba(128,128,128,0.01);">
                <div style="font-size: 0.62rem; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;">Talent Pool Quality</div>
                <div style="font-size: 0.9rem; font-weight: 700; margin-top: 4px; color: {pool_color};">{pool_text}</div>
            </div>
            <div style="border: 1px solid rgba(128,128,128,0.12); padding: 10px; border-radius: 6px; background-color: rgba(128,128,128,0.01);">
                <div style="font-size: 0.62rem; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;">Best Candidate</div>
                <div style="font-size: 0.9rem; font-weight: 700; margin-top: 4px; color: var(--text-color);">{best_cand} <span style="font-size:0.72rem; font-weight:500; color:#64748b;">({best_score}%)</span></div>
            </div>
        </div>
        
        <div style="font-size: 0.74rem; line-height: 1.5; color: var(--text-color);">
            <div style="margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid rgba(128,128,128,0.06);">
                <strong>Common Strengths:</strong> <span style="color: #64748b; margin-left: 4px;">{strengths}</span>
            </div>
            <div style="margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid rgba(128,128,128,0.06);">
                <strong>Key Competency Gaps:</strong> <span style="color: #dc2626; margin-left: 4px;">{gaps}</span>
            </div>
            <div>
                <strong>Recruiter Action:</strong> <span style="color: #2563eb; font-weight: 600; margin-left: 4px;">{action}</span>
            </div>
        </div>
    </div>
    """
    html_clean = "\n".join([line.strip() for line in html_content.split("\n")])
    st.markdown(html_clean, unsafe_allow_html=True)


# ------------------------------------------------------------------
# Page Configurations and Styles
# ------------------------------------------------------------------
st.set_page_config(
    page_title="HireSense AI - Recruiter Screening Portal",
    page_icon="💼",
    layout="wide"
)

# Inject modern corporate Inter and Material Icon styles
inject_custom_css()

# Create required folders (temp, data, etc.)
from config.settings import create_required_directories
create_required_directories()

# Session Authentication Guard
if "authenticated_recruiter" not in st.session_state:
    st.session_state["authenticated_recruiter"] = None

if st.session_state["authenticated_recruiter"] is None:
    render_auth_page()
    st.stop()

# Initialize session states
if "current_tab" not in st.session_state:
    st.session_state["current_tab"] = "Overview"
if "results" not in st.session_state:
    st.session_state["results"] = []
if "jd" not in st.session_state:
    st.session_state["jd"] = None
if "selected_candidate_name" not in st.session_state:
    st.session_state["selected_candidate_name"] = None
if "analysis_mode" not in st.session_state:
    st.session_state["analysis_mode"] = "AI Enhanced"
if "api_cred_source" not in st.session_state:
    st.session_state["api_cred_source"] = "Default System Key"
if "show_profile_modal" not in st.session_state:
    st.session_state["show_profile_modal"] = False
if "show_password_modal" not in st.session_state:
    st.session_state["show_password_modal"] = False

# ------------------------------------------------------------------
# Recruiter Account Dialog Modals (My Profile, Settings, Password Change)
# ------------------------------------------------------------------
from datetime import datetime

@st.dialog("👤 Recruiter Profile & Settings")
def show_profile_dialog():
    rec_info = st.session_state.get("authenticated_recruiter")
    if not rec_info:
        st.error("No active recruiter session.")
        return
        
    from database.auth import get_recruiter_details, update_recruiter_profile
    details = get_recruiter_details(rec_info["id"])
    if not details:
        st.error("Could not fetch recruiter account profile.")
        return
        
    st.markdown("#### Account Information")
    st.write(f"📧 **Work Email:** `{details['email']}`")
    st.write(f"🆔 **Recruiter ID:** `{details['id']}`")
    
    try:
        created_dt = datetime.fromisoformat(details["created_date"]).strftime("%B %d, %Y %I:%M %p")
    except Exception:
        created_dt = details["created_date"]
        
    try:
        last_login_dt = datetime.fromisoformat(details["last_login"]).strftime("%B %d, %Y %I:%M %p")
    except Exception:
        last_login_dt = details["last_login"]
        
    st.write(f"📅 **Created At:** {created_dt}")
    st.write(f"🕒 **Last Login:** {last_login_dt}")
    st.divider()
    
    st.markdown("#### Edit Profile Settings")
    with st.form("edit_profile_form", clear_on_submit=False):
        new_name = st.text_input("Full Name", value=details["fullname"])
        new_company = st.text_input("Company Name", value=details["company_name"])
        save_btn = st.form_submit_button("Save Changes", use_container_width=True)
        
        if save_btn:
            if not new_name.strip() or not new_company.strip():
                st.error("Fields cannot be empty.")
            else:
                success = update_recruiter_profile(details["id"], new_name.strip(), new_company.strip())
                if success:
                    st.session_state["authenticated_recruiter"]["fullname"] = new_name.strip()
                    st.session_state["authenticated_recruiter"]["company_name"] = new_company.strip()
                    st.success("Profile updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update profile.")

@st.dialog("🔐 Change Password")
def show_change_password_dialog():
    rec_info = st.session_state.get("authenticated_recruiter")
    if not rec_info:
        st.error("No active recruiter session.")
        return
        
    from database.auth import update_password
    from frontend.auth_ui import check_password_policy, render_password_requirements_panel
    
    st.markdown("#### Update Your Password")
    st.caption("Please configure a new secure password matching the enterprise validation rules below.")
    
    current_pwd = st.text_input("Current Password", type="password", key="dialog_curr_pwd")
    new_pwd = st.text_input("New Password", type="password", key="dialog_new_pwd")
    
    render_password_requirements_panel(new_pwd)
    
    confirm_pwd = st.text_input("Confirm New Password", type="password", key="dialog_conf_pwd")
    submit_btn = st.button("Update Password", key="dialog_pwd_submit_btn", use_container_width=True)
    
    if submit_btn:
        if not current_pwd or not new_pwd or not confirm_pwd:
            st.error("Please fill in all fields.")
        elif not check_password_policy(new_pwd):
            st.error("New password does not satisfy validation criteria.")
        elif new_pwd != confirm_pwd:
            st.error("Confirm password does not match new password.")
        else:
            from database.auth import get_connection, verify_password
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM recruiters WHERE id = ?", (rec_info["id"],))
            row = cursor.fetchone()
            conn.close()
            
            if not row or not verify_password(row["password_hash"], current_pwd):
                st.error("Current password incorrect.")
            else:
                success = update_password(rec_info["email"], new_pwd)
                if success:
                    st.success("Password updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update password.")

# Trigger popover dialogs
if st.session_state.get("show_profile_modal"):
    st.session_state["show_profile_modal"] = False
    show_profile_dialog()
    
if st.session_state.get("show_password_modal"):
    st.session_state["show_password_modal"] = False
    show_change_password_dialog()



# ------------------------------------------------------------------
# Sidebar - Configuration and Uploads
# ------------------------------------------------------------------
st.sidebar.markdown(
    textwrap.dedent("""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 20px;">
        <span class="material-symbols-outlined" style="font-size: 26px; color: #2563eb;">work</span>
        <h2 style="margin: 0; font-size: 1.25rem; font-weight: 800; letter-spacing: -0.02em; color: var(--text-color);">HireSense AI</h2>
    </div>
    """),
    unsafe_allow_html=True
)

st.sidebar.markdown(
    textwrap.dedent("""
    <div style="font-size: 0.72rem; font-weight: 700; color: #64748b; margin-bottom: 12px; letter-spacing: 0.05em; text-transform: uppercase;">
        Screening Controls
    </div>
    """),
    unsafe_allow_html=True
)

# Left navigation selection linked to session state (State-aware filtering)
if st.session_state.get("results"):
    nav_options = ["Overview", "Candidates", "Job Descriptions", "Reports"]
else:
    nav_options = ["Overview"]

# Ensure current tab is valid based on active state-aware options list
if st.session_state["current_tab"] not in nav_options:
    st.session_state["current_tab"] = "Overview"

# Safeguard widget key to prevent Streamlit options validation crash when options list changes
if "nav_radio_widget" in st.session_state and st.session_state["nav_radio_widget"] not in nav_options:
    st.session_state["nav_radio_widget"] = st.session_state["current_tab"]

# Render navigation radio representing the UI (nav_radio_widget key is treated as read-only)
selected_nav = st.sidebar.radio(
    "Navigation Selector",
    options=nav_options,
    index=nav_options.index(st.session_state["current_tab"]),
    key="nav_radio_widget",
    label_visibility="collapsed"
)

# Synchronously update the authoritative current_tab state and trigger clean rerun if changed
if selected_nav != st.session_state["current_tab"]:
    st.session_state["current_tab"] = selected_nav
    st.rerun()

st.sidebar.divider()

# Screening Speed / Analysis Modes Parameters
st.sidebar.markdown(
    textwrap.dedent("""
    <div style="font-size: 0.72rem; font-weight: 700; color: #64748b; margin-bottom: 12px; letter-spacing: 0.05em; text-transform: uppercase;">
        Screening Parameters
    </div>
    """),
    unsafe_allow_html=True
)

analysis_mode = st.sidebar.radio(
    "Analysis Mode",
    options=["Fast Screening", "AI Enhanced"],
    index=1 if st.session_state["analysis_mode"] == "AI Enhanced" else 0,
    help="Fast Screening skips AI evaluations to optimize latency. AI Enhanced uses Gemini for summaries and focus areas."
)
st.session_state["analysis_mode"] = analysis_mode

# Dynamic evaluation thresholds
shortlist_t = st.sidebar.slider(
    "Shortlist Cutoff",
    min_value=0,
    max_value=100,
    value=80,
    help="Fit percentage required for Shortlisted status."
)
review_t = st.sidebar.slider(
    "Review Later Cutoff",
    min_value=0,
    max_value=100,
    value=60,
    help="Fit percentage required for Review Later status. Below this is Rejected."
)

MatchingConfig.SHORTLIST_THRESHOLD = shortlist_t
MatchingConfig.REVIEW_THRESHOLD = review_t

# Instantly synchronize all candidates' status based on updated slider thresholds and their match_score
if st.session_state.get("results"):
    for r in st.session_state["results"]:
        c = r["resume"]
        if c.match_score >= shortlist_t:
            c.status = "SHORTLISTED"
        elif c.match_score >= review_t:
            c.status = "REVIEW LATER"
        else:
            c.status = "REJECTED"
        
        # Keep hiring_recommendation and ai_result synced
        c.hiring_recommendation = c.status
        if "ai_result" in r:
            r["ai_result"]["hiring_recommendation"] = c.status

st.sidebar.divider()

# Job Description Source Selector
st.sidebar.markdown(
    textwrap.dedent("""
    <div style="font-size: 0.72rem; font-weight: 700; color: #64748b; margin-bottom: 12px; letter-spacing: 0.05em; text-transform: uppercase;">
        Document Ingestion
    </div>
    """),
    unsafe_allow_html=True
)

jd_source = st.sidebar.radio("Job Description Source", ["Upload PDF/DOCX", "Paste Text"], label_visibility="collapsed")

jd_pasted = ""
jd_file = None

if jd_source == "Upload PDF/DOCX":
    jd_file = st.sidebar.file_uploader(
        "Upload Job Description",
        type=["pdf", "docx"],
        help="Upload the official PDF or Word file."
    )
else:
    jd_pasted = st.sidebar.text_area(
        "Paste Job Description Text",
        height=140,
        placeholder="Paste job title, qualifications, and requirements here..."
    )

resume_files = st.sidebar.file_uploader(
    "Upload Candidate Resumes",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=True,
    help="Select one or multiple candidate resumes to screen."
)

# Screening execution trigger
if st.sidebar.button("Run Screening Analysis", use_container_width=True):
    jd_valid = False
    jd_path = None
    import uuid
    
    if jd_source == "Upload PDF/DOCX" and jd_file:
        jd_suffix = Path(jd_file.name).suffix
        jd_path = PathConfig.TEMP_DIR / f"{uuid.uuid4()}{jd_suffix}"
        with open(jd_path, "wb") as f:
            f.write(jd_file.read())
        jd_valid = True
    elif jd_source == "Paste Text" and jd_pasted.strip():
        jd_path = PathConfig.TEMP_DIR / f"jd_{uuid.uuid4()}.txt"
        with open(jd_path, "w", encoding="utf-8") as f:
            f.write(jd_pasted)
        jd_valid = True
        
    if not jd_valid:
        st.sidebar.error("Error: Please provide a valid Job Description.")
    elif not resume_files:
        if jd_path and jd_path.exists():
            try:
                jd_path.unlink()
            except Exception:
                pass
        st.sidebar.error("Error: Please select candidate resumes to screen.")
    else:
        with st.spinner("Analyzing applicant files against requirements..."):
            try:
                # Parse Job Description
                jd = JDParser.parse(str(jd_path))
                st.session_state["jd"] = jd

                # Process candidates
                results = []
                use_ai_flag = (st.session_state["analysis_mode"] == "AI Enhanced")
                for res_file in resume_files:
                    res_suffix = Path(res_file.name).suffix
                    res_path = PathConfig.TEMP_DIR / f"{uuid.uuid4()}{res_suffix}"
                    
                    try:
                        with open(res_path, "wb") as f:
                            f.write(res_file.read())
                        
                        result = AnalysisService.analyze(str(res_path), str(jd_path), use_ai=use_ai_flag)
                        results.append(result)
                    except Exception as ex:
                        st.error(f"Error parsing resume '{res_file.name}': {ex}")
                    finally:
                        if res_path.exists():
                            try:
                                res_path.unlink()
                            except Exception:
                                pass

                st.session_state["results"] = results
                
                # Pre-calculate and cache batch AI insights
                api_key_active = bool(os.getenv("GEMINI_API_KEY", "") or AIConfig.API_KEY)
                if use_ai_flag and api_key_active:
                    st.session_state["batch_ai_insights"] = generate_batch_ai_insights(results, jd, os.getenv("GEMINI_API_KEY", "") or AIConfig.API_KEY)
                else:
                    st.session_state["batch_ai_insights"] = build_local_hiring_insights(results, jd)

                st.sidebar.success(f"Screening complete: {len(results)} applicants analyzed.")
                st.rerun()
            finally:
                if jd_path and jd_path.exists():
                    try:
                        jd_path.unlink()
                    except Exception:
                        pass

# Clear Screening Session button for recruiters
if st.session_state.get("results"):
    st.sidebar.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    if st.sidebar.button("Clear Screening Session", key="clear_session_btn", use_container_width=True):
        st.session_state["results"] = []
        st.session_state["jd"] = None
        if "batch_ai_insights" in st.session_state:
            del st.session_state["batch_ai_insights"]
        st.session_state["current_tab"] = "Overview"
        st.rerun()

st.sidebar.divider()

st.sidebar.markdown(
    textwrap.dedent("""
    <div style="font-size: 0.72rem; font-weight: 700; color: #64748b; margin-bottom: 12px; letter-spacing: 0.05em; text-transform: uppercase;">
        Engine Settings
    </div>
    """),
    unsafe_allow_html=True
)

# Determine active parser configuration
current_system_key = os.getenv("GEMINI_API_KEY", "")
api_key_active = bool(current_system_key or AIConfig.API_KEY)

# AI Engine Status Card
with st.sidebar.container(border=True):
    st.markdown(
        "<p style='font-size: 0.72rem; font-weight: 700; color: #64748b; letter-spacing: 0.05em; text-transform: uppercase; margin: 0 0 6px 0;'>AI Engine Status</p>",
        unsafe_allow_html=True
    )
    st.markdown("**Provider:** Google Gemini")
    st.markdown(f"**Model:** {AIConfig.MODEL_NAME}")
    
    status_label = "<span style='color: var(--success-accent); font-weight: 700;'>Connected</span>" if api_key_active else "<span style='color: var(--warning-accent); font-weight: 700;'>Offline (Fallback)</span>"
    st.markdown(f"**Status:** {status_label}", unsafe_allow_html=True)
    
    st.markdown(f"**Active Mode:** {st.session_state['analysis_mode']}")

# Credentials source selection
api_cred_source = st.sidebar.radio(
    "API Credentials Source",
    options=["Default System Key", "Custom API Key Override"],
    index=0 if st.session_state["api_cred_source"] == "Default System Key" else 1,
    help="Select whether to use the pre-configured system key or enter your own custom API Key."
)
st.session_state["api_cred_source"] = api_cred_source

if api_cred_source == "Custom API Key Override":
    api_key_input = st.sidebar.text_input(
        "Custom Gemini API Key",
        type="password",
        value=AIConfig.API_KEY if AIConfig.API_KEY != current_system_key else "",
        placeholder="Enter your Gemini API key..."
    )
    if api_key_input and api_key_input != AIConfig.API_KEY:
        os.environ["GEMINI_API_KEY"] = api_key_input
        AIConfig.API_KEY = api_key_input
        st.rerun()
else:
    if AIConfig.API_KEY != current_system_key:
        os.environ["GEMINI_API_KEY"] = current_system_key
        AIConfig.API_KEY = current_system_key
        st.rerun()



# ------------------------------------------------------------------
# Main Area Layout (Top Bar with Clickable Account Dropdown Popover)
# ------------------------------------------------------------------
# Dynamic recruiter information
rec_info = st.session_state.get("authenticated_recruiter")
rec_name = rec_info["fullname"] if rec_info else "Sai Vardhan"
rec_company = rec_info["company_name"] if rec_info else "Acme Corp"

import html
escaped_rec_name = html.escape(rec_name)
escaped_rec_company = html.escape(rec_company)

rec_names_split = rec_name.split()
rec_initials = "".join([n[0].upper() for n in rec_names_split[:2]]) if rec_names_split else "SV"
escaped_rec_initials = html.escape(rec_initials)

# Select dynamic title text based on current tab
tab_titles = {
    "Overview": "Screening Overview",
    "Candidates": "Candidate Evaluation",
    "Job Descriptions": "Job Specifications",
    "Reports": "Executive Reports"
}
current_title = tab_titles.get(st.session_state.get("current_tab", "Overview"), "Screening Overview")
current_desc = {
    "Overview": "Enterprise-grade talent assessment and shortlisting.",
    "Candidates": "Detailed comparison of applicant skills against job specs.",
    "Job Descriptions": "Ingested requirement parameters and specifications.",
    "Reports": "Executive pipeline summaries and exports."
}.get(st.session_state.get("current_tab", "Overview"), "Enterprise-grade talent assessment and shortlisting.")

# Inject Custom Account Menu CSS
st.markdown(
    f"""
    <style>
        /* Style the popover container to align right */
        div[data-testid="stPopover"] {{
            display: flex;
            justify-content: flex-end;
            width: 100%;
        }}

        /* Style the popover button to look like a profile card */
        div[data-testid="stPopover"] > button {{
            background: transparent !important;
            border: 1px solid rgba(128, 128, 128, 0.15) !important;
            border-radius: 8px !important;
            padding: 6px 14px !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
            text-align: left !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
            width: auto !important;
            height: 42px !important;
            color: var(--text-color) !important;
        }}

        div[data-testid="stPopover"] > button:hover {{
            background: rgba(128, 128, 128, 0.05) !important;
            border-color: rgba(128, 128, 128, 0.25) !important;
        }}

        /* Inject circular initials avatar */
        div[data-testid="stPopover"] > button::before {{
            content: "{escaped_rec_initials}" !important;
            width: 30px !important;
            height: 30px !important;
            border-radius: 50% !important;
            background-color: rgba(37, 99, 235, 0.08) !important;
            color: #2563eb !important;
            border: 1px solid rgba(37, 99, 235, 0.15) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 0.75rem !important;
            font-weight: 700 !important;
            font-family: 'Inter', sans-serif !important;
        }}

        /* Style popover menu items dropdown */
        div[data-testid="stPopoverBody"] button {{
            background: transparent !important;
            border: 1px solid transparent !important;
            color: var(--text-color) !important;
            text-align: left !important;
            justify-content: flex-start !important;
            padding: 8px 12px !important;
            font-size: 0.82rem !important;
            font-weight: 500 !important;
            width: 100% !important;
            border-radius: 6px !important;
            transition: background 0.15s ease !important;
        }}

        div[data-testid="stPopoverBody"] button:hover {{
            background: rgba(128, 128, 128, 0.06) !important;
        }}

        /* Soft red highlight for logout */
        div[data-testid="stPopoverBody"] button[key*="logout_dropdown_btn"] {{
            color: #ef4444 !important;
        }}

        /* Style disabled buttons to look like muted menu items */
        div[data-testid="stPopoverBody"] button:disabled {{
            color: #94a3b8 !important;
            cursor: not-allowed !important;
            opacity: 0.65 !important;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# Render Top Bar columns
col_title, col_profile = st.columns([2.0, 1.0])

with col_title:
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 1.6rem; font-weight: 800; letter-spacing: -0.03em; color: var(--text-color);">{current_title}</h1>
            <p style="margin: 3px 0 0 0; font-size: 0.85rem; color: #64748b;">{current_desc}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_profile:
    # Popover acts as the clickable recruiter profile card dropdown
    with st.popover(
        label=f"{escaped_rec_name} | {escaped_rec_company}",
        use_container_width=True,
    ):
        st.markdown(
            f"""
            <div style="padding: 4px 8px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    <div class="avatar-initials" style="width: 40px; height: 40px; border: 1px solid rgba(128,128,128,0.15); display: flex; align-items: center; justify-content: center; font-size: 0.95rem; font-weight: 700; background-color: rgba(37,99,235,0.08); color: #2563eb; border-radius: 50%;">
                        {escaped_rec_initials}
                    </div>
                    <div>
                        <p style="margin: 0; font-size: 0.9rem; font-weight: 700; color: var(--text-color); line-height: 1.2;">{escaped_rec_name}</p>
                        <p style="margin: 2px 0 0 0; font-size: 0.72rem; color: #64748b; font-weight: 500;">Recruiter</p>
                    </div>
                </div>
                <p style="margin: 0; font-size: 0.72rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;">{escaped_rec_company}</p>
            </div>
            <hr style="margin: 8px 0; border: 0; border-top: 1px solid rgba(128,128,128,0.1);"/>
            """,
            unsafe_allow_html=True
        )
        
        # Dropdown Actions
        if st.button("👤 My Profile", key="profile_menu_item", use_container_width=True):
            st.session_state["show_profile_modal"] = True
            st.rerun()
            
        if st.button("⚙ Account Settings", key="settings_menu_item", use_container_width=True):
            st.session_state["show_profile_modal"] = True
            st.rerun()
            
        if st.button("🔐 Change Password", key="password_menu_item", use_container_width=True):
            st.session_state["show_password_modal"] = True
            st.rerun()
        
        st.markdown('<hr style="margin: 8px 0; border: 0; border-top: 1px solid rgba(128,128,128,0.1);"/>', unsafe_allow_html=True)
        
        if st.button("🚪 Logout", key="logout_dropdown_btn", use_container_width=True):
            st.session_state["authenticated_recruiter"] = None
            st.rerun()

# Add a divider below top bar block
st.markdown('<hr style="margin-top: -10px; margin-bottom: 20px; border: 0; border-top: 1px solid rgba(128,128,128,0.1);"/>', unsafe_allow_html=True)

# User Information Banners: Inform recruiter if Gemini fallback is active in AI mode
if st.session_state["analysis_mode"] == "AI Enhanced" and not api_key_active:
    st.warning(
        "Fallback Mode Active: A Gemini API Key was not detected. The platform is evaluating applicants using "
        "local rules and heuristics. Provide a key in 'Engine Settings' on the sidebar for full AI recommendations."
    )

if not st.session_state["results"]:
    # Welcome / Onboarding Panel using Native Streamlit components (no HTML indentation bugs, perfect dark/light sync)
    with st.container(border=True):
        st.subheader("Welcome to HireSense AI")
        st.write(
            "HireSense is an enterprise-grade Job Description (JD) aware resume screening platform. "
            "It parses CVs and Job Descriptions, maps candidate competencies, validates education and experience checkpoints, "
            "and evaluates candidate fit based on objective criteria."
        )
        
        st.write("")
        st.markdown("**GET STARTED**")
        
        col_w1, col_w2, col_w3 = st.columns(3)
        with col_w1:
            with st.container(border=True):
                st.markdown("📋 **1. Ingest Requirements**")
                st.caption("Upload a Job Description PDF/DOCX or paste core details in the sidebar panel.")
        with col_w2:
            with st.container(border=True):
                st.markdown("👥 **2. Upload Candidate Resumes**")
                st.caption("Select one or multiple resumes to screen in a batch.")
        with col_w3:
            with st.container(border=True):
                st.markdown("📈 **3. Evaluate Fit**")
                st.caption("Trigger the analysis engine to inspect candidate matching breakdowns.")
else:
    results = st.session_state["results"]
    jd = st.session_state["jd"]
    candidates = [r["resume"] for r in results]
    current_tab_name = st.session_state["current_tab"]

    # ==============================================================
    # VIEW: OVERVIEW DASHBOARD
    # ==============================================================
    if current_tab_name == "Overview":
        # KPIs calculations
        total_count = len(candidates)
        shortlisted_count = sum(1 for c in candidates if c.status == "SHORTLISTED")
        needs_review_count = sum(1 for c in candidates if c.status == "REVIEW LATER")
        rejected_count = sum(1 for c in candidates if c.status == "REJECTED")
        avg_score = round(sum(c.match_score for c in candidates) / total_count, 1) if total_count > 0 else 0.0

        # Metrics row
        kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
        with kpi_col1:
            render_metric_card("Total Candidates", f"{total_count}", "group", "Active Screening Pool")
        with kpi_col2:
            pct = round(shortlisted_count / total_count * 100) if total_count > 0 else 0
            render_metric_card("Shortlisted", f"{shortlisted_count}", "check_circle", f"{pct}% of total", "green")
        with kpi_col3:
            pct_rev = round(needs_review_count / total_count * 100) if total_count > 0 else 0
            render_metric_card("Review Later", f"{needs_review_count}", "pending_actions", f"{pct_rev}% of total", "amber")
        with kpi_col4:
            pct_rej = round(rejected_count / total_count * 100) if total_count > 0 else 0
            render_metric_card("Rejected", f"{rejected_count}", "cancel", f"{pct_rej}% of total", "red")
        with kpi_col5:
            render_metric_card("Average Fit Score", f"{avg_score}%", "trending_up", "Roster Average Fit")

        st.divider()

        # Full-width Layout: Visual Analytics Grid & Candidate Roster stretch to the right end
        # Visual Analytics Grid
        chart_col1, chart_col2 = st.columns(2)
        
        is_fast_mode = (st.session_state["analysis_mode"] == "Fast Screening")
        current_system_key = os.getenv("GEMINI_API_KEY", "")
        gemini_active = bool(current_system_key or AIConfig.API_KEY)
        show_ai_insights = (not is_fast_mode) and gemini_active
        
        with chart_col1:
            with st.container(border=True, height=315):
                fig_status = plot_status_distribution(candidates)
                if fig_status:
                    st.plotly_chart(fig_status, use_container_width=True)
        
        with chart_col2:
            with st.container(border=True, height=315):
                if show_ai_insights:
                    render_executive_summary_widget(results, candidates, jd)
                else:
                    if not is_fast_mode and not gemini_active:
                        st.caption("ℹ️ AI insights are unavailable. Showing standard screening analytics.")
                        
                    fig_quality = plot_candidate_quality_distribution(candidates)
                    if fig_quality:
                        st.plotly_chart(fig_quality, use_container_width=True)

        st.divider()

        # Applicant List
        st.markdown(
            """
            <h3 style="font-size: 1.15rem; font-weight: 700; margin: 0 0 14px 0; color: var(--text-color);">All Applicants</h3>
            """,
            unsafe_allow_html=True
        )
        
        # Recruiter-friendly Column Headers
        hdr_av, hdr_cand, hdr_fit, hdr_status, hdr_skills, hdr_exp, hdr_edu, hdr_act = st.columns(
            [0.5, 2.0, 1.0, 1.2, 2.2, 0.8, 1.0, 0.8]
        )
        with hdr_av:
            st.markdown("<span style='font-size: 0.72rem; font-weight: 700; color: #64748b;'>ROSTER</span>", unsafe_allow_html=True)
        with hdr_cand:
            st.markdown("<span style='font-size: 0.72rem; font-weight: 700; color: #64748b;'>APPLICANT</span>", unsafe_allow_html=True)
        with hdr_fit:
            st.markdown("<span style='font-size: 0.72rem; font-weight: 700; color: #64748b;'>FIT SCORE</span>", unsafe_allow_html=True)
        with hdr_status:
            st.markdown("<span style='font-size: 0.72rem; font-weight: 700; color: #64748b;'>STATUS</span>", unsafe_allow_html=True)
        with hdr_skills:
            st.markdown("<span style='font-size: 0.72rem; font-weight: 700; color: #64748b;'>TOP MATCHED SKILLS</span>", unsafe_allow_html=True)
        with hdr_exp:
            st.markdown("<span style='font-size: 0.72rem; font-weight: 700; color: #64748b;'>EXPERIENCE</span>", unsafe_allow_html=True)
        with hdr_edu:
            st.markdown("<span style='font-size: 0.72rem; font-weight: 700; color: #64748b;'>EDUCATION</span>", unsafe_allow_html=True)
        with hdr_act:
            st.markdown("<span style='font-size: 0.72rem; font-weight: 700; color: #64748b;'>ACTION</span>", unsafe_allow_html=True)
        
        st.markdown("<hr style='margin: 4px 0 10px 0; border: 0; border-top: 1px solid rgba(128,128,128,0.15);'/>", unsafe_allow_html=True)

        for idx, r in enumerate(results):
            c = r["resume"]
            
            row_av, row_cand, row_fit, row_status, row_skills, row_exp, row_edu, row_act = st.columns(
                [0.5, 2.0, 1.0, 1.2, 2.2, 0.8, 1.0, 0.8]
            )
            
            import html
            names = c.name.split()
            initials = "".join([n[0].upper() for n in names[:2]]) if names else "AP"
            escaped_initials = html.escape(initials)
            
            with row_av:
                st.markdown(f'<div class="avatar-initials">{escaped_initials}</div>', unsafe_allow_html=True)
            
            escaped_name = html.escape(c.name)
            escaped_email = html.escape(c.email or 'N/A')
            with row_cand:
                st.markdown(f"<div style='font-size: 0.82rem; font-weight: 600; color: var(--text-color);'>{escaped_name}</div><div style='font-size: 0.72rem; color: #64748b;'>{escaped_email}</div>", unsafe_allow_html=True)
            
            with row_fit:
                score = c.match_score
                bar_color = "var(--success-accent)" if score >= 80 else "var(--warning-accent)" if score >= 60 else "var(--danger-accent)"
                st.markdown(f"<span style='font-weight: 600; font-size: 0.82rem; color: {bar_color};'>{score}%</span><div class='progress-container-custom'><div class='progress-bar-custom' style='width: {score}%; background-color: {bar_color};'></div></div>", unsafe_allow_html=True)
            
            with row_status:
                st.markdown(get_status_badge_html(c.status), unsafe_allow_html=True)
            
            with row_skills:
                c_skills = [s.name for s in c.skills]
                skills_slice = ", ".join(c_skills[:3])
                escaped_skills = html.escape(skills_slice)
                extra = len(c_skills) - 3
                extra_txt = f" <span style='font-size: 0.72rem; color: #64748b;'>+{extra} more</span>" if extra > 0 else ""
                st.markdown(f"<span style='font-size: 0.78rem; font-weight: 500; color: var(--text-color);'>{escaped_skills}{extra_txt}</span>", unsafe_allow_html=True)
            
            with row_exp:
                st.markdown(f"<span style='font-size: 0.78rem; font-weight: 500; color: var(--text-color);'>{c.experience_years} Yrs</span>", unsafe_allow_html=True)
            
            with row_edu:
                edu_name = c.education.split(",")[0] if c.education else "N/A"
                escaped_edu = html.escape(edu_name[:15])
                st.markdown(f"<span style='font-size: 0.78rem; color: #64748b;'>{escaped_edu}</span>", unsafe_allow_html=True)
            
            with row_act:
                if st.button("Review", key=f"rev_btn_{idx}", use_container_width=True):
                    st.session_state["selected_candidate_name"] = c.name
                    st.session_state["current_tab"] = "Candidates"
                    st.rerun()
            
            st.markdown("<hr style='margin: 8px 0; border: 0; border-top: 1px solid rgba(128,128,128,0.06);'/>", unsafe_allow_html=True)

    # ==============================================================
    # VIEW: CANDIDATES DETAILS
    # ==============================================================
    elif current_tab_name == "Candidates":
        st.subheader("Candidate Roster Evaluation")
        
        # Select Candidate
        cand_names = [c.name for c in candidates]
        default_idx = 0
        if st.session_state["selected_candidate_name"] in cand_names:
            default_idx = cand_names.index(st.session_state["selected_candidate_name"])
            
        selected_name = st.selectbox("Select Candidate profile to screen", cand_names, index=default_idx)
        st.session_state["selected_candidate_name"] = selected_name
        
        # Pull candidate info
        target_idx = cand_names.index(selected_name)
        r = results[target_idx]
        c = r["resume"]
        comp = r["comparison"]
        rule = r["rule_result"]
        ai = r["ai_result"]

        # Render Header Info Card
        render_candidate_header(c)

        # Main details panel layout
        col_summary, col_skills_breakdown = st.columns([1.8, 1.2])

        with col_summary:
            st.markdown("#### Executive Fit Assessment")
            st.info(ai.get("summary", "No screening summary available."))

            # Fit strengths vs gaps
            str_col, gap_col = st.columns(2)
            with str_col:
                st.markdown("**Strengths:**")
                if ai.get("strengths"):
                    for strength in ai["strengths"]:
                        st.write(f"- {strength}")
                else:
                    st.write("- None specified")

                st.markdown("**Suggested Interview Focus Areas:**")
                if ai.get("matched_projects"):
                    for proj in ai["matched_projects"]:
                        st.write(f"- {proj}")
                else:
                    st.write("- None specified")

            with gap_col:
                st.markdown("**Hiring Risks & Concerns:**")
                if ai.get("red_flags"):
                    for flag in ai["red_flags"]:
                        st.write(f"- {flag}")
                else:
                    st.write("- None specified")

                st.markdown("**Development Recommendations:**")
                if ai.get("improvement_suggestions"):
                    for sugg in ai["improvement_suggestions"]:
                        st.write(f"- {sugg}")
                else:
                    st.write("- None specified")

            st.divider()

            # Recruiter Decisions Notes
            st.markdown("#### Assessment Details")
            notes_col1, notes_col2 = st.columns(2)
            with notes_col1:
                st.write(f"**Hiring Recommendation:** `{ai.get('hiring_recommendation', 'REVIEW LATER')}`")
                st.write(f"**Interpersonal Capabilities:** {', '.join(c.soft_skills) if c.soft_skills else 'None specified'}")
            with notes_col2:
                st.write(f"**Executive Review Status:** `{c.status}`")
                st.write(f"**Confidence Level:** `{ai.get('confidence', 'MEDIUM')}`")
            
            # Action: Download PDF Card
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            pdf_bytes = generate_candidate_pdf(c, jd)
            st.download_button(
                label="📥 Download Candidate Assessment PDF",
                data=pdf_bytes,
                file_name=f"Assessment_{c.name.replace(' ', '_')}.pdf",
                mime="application/pdf",
                key=f"dl_detail_pdf_{target_idx}"
            )

        with col_skills_breakdown:
            st.markdown("#### Qualifications & Skill Verification")
            
            # Experience and Edu summary cards
            st.markdown(
                f"""
                <div style="border: 1px solid rgba(128,128,128,0.12); padding: 12px; border-radius: 6px; margin-bottom: 12px; background-color: rgba(128,128,128,0.015);">
                    <div style="font-size: 0.72rem; color:#64748b; font-weight:700; text-transform:uppercase;">Experience Level</div>
                    <div style="font-size: 1rem; font-weight:700; margin-top:2px; color: var(--text-color);">{c.experience_years} Years Detected</div>
                </div>
                <div style="border: 1px solid rgba(128,128,128,0.12); padding: 12px; border-radius: 6px; margin-bottom: 15px; background-color: rgba(128,128,128,0.015);">
                    <div style="font-size: 0.72rem; color:#64748b; font-weight:700; text-transform:uppercase;">Education Degree</div>
                    <div style="font-size: 0.85rem; font-weight:700; margin-top:2px; color: var(--text-color);">{c.education or 'N/A'}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Matched/Missing Skills lists
            m_tab, mis_tab = st.tabs(["Competencies Matched", "Gaps / Missing Skills"])
            with m_tab:
                recruiter_evidence = comp.get("recruiter_evidence", {})
                if recruiter_evidence:
                    st.markdown("<p style='font-size:0.72rem; color:#64748b; font-weight:700; text-transform:uppercase; margin-bottom:8px;'>Competency Evidence Scorecard</p>", unsafe_allow_html=True)
                    for comp_name, ev_data in recruiter_evidence.items():
                        conf = ev_data["confidence"]
                        badge_color = "#22c55e" if "High" in conf else "#f59e0b" if "Medium" in conf else "#ef4444"
                        
                        # Clean details to keep them short and readable
                        details_clean = [d for d in ev_data["details"] if d.strip()]
                        details_str = " &bull; ".join(details_clean) if details_clean else "Inferred from resume text"
                        
                        st.markdown(
                            f"""
                            <div style="border: 1px solid rgba(128,128,128,0.15); padding: 8px 12px; border-radius: 6px; margin-bottom: 8px; background-color: rgba(128,128,128,0.01);">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                    <span style="font-weight: 600; font-size: 0.82rem; color: var(--text-color);">{comp_name}</span>
                                    <span style="font-size: 0.68rem; font-weight: 700; color: {badge_color}; background-color: {badge_color}1a; padding: 2px 6px; border-radius: 4px;">&#10003; {conf}</span>
                                </div>
                                <div style="font-size: 0.74rem; color: #64748b; margin-left: 2px;">
                                    {details_str}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    if comp.get("direct_matched"):
                        st.success("Direct Matches:")
                        st.write(", ".join(comp["direct_matched"]))
                    if comp.get("fuzzy_matched"):
                        st.info("Fuzzy Skill Matches:")
                        for k_fuz, v_fuz in comp["fuzzy_matched"].items():
                            st.write(f"- **{k_fuz}** (matched with **{v_fuz['matched_with']}**)")
                    if comp.get("implicit_matched"):
                        st.info("Implicit Resolved Skills:")
                        for k_imp, v_imp in comp["implicit_matched"].items():
                            st.write(f"- **{k_imp}** (satisfied by **{', '.join(v_imp)}**)")
                
                if not recruiter_evidence and not comp.get("direct_matched") and not comp.get("fuzzy_matched") and not comp.get("implicit_matched"):
                    st.write("No matches detected.")

            with mis_tab:
                if comp.get("missing"):
                    st.error("Missing required competencies:")
                    missing_exps = comp.get("missing_explanations", {})
                    for m_skill in comp["missing"]:
                        explanation = missing_exps.get(m_skill, "No matching keywords detected in candidate profile.")
                        st.markdown(
                            f"""
                            <div style="margin-bottom: 8px; margin-left: 4px;">
                                <div style="font-weight: 600; font-size: 0.82rem; color: var(--text-color);">&bull; {m_skill}</div>
                                <div style="font-size: 0.74rem; color: #ef4444; margin-left: 12px; margin-top: 1px;">{explanation}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                else:
                    st.success("No missing required skills!")

        # --------------------------------------------------------------
        # HIDE ENGINEERING METRICS INSIDE COLLAPSIBLE EXPANDER
        # --------------------------------------------------------------
        st.divider()
        with st.expander("Advanced Diagnostics", expanded=False):
            st.markdown("#### Engine Metrics & Text Signatures")
            
            adv_col1, adv_col2 = st.columns(2)
            with adv_col1:
                st.write("**Score Breakdown Parameters:**")
                st.write(f"- Experience & Education Match: {c.rule_score} / 100")
                st.write(f"- Core Skills Alignment: {c.semantic_score} %")
                st.write(f"- AI Recommendation Fit: {c.ai_score} / 100")
                st.write(f"- Overall Fit Score: {c.match_score} %")
            
            with adv_col2:
                st.write("**Profile Signatures:**")
                st.write(f"- Lexical Text Proximity: {comp.get('semantic_similarity', 0)}%")
                st.write(f"- Core Skills Met: {rule.mandatory_skills}")
                st.write(f"- Online Code References: {rule.github_present}")
                st.write(f"- Profile Completeness: {getattr(c, 'resume_completeness', 0)}%")
                st.write(f"- Parser Confidence Rating: {getattr(c, 'confidence_score', 0)}%")
                
            st.write("**Validation Checklists:**")
            for r_reason in rule.reasons:
                st.write(f"- {r_reason}")

    # ==============================================================
    # VIEW: JOB DESCRIPTION PROFILE
    # ==============================================================
    elif current_tab_name == "Job Descriptions":
        st.subheader("Job Specification Details")
        st.divider()

        jd_col1, jd_col2 = st.columns([1, 2])
        
        with jd_col1:
            st.markdown(f"### Job: **{jd.job_title}**")
            st.write(f"**Experience Threshold:** {jd.experience_required} (Target: {jd.experience_years_required} years)")
            st.write(f"**Required Education Level:** {jd.education_requirement or 'Not Specified'}")
            
            if jd.certifications_required:
                st.markdown("**Preferred Certifications:**")
                for cert_r in jd.certifications_required:
                    st.write(f"- {cert_r}")

            st.markdown("#### Target Skills Profile")
            if jd.required_skills:
                st.markdown("**Required Skills:**")
                st.write(", ".join([s.name for s in jd.required_skills]))
            if jd.preferred_skills:
                st.markdown("**Preferred Skills:**")
                st.write(", ".join([s.name for s in jd.preferred_skills]))
            if jd.soft_skills_required:
                st.markdown("**Required Soft Skills:**")
                st.write(", ".join(jd.soft_skills_required))

        with jd_col2:
            st.markdown("### Core Job Responsibilities")
            if jd.responsibilities:
                for responsibility in jd.responsibilities:
                    st.write(f"- {responsibility}")
            else:
                st.markdown("**Raw Specification Text:**")
                st.text_area("Job Description Content", value=jd.raw_text, height=350, disabled=True)

    # ==============================================================
    # VIEW: DATA EXPORTS
    # ==============================================================
    elif current_tab_name == "Reports":
        st.subheader("Ingested Applicant Exports")
        st.caption("Download structured batch screening results or a summary report of this applicant cycle.")
        st.divider()

        exp_col1, exp_col2 = st.columns(2)
        
        with exp_col1:
            st.markdown("#### CSV Spreadsheet Export")
            st.write("Contains contact details, education tiers, experience years, rule checklists, and composite alignment scores of all processed profiles.")
            csv_data = generate_csv(candidates)
            st.download_button(
                label="📥 Download Roster Results CSV",
                data=csv_data,
                file_name=f"hiresense_screening_{jd.job_title.lower().replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with exp_col2:
            st.markdown("#### Markdown Summary Executive Report")
            st.write("Contains high-level pipeline counts, average fit score ratings, and a roster of shortlisted candidates.")
            md_data = generate_summary_report(candidates, jd)
            st.download_button(
                label="📥 Download Executive Summary Markdown",
                data=md_data,
                file_name=f"hiresense_report_{jd.job_title.lower().replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True
            )
