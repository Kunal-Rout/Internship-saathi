from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.recommender import recommender
from app.services.normalization import normalize_education

router = APIRouter()

@router.post("/recommendations", response_model=RecommendationResponse)
def get_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    # Validate education input
    if not request.profile.education or not request.profile.education.strip():
        raise HTTPException(
            status_code=422,
            detail="Education qualification is required."
        )

    norm_edu = normalize_education(request.profile.education)
    if not norm_edu:
        raise HTTPException(
            status_code=422,
            detail=f"Unrecognized education qualification '{request.profile.education}'. Please choose from supported options."
        )

    response = recommender.recommend(
        profile=request.profile,
        db=db,
        limit=request.limit
    )

    return response
