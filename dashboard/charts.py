import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List


def plot_status_distribution(candidates: List):
    """Generate a donut chart showing the candidate pipeline status breakdown."""
    if not candidates:
        return None

    statuses = [c.status for c in candidates]
    df = pd.DataFrame({"Status": statuses})
    counts = df["Status"].value_counts().reset_index()
    counts.columns = ["Status", "Count"]

    color_map = {
        "SHORTLISTED": "#16a34a",   # Green
        "REVIEW LATER": "#d97706",  # Amber
        "REJECTED": "#dc2626",      # Red
        "Not Evaluated": "#64748b"  # Gray
    }

    fig = px.pie(
        counts,
        values="Count",
        names="Status",
        hole=0.45,
        color="Status",
        color_discrete_map=color_map,
        title="Hiring Decisions Summary"
    )

    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#64748b", family="Inter, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=40, b=40, l=10, r=10),
        height=300
    )
    return fig


def plot_score_distribution(candidates: List):
    """Generate a histogram showing the candidate match score distribution."""
    if not candidates:
        return None

    scores = [c.match_score for c in candidates]
    names = [c.name for c in candidates]
    df = pd.DataFrame({"Name": names, "Fit Score": scores})

    fig = px.histogram(
        df,
        x="Fit Score",
        nbins=10,
        range_x=[0, 100],
        title="Applicant Fit Distribution",
        color_discrete_sequence=["#2563eb"]
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#64748b", family="Inter, sans-serif"),
        xaxis=dict(gridcolor="rgba(128,128,128,0.1)", title="Overall Fit (%)"),
        yaxis=dict(gridcolor="rgba(128,128,128,0.1)", title="Number of Applicants"),
        margin=dict(t=40, b=40, l=10, r=10),
        height=300
    )
    return fig


def plot_skill_frequency(candidates: List, jd):
    """Generate a horizontal bar chart showing required skills matched across candidates."""
    if not candidates or not jd:
        return None

    required_skill_names = [s.name for s in jd.required_skills]
    if not required_skill_names:
        return None

    skill_counts = {name: 0 for name in required_skill_names}
    
    for c in candidates:
        c_skills = [s.name for s in c.skills]
        for skill_name in required_skill_names:
            if skill_name in c_skills:
                skill_counts[skill_name] += 1

    df = pd.DataFrame({
        "Skill": list(skill_counts.keys()),
        "Candidates Match Count": list(skill_counts.values())
    }).sort_values(by="Candidates Match Count", ascending=True)

    fig = px.bar(
        df,
        y="Skill",
        x="Candidates Match Count",
        orientation="h",
        title="Core Competency Matches",
        color="Candidates Match Count",
        color_continuous_scale="Viridis",
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#64748b", family="Inter, sans-serif"),
        xaxis=dict(gridcolor="rgba(128,128,128,0.1)", title="Candidates with Skill", tickformat="d"),
        yaxis=dict(gridcolor="rgba(128,128,128,0.1)", title=""),
        margin=dict(t=40, b=40, l=10, r=10),
        coloraxis_showscale=False,
        height=340
    )
    return fig


def plot_experience_distribution(candidates: List):
    """Generate a bar chart bucketing experience levels across candidates."""
    if not candidates:
        return None

    buckets = {"Entry (0-2 Yrs)": 0, "Mid (3-5 Yrs)": 0, "Senior (6-10 Yrs)": 0, "Lead (10+ Yrs)": 0}
    for c in candidates:
        exp = c.experience_years
        if exp < 3.0:
            buckets["Entry (0-2 Yrs)"] += 1
        elif exp < 6.0:
            buckets["Mid (3-5 Yrs)"] += 1
        elif exp < 11.0:
            buckets["Senior (6-10 Yrs)"] += 1
        else:
            buckets["Lead (10+ Yrs)"] += 1

    df = pd.DataFrame({
        "Experience Bracket": list(buckets.keys()),
        "Candidate Count": list(buckets.values())
    })

    fig = px.bar(
        df,
        x="Experience Bracket",
        y="Candidate Count",
        title="Experience Bracket Breakdown",
        color="Experience Bracket",
        color_discrete_sequence=px.colors.qualitative.Safe
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#64748b", family="Inter, sans-serif"),
        xaxis=dict(title=""),
        yaxis=dict(gridcolor="rgba(128,128,128,0.1)", title="Candidates Count", tickformat="d"),
        margin=dict(t=40, b=40, l=10, r=10),
        showlegend=False,
        height=300
    )
    return fig


def plot_education_distribution(candidates: List):
    """Generate a donut chart showing parsed education levels."""
    if not candidates:
        return None

    edu_counts = {"Bachelor's": 0, "Master's": 0, "PhD": 0, "Other/Not Listed": 0}
    
    for c in candidates:
        edu_text = c.education.lower()
        if not edu_text:
            edu_counts["Other/Not Listed"] += 1
        elif "phd" in edu_text or "ph.d" in edu_text or "doctor" in edu_text:
            edu_counts["PhD"] += 1
        elif "master" in edu_text or "ms" in edu_text or "m.s." in edu_text or "mtech" in edu_text or "mba" in edu_text:
            edu_counts["Master's"] += 1
        elif "bachelor" in edu_text or "bs" in edu_text or "b.s." in edu_text or "btech" in edu_text:
            edu_counts["Bachelor's"] += 1
        else:
            edu_counts["Other/Not Listed"] += 1

    df = pd.DataFrame({
        "Education Tier": list(edu_counts.keys()),
        "Count": list(edu_counts.values())
    })
    
    df = df[df["Count"] > 0]

    fig = px.pie(
        df,
        values="Count",
        names="Education Tier",
        hole=0.45,
        title="Parsed Education Levels",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#64748b", family="Inter, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=40, b=40, l=10, r=10),
        height=300
    )
    return fig


def plot_candidate_quality_distribution(candidates: List):
    """Generate a recruiter-friendly horizontal bar chart showing candidate quality bands."""
    if not candidates:
        return None

    bands = {
        "Excellent Fit (85-100%)": 0,
        "Strong Fit (70-84%)": 0,
        "Average Fit (55-69%)": 0,
        "Low Fit (<55%)": 0
    }

    for c in candidates:
        score = c.match_score
        if score >= 85:
            bands["Excellent Fit (85-100%)"] += 1
        elif score >= 70:
            bands["Strong Fit (70-84%)"] += 1
        elif score >= 55:
            bands["Average Fit (55-69%)"] += 1
        else:
            bands["Low Fit (<55%)"] += 1

    df = pd.DataFrame({
        "Quality Band": list(bands.keys()),
        "Candidates Count": list(bands.values())
    })

    df["order"] = [0, 1, 2, 3]
    df = df.sort_values("order", ascending=False)

    color_map = {
        "Excellent Fit (85-100%)": "#16a34a",
        "Strong Fit (70-84%)": "#3b82f6",
        "Average Fit (55-69%)": "#f59e0b",
        "Low Fit (<55%)": "#dc2626"
    }

    fig = px.bar(
        df,
        y="Quality Band",
        x="Candidates Count",
        orientation="h",
        color="Quality Band",
        color_discrete_map=color_map,
        title="Candidate Quality Distribution"
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#64748b", family="Inter, sans-serif"),
        xaxis=dict(gridcolor="rgba(128,128,128,0.1)", title="Number of Candidates", tickformat="d"),
        yaxis=dict(gridcolor="rgba(128,128,128,0.1)", title=""),
        margin=dict(t=40, b=40, l=10, r=10),
        showlegend=False,
        height=300
    )
    return fig
