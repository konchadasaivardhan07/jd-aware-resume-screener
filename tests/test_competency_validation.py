import sys
from pathlib import Path

# Add project root to python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from extractor.skill_extractor import KnowledgeExtractor
from matcher.semantic_matcher import KnowledgeMatcher
from models.job_description import JobDescription
from models.candidate import Candidate
from models.skill import Skill

def run_validation():
    print("=" * 80)
    print("              HIRESENSE AI - COMPETENCY VALIDATION RUN")
    print("=" * 80)

    # 1. Define Candidate Profile using Sivamani's OCR resume text
    resume_text = """
    Kuppili Sivamani
    +91 8919916823 | sivamanikuppili35@gmail.com | Palasa, Andhra Pradesh, India | linkedin.com/in/kuppili-sivamani |
    github.com/sivamanikuppili
    Professional Summary
    Final-year B.Tech CS Engineer (GITAM, 2026 | CGPA: 8.07) skilled in Java, Spring Boot, Node.js, React.js, Python, and ML. Built 3
    full-stack and AI/ML projects, published 3 peer-reviewed papers (IF up to 8.10), and completed 2 internships. Proficient in Docker,
    Kubernetes, CI/CD, MongoDB, and REST APIs. Seeking a Software Engineer / Full-Stack / ML role.
    Technical Skills
    Languages: Java, Python, C, JavaScript (ES6+), SQL, HTML5, CSS3
    Backend: Spring Boot, Spring Data JPA, Node.js, Express.js, EJS, REST APIs, Middleware, JWT, Error Handling
    Frontend: React.js, Redux, Redux Toolkit, Tailwind CSS, Bootstrap, Responsive Design
    Databases: MySQL, MongoDB, MongoDB with Express, Node.js with SQL, Database Relationships, NoSQL
    AI / ML: Machine Learning Algorithms, ANN, Deep Learning, YOLOv8, OpenCV, ONNX, CNN, ResNet, Pandas, NumPy,
    Matplotlib
    DSA & Design: OOPs, DSA, Dynamic Programming, Segment Trees, System Design, SDLC
    DevOps & Tools: Docker, Kubernetes, CI/CD (GitHub Actions), Git, GitHub, Linux (Terminal), VS Code, IntelliJ IDEA,
    Anaconda, Google Colab, Postman
    Education
    Gandhi Institute of Technology and Management (GITAM) Visakhapatnam, Andhra Pradesh
    Bachelor of Technology in Computer Science Engineering — CGPA: 8.07 / 10.0 Aug 2022 – May 2026 (Expected)
    Sri Chaitanya Junior College Andhra Pradesh
    Intermediate (MPC) — Physics, Mathematics, Chemistry 2020 – 2022
    Work Experience
    AI/ML Intern Remote
    Bharat Versity June 2025
    • Optimized ML predictive pipelines using Python (Pandas, NumPy), improving processing accuracy by 15%.
    • Built a custom data preprocessing pipeline that reduced manual maintenance efforts by 40%.
    • Integrated Python-based ML modules (regression, classification) into the core application with senior engineers.
    Java Full Stack Developer Intern Virtual
    EduSkills Academy (AICTE – National Internship Portal) April 2025 – June 2025
    • Completed 10-week AICTE-certified program covering Spring Boot, React.js, MySQL, REST APIs, and DevOps.
    • Built full-stack apps with JWT auth, middleware, Docker containerization, and GitHub Actions CI/CD pipelines.
    Projects
    Multi-Class Real-Time Object Detection | YOLOv8, OpenCV, ONNX | GitHub
    • Built an end-to-end real-time detection pipeline with YOLOv8 supporting multi-class inference and persistent object identity.
    • Optimized for edge hardware via ONNX export and quantization; engineered re-identification across occlusion scenarios.
    High-Volume Trading Engine | Java, Spring Boot, React.js, MySQL | GitHub
    • Designed scalable trading backend with Spring Boot & Spring Data JPA; applied Segment Trees for O(log n) order matching.
    • Built React.js + Redux frontend with real-time API integration; implemented OOPs design patterns for maintainability.
    E-Commerce Order Management | Node.js, Express.js, MongoDB, React.js | GitHub
    • Developed full-stack platform with Express.js REST APIs, JWT auth, middleware, and centralized error handling.
    • Designed MongoDB schemas with complex database relationships; deployed via Docker and GitHub Actions CI/CD.
    """

    # 2. Define JD Profile based on the Full-Stack Developer JD requirements
    jd_text = """
    At [Company X], we rely on a dynamic team of engineers to solve the many challenges and puzzles of our rapidly evolving technical stack. We’re seeking a full stack developer who is ready to work with new technologies and architectures in a forward-thinking organization that’s always pushing boundaries. This person will have complete, end-to-end ownership of projects. The ideal candidate has experience building products across the stack and a firm understanding of web frameworks, APIs, databases, and multiple back-end languages.
    
    Required skills and qualifications
    At least one year of experience in building large-scale software applications
    Experience in building web applications
    Experience in designing and integrating RESTful APIs
    Knowledge of Ruby, Java/JRuby, React, and JavaScript
    """

    # Extract profiles using KnowledgeExtractor
    extractor = KnowledgeExtractor()
    resume_profile = extractor.extract(resume_text)
    jd_profile = extractor.extract(jd_text)

    # Construct mock candidate object
    candidate = Candidate(
        name="Kuppili Sivamani",
        email="sivamanikuppili35@gmail.com",
        phone="+91 8919916823",
        education="Gandhi Institute of Technology and Management (GITAM)",
        experience_years=0.0,
        skills=[item["skill"] for cat in resume_profile.values() for item in cat],
        github="github.com/sivamanikuppili",
        linkedin="linkedin.com/in/kuppili-sivamani"
    )

    # Construct mock JD object
    required_skills = [
        Skill(name="Backend languages", category="Programming Languages"),
        Skill(name="Databases", category="Databases"),
        Skill(name="RESTful APIs", category="Software Engineering"),
        Skill(name="Web applications", category="Software Engineering"),
        Skill(name="Ruby", category="Programming Languages"),
        Skill(name="React", category="Web Frameworks & Libraries"),
        Skill(name="JavaScript", category="Programming Languages")
    ]
    
    class MockJD:
        def __init__(self):
            self.job_title = "Full Stack Developer"
            self.required_skills = required_skills
            self.preferred_skills = []
            self.education_requirement = "Bachelor"
            self.experience_years_required = 1.0

    jd_mock = MockJD()

    # Run Match comparison
    comparison = KnowledgeMatcher.compare(
        resume_profile,
        jd_profile,
        resume_text=resume_text,
        jd_text=jd_text,
        jd=jd_mock
    )

    print(f"Overall Fit Score    : {comparison['match_percentage']}%")
    print(f"Required Skills Score: {comparison['required_score']}/100")
    print(f"Cosine Similarity    : {comparison['semantic_similarity']}%")
    print("-" * 80)
    print("Competency Scorecard Details:")
    for comp, data in comparison.get("recruiter_evidence", {}).items():
        print(f"\n[OK] {comp} - Confidence: {data['confidence']}")
        for detail in data["details"]:
            print(f"  • {detail}")

    print("\n" + "-" * 80)
    print("Gaps / Missing Competencies:")
    for skill in comparison["missing"]:
        explanation = comparison["missing_explanations"].get(skill, "No match found")
        print(f"[MISSING] {skill} - {explanation}")
    print("=" * 80)

if __name__ == "__main__":
    run_validation()
