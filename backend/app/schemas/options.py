from typing import List, Dict
from pydantic import BaseModel

class LocalizedOption(BaseModel):
    code: str
    label_en: str
    label_hi: str

class SectorOption(BaseModel):
    code: str
    name_en: str
    name_hi: str

class SkillOption(BaseModel):
    code: str
    name_en: str
    name_hi: str
    sector_code: str | None = None

class DistrictOption(BaseModel):
    name_en: str
    name_hi: str

class StateDistrictOption(BaseModel):
    state_en: str
    state_hi: str
    districts: List[DistrictOption]

class WorkModeOption(BaseModel):
    code: str
    label_en: str
    label_hi: str

class OptionsResponse(BaseModel):
    education_categories: List[LocalizedOption]
    sectors: List[SectorOption]
    skills: List[SkillOption]
    states_and_districts: List[StateDistrictOption]
    work_modes: List[WorkModeOption]
