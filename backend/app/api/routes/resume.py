"""
Resume parsing endpoint - privacy-preserving, in-memory only.
Accepts PDF/DOCX, extracts text, matches against skill taxonomy.
"""
import io
import logging
import re
from typing import List, Optional, Set

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services.normalization import normalize_skill, SKILL_ALIASES
from app.services.embeddings import get_embedding_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["Resume"])

# Maximum file size: 5 MB
MAX_FILE_SIZE = 5 * 1024 * 1024

# Known skill codes for matching (will be populated from taxonomy at runtime)
_skill_codes: Set[str] = set()


def get_skill_codes() -> Set[str]:
    """Get all known skill codes from the taxonomy."""
    global _skill_codes
    if not _skill_codes:
        # Import here to avoid circular imports
        from app.db.session import SessionLocal
        from app.models.skill import Skill

        db = SessionLocal()
        try:
            skills = db.query(Skill).all()
            _skill_codes = {sk.code for sk in skills}
            # Add aliases as well
            _skill_codes.update(SKILL_ALIASES.keys())
        finally:
            db.close()
    return _skill_codes


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using pypdf."""
    try:
        import pypdf
        pdf_file = io.BytesIO(file_bytes)
        reader = pypdf.PdfReader(pdf_file)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        import docx
        doc_file = io.BytesIO(file_bytes)
        doc = docx.Document(doc_file)
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text_parts.append(cell.text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse DOCX: {str(e)}")


def detect_skills_from_text(text: str) -> List[str]:
    """
    Match extracted text against skill taxonomy (case-insensitive, alias-aware).
    Returns list of detected skill codes, trimmed to the API schema limit.
    """
    text_lower = text.lower()
    detected: Set[str] = set()

    # Get all skill codes and aliases
    skill_codes = get_skill_codes()

    # Direct skill code matching (whole word)
    for code in skill_codes:
        # Match as whole word with word boundaries
        import re
        pattern = r'\b' + re.escape(code.replace('_', r'[\s_\-]?')) + r'\b'
        if re.search(pattern, text_lower):
            detected.add(code)

    # Alias matching
    for alias, canonical in SKILL_ALIASES.items():
        if alias.lower() in text_lower:
            detected.add(canonical)

    # Special multi-word skill detection
    skill_patterns = {
        "machine_learning": [
            r"machine learning", r"deep learning", r"ml\b", r"ai\b", r"artificial intelligence",
            r"neural network", r"pytorch", r"tensorflow", r"keras", r"scikit.learn",
            r"supervised", r"unsupervised", r"classification", r"regression", r"clustering"
        ],
        "python": [r"\bpython\b", r"\bpy\b", r"python3"],
        "sql": [r"\bsql\b", r"mysql", r"postgres", r"postgresql", r"nosql", r"mongodb"],
        "data_visualization": [r"visualization", r"dashboard", r"power.?bi", r"tableau", r"looker", r"matplotlib", r"seaborn", r"plotly"],
        "statistics": [r"statistics", r"stats\b", r"probability", r"hypothesis testing", r"a/b testing"],
        "pandas": [r"pandas", r"dataframe", r"data analysis"],
        "numpy": [r"numpy", r"np\b", r"numerical python"],
        "docker": [r"docker", r"container"],
        "kubernetes": [r"kubernetes", r"k8s\b", r"kube"],
        "git": [r"\bgit\b", r"github", r"gitlab", r"version control"],
        "ci_cd": [r"ci.?cd", r"jenkins", r"github actions", r"gitlab ci", r"continuous integration"],
        "rest_apis": [r"rest.?api", r"restful", r"api design", r"graphql"],
        "fastapi": [r"fastapi", r"django", r"flask"],
        "react": [r"react", r"reactjs", r"react.js", r"frontend", r"jsx", r"hooks"],
        "typescript": [r"typescript", r"\bts\b", r"type script"],
        "javascript": [r"javascript", r"\bjs\b", r"node\.js", r"nodejs", r"express"],
        "html_css": [r"html", r"css", r"tailwind", r"bootstrap", r"sass", r"scss"],
        "java": [r"\bjava\b", r"spring boot", r"spring", r"hibernate", r"jpa", r"maven", r"gradle"],
        "aws": [r"aws", r"amazon web services", r"ec2", r"s3", r"lambda", r"cloudformation"],
        "linux": [r"linux", r"ubuntu", r"unix", r"bash", r"shell script"],
        "terraform": [r"terraform", r"iac", r"infrastructure as code"],
        "ansible": [r"ansible", r"configuration management"],
        "prometheus": [r"prometheus", r"grafana", r"monitoring"],
        "test_automation": [r"selenium", r"playwright", r"cypress", r"pytest", r"junit", r"test automation", r"qa\b", r"quality assurance"],
        "kafka": [r"kafka", r"message queue", r"event streaming"],
        "spark": [r"spark", r"pyspark", r"big data"],
        "airflow": [r"airflow", r"orchestration", r"data pipeline"],
        "communication_skills": [r"communication", r"spoken english", r"presentation", r"public speaking"],
        "ms_excel": [r"excel", r"spreadsheet", r"vlookup", r"pivot table"],
        "data_entry": [r"data entry", r"typing"],
    }

    for skill, patterns in skill_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                detected.add(skill)
                break

    # Keep the parsed resume result compatible with the recommendation profile
    # schema, which already enforces a maximum skill list size of 20.
    return sorted(list(detected))[:20]


def detect_education_level(text: str) -> Optional[str]:
    """Infer education level from resume text."""
    text_lower = text.lower()

    education_patterns = {
        "masters": [r"master", r"m\.?tech", r"m\.?sc", r"m\.?com", r"m\.?a\b", r"mba", r"post.?grad", r"pg\b"],
        "bachelors": [r"bachelor", r"b\.?tech", r"b\.?sc", r"b\.?com", r"b\.?a\b", r"b\.?e\b", r"graduat", r"degree"],
        "diploma": [r"diploma", r"polytechnic"],
        "iti": [r"iti\b", r"industrial training"],
        "twelfth_pass": [r"12th", r"12\b", r"intermediate", r"hsc", r"higher secondary", r"senior secondary"],
        "tenth_pass": [r"10th", r"10\b", r"matric", r"ssc", r"secondary"],
    }

    # Check from highest to lowest
    for level, patterns in [
        ("masters", education_patterns["masters"]),
        ("bachelors", education_patterns["bachelors"]),
        ("diploma", education_patterns["diploma"]),
        ("iti", education_patterns["iti"]),
        ("twelfth_pass", education_patterns["twelfth_pass"]),
        ("tenth_pass", education_patterns["tenth_pass"]),
    ]:
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return level

    return None


class ParsedResumeResponse(BaseModel):
    detected_skills: List[str] = Field(..., description="List of detected skill codes")
    detected_education: Optional[str] = Field(None, description="Inferred education level code")
    resume_text: str = Field(..., description="Truncated resume text (first 2000 chars)")
    privacy_note_en: str = "Your resume is processed in memory and never stored."
    privacy_note_hi: str = "आपका रिज्यूमे केवल मेमोरी में प्रोसेस किया जाता है और कभी स्टोर नहीं किया जाता।"


@router.post("/parse", response_model=ParsedResumeResponse)
async def parse_resume(file: UploadFile = File(...)):
    """
    Parse uploaded resume (PDF or DOCX) and extract skills.
    File is processed IN MEMORY ONLY - never written to disk or database.
    """
    # Validate file size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB."
        )

    # Validate file type
    filename = file.filename or ""
    content_type = file.content_type or ""

    is_pdf = filename.lower().endswith(".pdf") or content_type == "application/pdf"
    is_docx = filename.lower().endswith(".docx") or content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    if not (is_pdf or is_docx):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a PDF or DOCX file."
        )

    # Extract text IN MEMORY ONLY
    if is_pdf:
        text = extract_text_from_pdf(file_bytes)
    else:
        text = extract_text_from_docx(file_bytes)

    if not text or not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from the file. Please ensure it's not scanned/image-based."
        )

    # Detect skills and education
    detected_skills = detect_skills_from_text(text)
    detected_education = detect_education_level(text)

    # Truncate resume text for client (first 2000 chars)
    truncated_text = text[:2000]

    logger.info(f"Parsed resume: {len(detected_skills)} skills detected, education: {detected_education}")

    return ParsedResumeResponse(
        detected_skills=detected_skills,
        detected_education=detected_education,
        resume_text=truncated_text,
    )