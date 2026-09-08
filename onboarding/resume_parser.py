"""
resume_parser.py  —  Enhanced AI-powered resume parser
Extracts skills from PDF / DOCX resumes and stores them on the Employee profile.
"""
import re

try:
    from pdfminer.high_level import extract_text as pdf_extract
except ImportError:
    pdf_extract = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None


# ─── SKILLS DATABASE ─────────────────────────────────────────────────────────
# Grouped by category so we can show structured skill tags

SKILLS_DB = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c", "ruby",
        "php", "swift", "kotlin", "go", "rust", "scala", "r", "matlab",
        "perl", "dart", "lua", "bash", "shell",
    ],
    "Web Development": [
        "html", "css", "react", "angular", "vue", "next.js", "nuxt",
        "django", "flask", "fastapi", "node", "node.js", "express",
        "bootstrap", "tailwind", "jquery", "rest api", "graphql",
        "spring boot", "laravel", "rails",
    ],
    "Data & AI": [
        "machine learning", "deep learning", "data science", "nlp",
        "computer vision", "tensorflow", "pytorch", "keras", "sklearn",
        "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn",
        "data analysis", "data visualization", "power bi", "tableau",
        "statistics", "regression", "classification",
    ],
    "Databases": [
        "sql", "mysql", "postgresql", "sqlite", "mongodb", "redis",
        "oracle", "cassandra", "firebase", "dynamodb", "elasticsearch",
    ],
    "DevOps & Cloud": [
        "docker", "kubernetes", "aws", "azure", "gcp", "linux",
        "git", "github", "gitlab", "ci/cd", "jenkins", "terraform",
        "ansible", "nginx",
    ],
    "Mobile": [
        "android", "ios", "react native", "flutter", "xamarin",
    ],
    "Soft Skills": [
        "leadership", "communication", "teamwork", "problem solving",
        "project management", "agile", "scrum", "jira",
    ],
}

# Flat list for quick lookup
ALL_SKILLS = []
for skills in SKILLS_DB.values():
    ALL_SKILLS.extend(skills)


def extract_text_from_resume(file_path: str) -> str:
    """Extract raw text from PDF or DOCX file."""
    text = ""
    if file_path.lower().endswith(".pdf"):
        if pdf_extract:
            try:
                text = pdf_extract(file_path) or ""
            except Exception:
                text = ""
    elif file_path.lower().endswith(".docx"):
        if DocxDocument:
            try:
                doc = DocxDocument(file_path)
                text = "\n".join(p.text for p in doc.paragraphs)
            except Exception:
                text = ""
    return text


def extract_skills(text: str) -> list[str]:
    """
    Scan the text and return a list of matched skills.
    Uses word-boundary matching to avoid false positives (e.g. 'C' in 'CISCO').
    """
    text_lower = text.lower()
    found = []
    for skill in ALL_SKILLS:
        # Use word boundary for short/ambiguous skills
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


def extract_skills_categorised(text: str) -> dict:
    """Return skills grouped by category."""
    text_lower = text.lower()
    result = {}
    for category, skills in SKILLS_DB.items():
        matched = []
        for skill in skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                matched.append(skill)
        if matched:
            result[category] = matched
    return result


def parse_resume_and_update_employee(employee, file_path: str) -> dict:
    """
    Full pipeline: extract text → find skills → save to Employee.skills.
    Returns a summary dict with skills found.
    """
    text = extract_text_from_resume(file_path)
    if not text.strip():
        return {"skills": [], "categorised": {}, "text_found": False}

    skills = extract_skills(text)
    categorised = extract_skills_categorised(text)

    # Persist skills on Employee profile (comma-separated)
    employee.skills = ", ".join(skills)
    employee.save(update_fields=["skills"])

    return {
        "skills": skills,
        "categorised": categorised,
        "text_found": True,
    }


# ─── BACKWARD-COMPAT helpers used in old views ───────────────────────────────

def calculate_match(candidate_skills, required_skills):
    if not candidate_skills:
        candidate_skills = ""
    if not required_skills:
        required_skills = ""
    candidate = set(s.strip() for s in candidate_skills.lower().split(",") if s.strip())
    required  = set(s.strip() for s in required_skills.lower().split(",") if s.strip())
    matched   = candidate.intersection(required)
    missing   = required - candidate
    if not required:
        return 0, set(), set()
    score = round((len(matched) / len(required)) * 100, 2)
    return score, matched, missing
