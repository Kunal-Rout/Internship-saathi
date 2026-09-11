from app.schemas.recommendation import CandidateProfile
from app.services.recommender import recommender

def test_score_bounds_and_renormalization(db_session):
    # Candidate provides only skills, no location or sectors
    profile = CandidateProfile(
        education="twelfth_pass",
        skills=["python"],
        sectors=[],
        state=None,
        district=None,
        preferred_work_mode="any"
    )
    res = recommender.recommend(profile=profile, db=db_session)
    assert len(res.results) > 0
    for item in res.results:
        assert 0.0 <= item.relative_score <= 1.0
        # Effective weights should sum to 1.0 (with slight float rounding tolerance)
        total_eff_weight = (
            item.effective_weights.skill_weight +
            item.effective_weights.sector_weight +
            item.effective_weights.location_weight +
            item.effective_weights.text_weight
        )
        assert abs(total_eff_weight - 1.0) < 0.05

def test_internship_with_no_listed_skills(db_session):
    # Candidate has 10th pass and no skills
    profile = CandidateProfile(
        education="tenth_pass",
        skills=[],
        sectors=["agriculture"],
        state="Maharashtra",
        district="Pune"
    )
    res = recommender.recommend(profile=profile, db=db_session)
    t2_item = next((r for r in res.results if r.internship.id == "TEST-002"), None)
    assert t2_item is not None
    # TEST-002 has allows_no_skills=True
    assert t2_item.internship.allows_no_skills is True
    reason_codes = {r.code for r in t2_item.reasons}
    assert "NO_PRIOR_SKILLS_REQUIRED" in reason_codes

def test_limited_profile_detection(db_session):
    # Candidate gives only education and no other preference
    profile = CandidateProfile(
        education="tenth_pass",
        skills=[],
        sectors=[],
        state=None,
        district=None,
        preferred_work_mode="any"
    )
    res = recommender.recommend(profile=profile, db=db_session)
    assert res.has_limited_profile is True
    assert len(res.results) > 0
    # Suggestions should exist, but marked with LIMITED_PROFILE_EXPLORATION
    first_result = res.results[0]
    reason_codes = [r.code for r in first_result.reasons]
    assert any("LIMITED" in code or "NO_PRIOR_SKILLS" in code for code in reason_codes)

def test_deterministic_tie_breaking(db_session):
    profile = CandidateProfile(
        education="tenth_pass",
        skills=[],
        sectors=[],
        preferred_work_mode="any"
    )
    res1 = recommender.recommend(profile=profile, db=db_session)
    res2 = recommender.recommend(profile=profile, db=db_session)
    ids1 = [r.internship.id for r in res1.results]
    ids2 = [r.internship.id for r in res2.results]
    assert ids1 == ids2

def test_max_results_bounded_at_five(db_session):
    profile = CandidateProfile(
        education="bachelors",
        skills=["python", "ms_excel"],
        sectors=["it_software"],
        preferred_work_mode="any"
    )
    res = recommender.recommend(profile=profile, db=db_session, limit=5)
    assert len(res.results) <= 5
