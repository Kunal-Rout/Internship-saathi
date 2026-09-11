from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.internship import Internship
from app.models.sector import Sector
from app.schemas.internship import (
    InternshipDetail,
    InternshipBase,
    SectorSummary,
    SkillSummary,
    EducationSummary
)
from app.schemas.common import PaginatedResponse, PaginatedMeta

router = APIRouter()

@router.get("/internships", response_model=PaginatedResponse[InternshipBase])
def list_internships(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=50, description="Items per page (max 50)"),
    sector: Optional[str] = Query(None, description="Filter by sector code"),
    work_mode: Optional[str] = Query(None, description="Filter by work mode (onsite, hybrid, remote)"),
    state: Optional[str] = Query(None, description="Filter by state"),
    db: Session = Depends(get_db)
):
    query = db.query(Internship).filter(Internship.is_active == True)

    if sector:
        query = query.join(Internship.sector).filter(Sector.code == sector.strip().lower())
    if work_mode:
        query = query.filter(func.lower(Internship.work_mode) == work_mode.strip().lower())
    if state:
        query = query.filter(func.lower(Internship.state) == state.strip().lower())

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    records = query.order_by(Internship.id).offset((page - 1) * page_size).limit(page_size).all()

    items = [
        InternshipBase(
            id=i.id,
            title=i.title,
            organization_name=i.organization_name,
            sector=SectorSummary(
                id=i.sector.id,
                code=i.sector.code,
                name_en=i.sector.name_en,
                name_hi=i.sector.name_hi
            ),
            state=i.state,
            district=i.district,
            work_mode=i.work_mode,
            duration_months=i.duration_months,
            stipend_inr=i.stipend_inr,
            deadline=i.deadline,
            is_active=i.is_active,
            allows_no_skills=i.allows_no_skills,
            is_sample=i.is_sample
        )
        for i in records
    ]

    return PaginatedResponse(
        items=items,
        pagination=PaginatedMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )

@router.get("/internships/{internship_id}", response_model=InternshipDetail)
def get_internship_by_id(internship_id: str, db: Session = Depends(get_db)):
    clean_id = internship_id.strip().upper()
    inst = db.query(Internship).filter(Internship.id == clean_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail=f"Internship with ID '{internship_id}' not found.")

    return InternshipDetail(
        id=inst.id,
        title=inst.title,
        organization_name=inst.organization_name,
        description=inst.description,
        sector=SectorSummary(
            id=inst.sector.id,
            code=inst.sector.code,
            name_en=inst.sector.name_en,
            name_hi=inst.sector.name_hi
        ),
        state=inst.state,
        district=inst.district,
        work_mode=inst.work_mode,
        duration_months=inst.duration_months,
        stipend_inr=inst.stipend_inr,
        deadline=inst.deadline,
        is_active=inst.is_active,
        allows_no_skills=inst.allows_no_skills,
        is_sample=inst.is_sample,
        required_skills=[
            SkillSummary(id=sk.id, code=sk.code, name_en=sk.name_en, name_hi=sk.name_hi)
            for sk in inst.required_skills
        ],
        accepted_educations=[
            EducationSummary(id=ed.id, code=ed.code, label_en=ed.label_en, label_hi=ed.label_hi)
            for ed in inst.accepted_educations
        ]
    )
