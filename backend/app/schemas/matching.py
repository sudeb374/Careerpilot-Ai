from typing import Literal

from pydantic import BaseModel


class MatchComponentScore(BaseModel):
    component: str
    awarded_points: float
    max_points: float
    explanation: str

class MatchExplanation(BaseModel):
    summary: str
    strengths: list[str]
    limitations: list[str]

class OpportunityMatchResponse(BaseModel):
    scoring_version: str = "1.0"
    score: float | None = None
    score_label: str | None = None
    data_coverage: Literal["High", "Moderate", "Limited", "Unavailable"]
    matched_skills: list[str]
    missing_required_skills: list[str]
    matched_factors: list[str]
    mismatched_preferences: list[str]
    component_scores: list[MatchComponentScore]
    components_not_assessed: list[str]
    explanation: MatchExplanation

from app.schemas.opportunity import OpportunityListItem


class OpportunityMatchItem(BaseModel):
    opportunity: OpportunityListItem
    match: OpportunityMatchResponse

class PaginatedOpportunityMatchResponse(BaseModel):
    items: list[OpportunityMatchItem]
    page: int
    page_size: int
    total: int
    total_pages: int

