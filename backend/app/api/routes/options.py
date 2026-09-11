import json
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.education import EducationCategory
from app.models.sector import Sector
from app.models.skill import Skill
from app.schemas.options import (
    OptionsResponse,
    LocalizedOption,
    SectorOption,
    SkillOption,
    StateDistrictOption,
    WorkModeOption,
    DistrictOption
)

router = APIRouter()
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

@router.get("/options", response_model=OptionsResponse)
def get_options(db: Session = Depends(get_db)):
    # Read taxonomy json for static states and districts and work modes
    taxonomy_file = DATA_DIR / "taxonomy.json"
    with open(taxonomy_file, "r", encoding="utf-8") as f:
        tax_data = json.load(f)

    # Education categories from DB
    edu_records = db.query(EducationCategory).all()
    # Filter out internal 'any' if needed or present it cleanly
    edu_options = [
        LocalizedOption(code=e.code, label_en=e.label_en, label_hi=e.label_hi)
        for e in edu_records if e.code != "any"
    ]

    # Sectors from DB
    sec_records = db.query(Sector).all()
    sec_options = [
        SectorOption(code=s.code, name_en=s.name_en, name_hi=s.name_hi)
        for s in sec_records
    ]

    # Skills from DB
    skill_records = db.query(Skill).all()
    skill_options = [
        SkillOption(code=sk.code, name_en=sk.name_en, name_hi=sk.name_hi, sector_code=sk.sector_code)
        for sk in skill_records
    ]

    # States & Districts from taxonomy.json
    states_data = tax_data.get("states_and_districts", [])
    states_options = [
        StateDistrictOption(
            state_en=s["state_en"],
            state_hi=s["state_hi"],
            districts=[
                DistrictOption(name_en=d["name_en"], name_hi=d["name_hi"])
                for d in s.get("districts", [])
            ]
        )
        for s in states_data
    ]

    work_modes_data = tax_data.get("work_modes", [])
    work_mode_options = [
        WorkModeOption(code=wm["code"], label_en=wm["label_en"], label_hi=wm["label_hi"])
        for wm in work_modes_data
    ]

    return OptionsResponse(
        education_categories=edu_options,
        sectors=sec_options,
        skills=skill_options,
        states_and_districts=states_options,
        work_modes=work_mode_options
    )
