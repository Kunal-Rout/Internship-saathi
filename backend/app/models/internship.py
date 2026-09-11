from datetime import date
from sqlalchemy import Integer, String, Text, Boolean, Date, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

# Association Table: Internship <-> Skill
internship_skills = Table(
    "internship_skills",
    Base.metadata,
    Column("internship_id", String(32), ForeignKey("internships.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

# Association Table: Internship <-> EducationCategory
internship_educations = Table(
    "internship_educations",
    Base.metadata,
    Column("internship_id", String(32), ForeignKey("internships.id", ondelete="CASCADE"), primary_key=True),
    Column("education_id", Integer, ForeignKey("education_categories.id", ondelete="CASCADE"), primary_key=True),
)

class Internship(Base):
    __tablename__ = "internships"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    organization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    sector_id: Mapped[int] = mapped_column(Integer, ForeignKey("sectors.id"), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    work_mode: Mapped[str] = mapped_column(String(20), nullable=False)  # "onsite", "hybrid", "remote"
    duration_months: Mapped[int] = mapped_column(Integer, nullable=False)
    stipend_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    deadline: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    allows_no_skills: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    sector = relationship("Sector", back_populates="internships")
    required_skills = relationship(
        "Skill",
        secondary=internship_skills,
        back_populates="internships",
        lazy="selectin"
    )
    accepted_educations = relationship(
        "EducationCategory",
        secondary=internship_educations,
        back_populates="internships",
        lazy="selectin"
    )
