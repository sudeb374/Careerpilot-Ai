import pytest
from unittest.mock import patch
import asyncio
from app.services.matching import CandidateEvidence, calculate_match_with_evidence
from app.models.opportunity import Opportunity
from app.schemas.matching import OpportunityMatchResponse

from unittest.mock import patch, AsyncMock

# Mock the embeddings to return expected values
@pytest.fixture
def mock_embeddings():
    with patch('app.services.matching.is_model_available', return_value=True), \
         patch('app.services.matching.calculate_max_similarity', new_callable=AsyncMock) as mock_sim:
        yield mock_sim

@pytest.mark.anyio
async def test_semantic_role_match(mock_embeddings):
    # Setup mock to return a high score for role match
    mock_embeddings.side_effect = lambda target, candidates: (0.85, "Software Engineer") if "Software Engineer" in candidates else (None, None)
    
    opp = Opportunity(title="Backend Developer", education_requirements=None, status="Published")
    evidence = CandidateEvidence(
        candidate_skill_ids=set(), desired_roles=["Software Engineer"],
        work_model=[], locations=[], preferred_domains=[], years_exp=0.0, education_text=[]
    )
    
    resp = await calculate_match_with_evidence(opp, evidence)
    assert resp.score == 100.0
    role_comp = next(c for c in resp.component_scores if c.component == "Desired Role")
    assert role_comp.awarded_points == 20.0
    
@pytest.mark.anyio
async def test_semantic_education_match(mock_embeddings):
    # Mock education similarity
    def mock_sim_side_effect(target, candidates):
        if "Computer Science" in target:
            return (0.9, "B.S. in Computer Science")
        return (None, None)
    mock_embeddings.side_effect = mock_sim_side_effect
    
    opp = Opportunity(title="Test", education_requirements="Bachelors in Computer Science", status="Published")
    evidence = CandidateEvidence(
        candidate_skill_ids=set(), desired_roles=[],
        work_model=[], locations=[], preferred_domains=[], years_exp=0.0, 
        education_text=["B.S. in Computer Science"]
    )
    
    resp = await calculate_match_with_evidence(opp, evidence)
    assert resp.score == 100.0
    edu_comp = next(c for c in resp.component_scores if c.component == "Experience & Education")
    assert edu_comp.awarded_points == 15.0
    assert "Education aligns with requirements" in edu_comp.explanation

@pytest.mark.anyio
async def test_semantic_education_mismatch(mock_embeddings):
    # Mock low similarity
    mock_embeddings.side_effect = None
    mock_embeddings.return_value = (0.2, "B.A. in History")
    
    opp = Opportunity(title="Test", education_requirements="Bachelors in Computer Science", status="Published")
    evidence = CandidateEvidence(
        candidate_skill_ids=set(), desired_roles=[],
        work_model=[], locations=[], preferred_domains=[], years_exp=0.0, 
        education_text=["B.A. in History"]
    )
    
    resp = await calculate_match_with_evidence(opp, evidence)
    assert resp.score == 50.0
    edu_comp = next(c for c in resp.component_scores if c.component == "Experience & Education")
    assert edu_comp.awarded_points == 7.5 # Only gets Experience points
    assert "Education may not meet requirements" in edu_comp.explanation

@pytest.mark.anyio
async def test_deterministic_fallback():
    # Test when model is unavailable
    with patch('app.services.matching.is_model_available', return_value=False):
        opp = Opportunity(title="Software Engineer", education_requirements=None, status="Published")
        evidence = CandidateEvidence(
            candidate_skill_ids=set(), desired_roles=["Software Engineer"],
            work_model=[], locations=[], preferred_domains=[], years_exp=0.0, education_text=[]
        )
        
        resp = await calculate_match_with_evidence(opp, evidence)
        role_comp = next(c for c in resp.component_scores if c.component == "Desired Role")
        assert role_comp.awarded_points == 20.0

@pytest.mark.anyio
async def test_semantic_role_mismatch_no_fallback(mock_embeddings):
    # Test that a score below threshold does not silently trigger exact fallback
    # even if there's a substring match.
    mock_embeddings.side_effect = None
    mock_embeddings.return_value = (0.3, "Junior Developer")
    
    opp = Opportunity(title="Junior Developer", education_requirements=None, status="Published")
    evidence = CandidateEvidence(
        candidate_skill_ids=set(), desired_roles=["Junior Developer"],
        work_model=[], locations=[], preferred_domains=[], years_exp=0.0, education_text=[]
    )
    
    resp = await calculate_match_with_evidence(opp, evidence)
    # The score is 0.3 (< 0.5 threshold). It should NOT fall back to exact match,
    # so role points should be 0.
    role_comp = next(c for c in resp.component_scores if c.component == "Desired Role")
    assert role_comp.awarded_points == 0.0
