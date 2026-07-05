# ⚡ HireSense AI - Explainable Talent Screener Dashboard

HireSense AI is a professional, job description-aware candidate screening and qualification validation portal built with Python and Streamlit. It automates candidate indexing by matching resume qualifications against specific Job Descriptions using a combination of keyword rules, fuzzy matching, implicit technology mapping, cosine text similarity, and Gemini AI.

---

## 🚀 Key Features

* **Multi-Stage Document Parsing**:
  - *Baseline Regex Extractors*: Extracts emails, phone numbers, GitHub/LinkedIn profile URLs, and education landmarks instantly.
  - *Gemini AI Parser*: If the Gemini API key is configured, the system uses structure-based JSON prompts to extract detailed candidate metadata and JD parameters with high precision.
* **Advanced Semantic Matching**:
  - *Synonym Resolution*: Normalizes technology representations (e.g. "ML" to "Machine Learning") using a mapped synonyms base.
  - *Fuzzy Match (RapidFuzz)*: Resolves typos and spelling variants of key tech stacks.
  - *Dependency Resolution (Implicit Match)*: Dynamically infers parent skills from child expertise (e.g. knowing "Django" implies experience with "Python").
  - *Cosine Text Similarity*: Computes a word-level TF-IDF overlap to measure candidate profile lexical alignment to the JD.
* **Explainable Rule Engine Checklists**:
  - Renders a multi-factor score out of 100 representing: Core Skills Match (50pts), Education Fit (15pts), Experience Years (20pts), and Online Presence (15pts).
  - Provides a detailed pass/warn/fail log for every decision, giving recruiters full context.
* **Premium HR Streamlit Dashboard UI**:
  - Dark-theme visual elements with glassmorphic cards and color-graded progress indicators.
  - Interactive Plotly visualizations showing: Pipeline Status Breakdowns, Match Score Distribution, and Top Extracted Skills.
  - Advanced search filters (by keyword/skill), min score range selectors, and score/name sorting.
  - Detailed audit expansions showing raw background parameters and side-by-side skill comparisons.
* **Export Center**:
  - Download evaluated candidate pool spreadsheets in CSV format.
  - Export batch screening summaries in Markdown formats.

---

## 🛠️ Project Directory Structure

```
JD-Aware-Resume-Screener/
├── ai/
│   ├── prompts.py            # Strict JSON recruiting prompting schemas
│   └── ai_analyzer.py        # Gemini client interface and rule-based fallback
├── config/
│   └── settings.py           # Globals, paths, and matching weights configurations
├── dashboard/
│   ├── charts.py             # Plotly donut, histogram, and horizontal bar charts
│   └── reports.py            # CSV formatter and Markdown summaries generators
├── data/
│   ├── jd_samples/           # Reference job description templates
│   ├── resume_samples/       # Candidate CV templates
│   ├── knowledge_base.json   # Technical technology skills relations catalog
│   └── synonyms.json         # Acronym mappings dictionary
├── extractor/
│   └── skill_extractor.py    # Text normalizer and skills parser
├── frontend/
│   ├── components.py         # Glassmorphic HTML metrics and progress card components
│   └── ui.py                 # Core dashboard interface
├── matcher/
│   └── semantic_matcher.py   # Fuzzy, implicit, and TF-IDF Cosine Matchers
├── models/
│   ├── candidate.py          # Candidate profile variables model
│   ├── job_description.py    # Job description requirements model
│   └── skill.py              # Skill classification data class
├── parser/
│   ├── jd_parser.py          # Job description parsing pipeline (Regex + Gemini)
│   └── resume_parser.py      # Resume parsing pipeline (Regex + Gemini)
├── rules/
│   └── rule_engine.py        # Multi-factor explainable verification engine
├── tests/
│   └── test_screener.py      # Assertive pipeline verification tests
├── app.py                    # Console CLI entry point / Dry Run script
├── requirements.txt          # Third-party python libraries
└── .env                      # Environment configurations (Gemini keys)
```

---

## ⚙️ Quick Start Guide

### 1. Prerequisite Installations

Ensure you have Python 3.10+ installed.

### 2. Environment Setup

Clone this project folder and initialize a virtual environment:
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Unix/macOS
python3 -m venv .venv
source .venv/bin/activate
```

Install the third-party dependencies:
```bash
pip install -r requirements.txt
```

### 3. API Credentials Configuration

Create a `.env` file in the root folder:
```env
GEMINI_API_KEY=YOUR_GOOGLE_GEMINI_API_KEY
```
*(Alternatively, you can input your Gemini API Key directly within the Streamlit sidebar during runtime!)*

### 4. Running the Interactive Dashboard

Launch the Streamlit portal:
```bash
streamlit run frontend/ui.py
```
This opens the HR screener in your default web browser (typically on `http://localhost:8501`).

### 5. Running the Automated Tests

Verify code changes:
```bash
python tests/test_screener.py
```

### 6. Running the CLI Dry Run

Execute the console dry run on sample data:
```bash
python app.py
```

---

## 🤝 Key Integration Guidelines

* **Streamlit Cloud Deployment**: Fully compatible! Simply specify `GEMINI_API_KEY` under the app secrets panel in the Streamlit Admin console.
* **Render Deployment**: Push to GitHub, link to Render, select Docker or Python web service environment, set startup command to `streamlit run frontend/ui.py --server.port $PORT`, and add your API keys under Env variables.
