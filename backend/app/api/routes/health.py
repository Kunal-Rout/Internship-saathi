from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.internship import Internship

router = APIRouter()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    count = db.query(Internship).count()
    return {
        "status": "healthy",
        "app": "Internship Saathi",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "sample_data_count": count,
        "disclaimer": "Demonstration prototype. Sample internships only. Not an official government portal."
    }
