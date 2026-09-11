from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class EducationCategory(Base):
    __tablename__ = "education_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    label_en: Mapped[str] = mapped_column(String(100), nullable=False)
    label_hi: Mapped[str] = mapped_column(String(100), nullable=False)

    internships = relationship(
        "Internship",
        secondary="internship_educations",
        back_populates="accepted_educations"
    )
