from pdfminer.high_level import extract_text
from docx import Document


SKILLS_DB = [
    "python",
    "django",
    "java",
    "sql",
    "machine learning",
    "data science",
    "react",
    "javascript",
    "html",
    "css",
    "c++",
    "c",
    "node",
    "flask",
    "git",
]


def extract_text_from_resume(file_path):

    text = ""

    if file_path.endswith(".pdf"):
        text = extract_text(file_path)

    elif file_path.endswith(".docx"):
        doc = Document(file_path)

        for para in doc.paragraphs:
            text += para.text

    return text.lower()


def extract_skills(text):

    skills_found = []

    for skill in SKILLS_DB:
        if skill in text:
            skills_found.append(skill)

    return skills_found


def calculate_match(candidate_skills, required_skills):
    if not candidate_skills:
        candidate_skills = ""
    if not required_skills:
        required_skills = ""
    candidate = set(candidate_skills.lower().split(","))
    required = set(required_skills.lower().split(","))
    matched = candidate.intersection(required)
    missing = required - candidate
    if len(required) == 0:
        return 0
    else:
        score = (len(matched) / len(required)) * 100
    return round(score, 2), matched, missing