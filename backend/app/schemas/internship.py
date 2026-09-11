from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class SkillSummary(BaseModel):
    id: int
    code: str
    name_en: str
    name_hi: str

class EducationSummary(BaseModel):
    id: int
    code: str
    label_en: str
    label_hi: str

class SectorSummary(BaseModel):
    id: int
    code: str
    name_en: str
    name_hi: str

class InternshipBase(BaseModel):
    id: str
    title: str
    organization_name: str
    sector: SectorSummary
    state: str
    district: str
    work_mode: str
    duration_months: int
    stipend_inr: int
    deadline: date
    is_active: bool
    allows_no_skills: bool
    is_sample: bool = True

class InternshipDetail(InternshipBase):
    model_config = ConfigDict(from_attributes=True)

    description: str
    required_skills: List[SkillSummary] = []
    accepted_educations: List[EducationSummary] = []

