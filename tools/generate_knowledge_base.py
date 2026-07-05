"""
Knowledge Base Generator

Author: Konchada Sai Vardhan
Project: HireSense AI

Purpose
-------
Generates the application's knowledge_base.json from
structured Python dictionaries.

Run:
    python tools/generate_knowledge_base.py
"""

from __future__ import annotations

import json
from pathlib import Path

# ------------------------------------------------------------------
# Knowledge Categories
# ------------------------------------------------------------------

KNOWLEDGE_BASE = {

    "Programming Languages": {

        "Python": {
            "aliases": [
                "python",
                "python3",
                "python programming"
            ],
            "type": "Programming Language",
            "related": [
                "Flask",
                "Django",
                "FastAPI",
                "TensorFlow",
                "NumPy",
                "Pandas"
            ]
        },

        "Java": {
            "aliases": [
                "java",
                "core java",
                "advanced java"
            ],
            "type": "Programming Language",
            "related": [
                "Spring Boot",
                "Hibernate",
                "Maven"
            ]
        },

        "C": {
            "aliases": [
                "c",
                "c language"
            ],
            "type": "Programming Language",
            "related": [
                "Pointers",
                "Memory Management"
            ]
        },

        "C++": {
            "aliases": [
                "c++",
                "cpp"
            ],
            "type": "Programming Language",
            "related": [
                "STL",
                "OOP"
            ]
        },

        "JavaScript": {
            "aliases": [
                "javascript",
                "js"
            ],
            "type": "Programming Language",
            "related": [
                "React",
                "Node.js",
                "Express.js"
            ]
        },

        "TypeScript": {
            "aliases": [
                "typescript",
                "ts"
            ],
            "type": "Programming Language",
            "related": [
                "Angular",
                "React"
            ]
        },

        "SQL": {
            "aliases": [
                "sql",
                "structured query language"
            ],
            "type": "Programming Language",
            "related": [
                "MySQL",
                "PostgreSQL",
                "Oracle"
            ]
        }

    },

    # ----------------------------------------------------------

    "Frontend": {

        "HTML": {
            "aliases": ["html", "html5"],
            "type": "Frontend",
            "related": ["CSS"]
        },

        "CSS": {
            "aliases": ["css", "css3"],
            "type": "Frontend",
            "related": ["HTML"]
        },

        "Bootstrap": {
            "aliases": ["bootstrap"],
            "type": "Frontend",
            "related": ["CSS"]
        },

        "React": {
            "aliases": [
                "react",
                "reactjs",
                "react.js"
            ],
            "type": "Frontend",
            "related": [
                "JavaScript",
                "Redux"
            ]
        },

        "Angular": {
            "aliases": ["angular"],
            "type": "Frontend",
            "related": [
                "TypeScript"
            ]
        }

    },

    # ----------------------------------------------------------

    "Backend": {

        "Flask": {
            "aliases": ["flask"],
            "type": "Backend",
            "related": ["Python"]
        },

        "FastAPI": {
            "aliases": ["fastapi"],
            "type": "Backend",
            "related": ["Python"]
        },

        "Django": {
            "aliases": ["django"],
            "type": "Backend",
            "related": ["Python"]
        },

        "Spring Boot": {
            "aliases": [
                "spring boot",
                "springboot"
            ],
            "type": "Backend",
            "related": ["Java"]
        },

        "Node.js": {
            "aliases": [
                "node",
                "nodejs",
                "node.js"
            ],
            "type": "Backend",
            "related": ["JavaScript"]
        }

    },

    # ----------------------------------------------------------

    "Machine Learning": {

        "Machine Learning": {
            "aliases": [
                "machine learning",
                "ml"
            ],
            "type": "AI",
            "related": [
                "TensorFlow",
                "PyTorch",
                "Scikit-learn"
            ]
        },

        "Deep Learning": {
            "aliases": [
                "deep learning",
                "dl"
            ],
            "type": "AI",
            "related": [
                "TensorFlow",
                "PyTorch"
            ]
        },

        "TensorFlow": {
            "aliases": [
                "tensorflow",
                "tf"
            ],
            "type": "Framework",
            "related": [
                "Python"
            ]
        },

        "PyTorch": {
            "aliases": [
                "pytorch"
            ],
            "type": "Framework",
            "related": [
                "Python"
            ]
        },

        "OpenCV": {
            "aliases": [
                "opencv",
                "computer vision"
            ],
            "type": "Library",
            "related": [
                "Python"
            ]
        }

    }

}

# ------------------------------------------------------------------
# Output Path
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "knowledge_base.json"
)

OUTPUT_FILE.parent.mkdir(
    exist_ok=True
)

# ------------------------------------------------------------------
# Generate JSON
# ------------------------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        KNOWLEDGE_BASE,
        file,
        indent=4,
        ensure_ascii=False
    )

print("=" * 50)
print("Knowledge Base Generated Successfully")
print(OUTPUT_FILE)
print("=" * 50)