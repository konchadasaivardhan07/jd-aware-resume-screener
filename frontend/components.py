import streamlit as st


def inject_custom_css():
    """Inject corporate HCM CSS styling (Inter typography, Material Icons, light/dark mode variables)."""
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
        
        /* Set base font */
        html, body, [class*="css"], .stMarkdown, p, div, label {
            font-family: 'Inter', -apple-system, sans-serif !important;
        }

        /* Restrained color variables for light and dark modes */
        :root {
            --primary-accent: #2563eb;
            --success-accent: #16a34a;
            --warning-accent: #d97706;
            --danger-accent: #dc2626;
        }

        /* Metric Cards */
        .glass-metric {
            background: rgba(128, 128, 128, 0.03) !important;
            border: 1px solid rgba(128, 128, 128, 0.1) !important;
            border-left: 3px solid var(--primary-accent) !important;
            border-radius: 6px;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        .glass-metric.metric-green {
            border-left: 3px solid var(--success-accent) !important;
        }
        .glass-metric.metric-amber {
            border-left: 3px solid var(--warning-accent) !important;
        }
        .glass-metric.metric-red {
            border-left: 3px solid var(--danger-accent) !important;
        }
        
        .glass-metric-value {
            font-size: 1.35rem;
            font-weight: 700;
            margin: 2px 0 0 0;
            line-height: 1.25;
            color: var(--text-color);
        }
        .glass-metric-label {
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin: 0;
            font-weight: 700;
        }
        
        /* Status Badges */
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: capitalize;
            border: 1px solid transparent;
            text-align: center;
        }
        .badge-shortlisted {
            background-color: rgba(22, 163, 74, 0.08);
            color: var(--success-accent);
            border-color: rgba(22, 163, 74, 0.18);
        }
        .badge-review {
            background-color: rgba(217, 119, 6, 0.08);
            color: var(--warning-accent);
            border-color: rgba(217, 119, 6, 0.18);
        }
        .badge-rejected {
            background-color: rgba(220, 38, 38, 0.08);
            color: var(--danger-accent);
            border-color: rgba(220, 38, 38, 0.18);
        }

        /* Avatar Icon block */
        .avatar-initials {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background-color: rgba(37, 99, 235, 0.08);
            color: var(--primary-accent);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: 600;
        }

        /* Compact custom progress container */
        .progress-container-custom {
            width: 100%;
            background: rgba(128, 128, 128, 0.12);
            border-radius: 4px;
            height: 4px;
            overflow: hidden;
            margin-top: 4px;
        }
        .progress-bar-custom {
            height: 100%;
            border-radius: 4px;
        }

        /* Collapsible Section Clean styling */
        .stExpander {
            background-color: rgba(128, 128, 128, 0.01) !important;
            border: 1px solid rgba(128, 128, 128, 0.08) !important;
            border-radius: 6px !important;
            margin-bottom: 10px !important;
        }
        
        /* Redesign main cards */
        .enterprise-card {
            background: rgba(128, 128, 128, 0.02) !important;
            border: 1px solid rgba(128, 128, 128, 0.1) !important;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 14px;
        }
    </style>
    """
    st.html(css)


def render_metric_card(label: str, value: str, icon_name: str, subtext: str = "", trend_col: str = ""):
    """Render a Workday-style clean executive metric card."""
    trend_html = ""
    if subtext:
        color = "var(--success-accent)" if trend_col == "green" else "var(--danger-accent)" if trend_col == "red" else "#64748b"
        trend_html = f'<p style="margin: 3px 0 0 0; font-size: 0.68rem; color: {color}; font-weight: 500;">{subtext}</p>'

    class_modifier = "metric-green" if trend_col == "green" else "metric-amber" if trend_col == "amber" else "metric-red" if trend_col == "red" else ""

    html = f"""
    <div class="glass-metric {class_modifier}">
        <div>
            <p class="glass-metric-label">{label}</p>
            <p class="glass-metric-value">{value}</p>
            {trend_html}
        </div>
        <div style="display: flex; align-items: center;">
            <span class="material-symbols-outlined" style="font-size: 20px; color: #64748b; opacity: 0.75;">{icon_name}</span>
        </div>
    </div>
    """
    st.html(html)


def get_status_badge_html(status: str) -> str:
    """Return the styled HTML for an enterprise status badge."""
    status_lower = status.lower()
    if "shortlist" in status_lower:
        class_name = "badge-shortlisted"
        label = "Shortlisted"
    elif "review" in status_lower:
        class_name = "badge-review"
        label = "Review Later"
    else:
        class_name = "badge-rejected"
        label = "Rejected"
    return f'<span class="badge {class_name}">{label}</span>'


def get_progress_bar_html(percentage: float) -> str:
    """Return the styled HTML for a compact progress bar based on percentage."""
    if percentage >= 80:
        bar_color = "var(--success-accent)"
    elif percentage >= 60:
        bar_color = "var(--warning-accent)"
    else:
        bar_color = "var(--danger-accent)"

    return f"""
    <div class="progress-container-custom">
        <div class="progress-bar-custom" style="width: {percentage}%; background-color: {bar_color};"></div>
    </div>
    """


import html


def render_candidate_header(candidate):
    """Render candidate brief details."""
    badge = get_status_badge_html(candidate.status)
    progress_bar = get_progress_bar_html(candidate.match_score)
    experience = f"{candidate.experience_years} Yrs Experience" if candidate.experience_years > 0 else "Experience N/A"
    edu_text = candidate.education.split(",")[0] if candidate.education else "Education Credentials N/A"

    escaped_name = html.escape(candidate.name)
    escaped_email = html.escape(candidate.email or 'N/A')
    escaped_phone = html.escape(candidate.phone or 'N/A')
    escaped_edu = html.escape(edu_text[:50])

    html_content = f"""
    <div class="enterprise-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <h4 style="margin: 0 0 2px 0; font-size: 1.05rem; font-weight: 700; color: var(--text-color);">{escaped_name}</h4>
                <span style="color: #64748b; font-size: 0.76rem; font-weight: 500;">{escaped_email}  |  {escaped_phone}</span>
            </div>
            <div>
                {badge}
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px; font-size: 0.76rem; font-weight: 600;">
            <span style="color: var(--text-color);">Overall Fit: {candidate.match_score}%</span>
            <span style="color: #64748b; font-weight: 500;">{experience}  |  {escaped_edu}</span>
        </div>
        {progress_bar}
    </div>
    """
    st.html(html_content)
