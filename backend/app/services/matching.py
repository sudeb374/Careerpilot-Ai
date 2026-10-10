import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.opportunity import Opportunity, OpportunitySkill
from app.models.profile import Profile, ProfileSkill
from app.schemas.matching import (
    MatchComponentScore,
    MatchExplanation,
    OpportunityMatchResponse,
)
from app.services.embeddings import calculate_max_similarity, is_model_available


@dataclass
class CandidateEvidence:
    candidate_skill_ids: set[str]
    desired_roles: list[str]
    work_model: list[str]
    locations: list[str]
    preferred_domains: list[str]
    years_exp: float
    education_text: list[str]


def normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'[^a-z0-9]', '', text.lower())


async def get_candidate_evidence(db: AsyncSession, profile_id: uuid.UUID) -> CandidateEvidence:
    prof_stmt = (
        select(Profile)
        .options(
            selectinload(Profile.career_preferences),
            selectinload(Profile.skills).selectinload(ProfileSkill.skill),
            selectinload(Profile.resumes),
            selectinload(Profile.experiences),
            selectinload(Profile.educations)
        )
        .where(Profile.id == profile_id)
    )
    prof_res = await db.execute(prof_stmt)
    profile = prof_res.scalar_one_or_none()
    
    if not profile:
        raise ValueError("Profile not found")

    candidate_skill_ids: set[str] = set()
    for ps in profile.skills:
        if ps.skill_id:
            candidate_skill_ids.add(str(ps.skill_id))

    active_resume = next((r for r in profile.resumes if r.is_active), None)
    if active_resume and active_resume.has_structured_data:
        resume_skills = active_resume.structured_data.get("skills", [])
        for rs in resume_skills:
            if rs.get("skill_id"):
                candidate_skill_ids.add(str(rs["skill_id"]))
                
    prefs = profile.career_preferences
    desired_roles = prefs.desired_roles if prefs and prefs.desired_roles else []
    work_model = prefs.work_model if prefs and prefs.work_model else []
    locations = prefs.locations if prefs and prefs.locations else []
    preferred_domains = prefs.preferred_domains if prefs and prefs.preferred_domains else []
    
    years_exp = 0.0
    for exp in profile.experiences:
        if exp.start_date:
            end = exp.end_date if exp.end_date else datetime.now(timezone.utc).date()
            days = (end - exp.start_date).days
            if days > 0:
                years_exp += days / 365.25

    education_text = []
    for edu in profile.educations:
        edu_parts = []
        if edu.degree:
            edu_parts.append(edu.degree)
        if edu.field_of_study:
            edu_parts.append(edu.field_of_study)
        if edu_parts:
            education_text.append(" in ".join(edu_parts))

    return CandidateEvidence(
        candidate_skill_ids=candidate_skill_ids,
        desired_roles=desired_roles,
        work_model=work_model,
        locations=locations,
        preferred_domains=preferred_domains,
        years_exp=years_exp,
        education_text=education_text
    )


async def calculate_match_with_evidence(
    opportunity: Opportunity, 
    evidence: CandidateEvidence
) -> OpportunityMatchResponse:
    if opportunity.status != "Published":
        return OpportunityMatchResponse(
            scoring_version="1.0",
            score=None,
            score_label=None,
            data_coverage="Unavailable",
            matched_skills=[],
            missing_required_skills=[],
            matched_factors=[],
            mismatched_preferences=["Opportunity is not Published"],
            component_scores=[],
            components_not_assessed=["Required Skills", "Desired Role", "Work Model & Location", "Experience & Education", "Preferred Domain"],
            explanation=MatchExplanation(
                summary="Opportunity is not available for matching.",
                strengths=[],
                limitations=["Opportunity is not Published."]
            )
        )

    components = []
    not_assessed = []
    matched_skills = []
    missing_skills = []
    matched_factors = []
    mismatched_preferences = []
    strengths = []
    limitations = []
    
    total_awarded = 0.0
    total_assessable_max = 0.0

    # 1. Required Skills (40 pts)
    opp_skills = opportunity.skills
    if opp_skills:
        max_skill_pts = 40.0
        total_assessable_max += max_skill_pts
        matched_count = 0
        for os in opp_skills:
            if str(os.skill_id) in evidence.candidate_skill_ids:
                matched_count += 1
                matched_skills.append(os.skill.name)
            else:
                missing_skills.append(os.skill.name)
        
        awarded_skill_pts = (matched_count / len(opp_skills)) * max_skill_pts
        total_awarded += awarded_skill_pts
        
        components.append(MatchComponentScore(
            component="Required Skills",
            awarded_points=round(awarded_skill_pts, 2),
            max_points=max_skill_pts,
            explanation=f"Matched {matched_count} of {len(opp_skills)} required skills."
        ))
        if matched_count == len(opp_skills):
            strengths.append("Meets all required skills.")
        elif matched_count > 0:
            strengths.append(f"Meets some required skills ({matched_count}/{len(opp_skills)}).")
        else:
            limitations.append("Lacks all required skills.")
    else:
        not_assessed.append("Required Skills")
        limitations.append("Opportunity does not specify required skills.")

    # 2. Desired Role (20 pts)
    if evidence.desired_roles:
        max_role_pts = 20.0
        total_assessable_max += max_role_pts
        
        opp_title_norm = normalize_text(opportunity.title)
        role_matched = False
        matched_role_name = ""
        
        model_available = is_model_available()
        if model_available:
            score, cand_role = await calculate_max_similarity(opportunity.title, evidence.desired_roles)
            if score is not None:
                if score >= 0.5:
                    role_matched = True
                    matched_role_name = cand_role
            else:
                model_available = False # Inference error, allow fallback
                
        if not model_available:
            for dr in evidence.desired_roles:
                dr_norm = normalize_text(dr)
                if dr_norm and (dr_norm in opp_title_norm or opp_title_norm in dr_norm):
                    role_matched = True
                    matched_role_name = dr
                    break
                
        if role_matched:
            total_awarded += max_role_pts
            components.append(MatchComponentScore(
                component="Desired Role",
                awarded_points=max_role_pts,
                max_points=max_role_pts,
                explanation="Opportunity title matches desired role."
            ))
            matched_factors.append(f"Role: {matched_role_name}")
            strengths.append("Matches your desired role.")
        else:
            components.append(MatchComponentScore(
                component="Desired Role",
                awarded_points=0.0,
                max_points=max_role_pts,
                explanation="Opportunity title does not match your desired roles."
            ))
            mismatched_preferences.append("Desired Role")
            limitations.append("Does not match desired roles.")
    else:
        not_assessed.append("Desired Role")
        limitations.append("Candidate has not specified desired roles.")

    # 3. Work Model & Location (15 pts)
    if evidence.work_model or evidence.locations:
        max_model_loc_pts = 15.0
        total_assessable_max += max_model_loc_pts
        awarded = 0.0
        
        model_matched = False
        if evidence.work_model and opportunity.work_model:
            opp_model_norm = normalize_text(opportunity.work_model)
            for m in evidence.work_model:
                if normalize_text(m) == opp_model_norm:
                    model_matched = True
                    break
        elif not evidence.work_model:
            model_matched = True
            
        loc_matched = False
        if evidence.locations and opportunity.locations:
            opp_locs_norm = [normalize_text(l) for l in opportunity.locations]
            for l in evidence.locations:
                l_norm = normalize_text(l)
                if any(l_norm in opp_loc for opp_loc in opp_locs_norm) or any(opp_loc in l_norm for opp_loc in opp_locs_norm):
                    loc_matched = True
                    break
        elif not evidence.locations:
            loc_matched = True
            
        if model_matched:
            awarded += 7.5
            if evidence.work_model:
                matched_factors.append(f"Work Model: {opportunity.work_model}")
        else:
            mismatched_preferences.append("Work Model")
            
        if loc_matched:
            awarded += 7.5
            if evidence.locations:
                matched_factors.append("Location")
        else:
            mismatched_preferences.append("Location")
            
        total_awarded += awarded
        components.append(MatchComponentScore(
            component="Work Model & Location",
            awarded_points=awarded,
            max_points=max_model_loc_pts,
            explanation=f"Work model match: {model_matched}. Location match: {loc_matched}."
        ))
        if awarded == 15.0:
            strengths.append("Matches work model and location preferences.")
    else:
        not_assessed.append("Work Model & Location")
        limitations.append("Candidate has not specified work model or location preferences.")

    # 4. Experience & Education (15 pts)
    exp_edu_pts = 0.0
    exp_edu_max = 0.0
    
    if opportunity.required_experience_min is not None and opportunity.required_experience_min > 0:
        exp_edu_max += 7.5
        if evidence.years_exp >= opportunity.required_experience_min:
            if opportunity.required_experience_max is not None:
                if evidence.years_exp <= opportunity.required_experience_max:
                    exp_edu_pts += 7.5
                    matched_factors.append("Experience")
            else:
                exp_edu_pts += 7.5
                matched_factors.append("Experience")
    else:
        exp_edu_max += 7.5
        exp_edu_pts += 7.5
        
    edu_explanation = "Education explicitly required: False."
    if opportunity.education_requirements:
        exp_edu_max += 7.5
        if evidence.education_text:
            edu_score, edu_match = await calculate_max_similarity(opportunity.education_requirements, evidence.education_text)
            if edu_score is not None and edu_score >= 0.4:
                exp_edu_pts += 7.5
                matched_factors.append("Education")
                edu_explanation = "Education aligns with requirements."
            else:
                edu_explanation = "Education may not meet requirements."
        else:
            not_assessed.append("Education Text")
            limitations.append("Opportunity requires education, but none is in candidate profile.")
            exp_edu_max -= 7.5
            edu_explanation = "Education requirements present, but candidate has no education records."
    else:
        exp_edu_max += 7.5
        exp_edu_pts += 7.5
        
    total_assessable_max += exp_edu_max
    total_awarded += exp_edu_pts
    components.append(MatchComponentScore(
        component="Experience & Education",
        awarded_points=exp_edu_pts,
        max_points=exp_edu_max,
        explanation=f"Experience verified. {edu_explanation}"
    ))

    # 5. Preferred Domain (10 pts)
    if evidence.preferred_domains and opportunity.domain:
        max_domain_pts = 10.0
        total_assessable_max += max_domain_pts
        
        opp_domain_norm = normalize_text(opportunity.domain)
        domain_matched = False
        for pd in evidence.preferred_domains:
            if normalize_text(pd) == opp_domain_norm:
                domain_matched = True
                break
                
        if domain_matched:
            total_awarded += max_domain_pts
            components.append(MatchComponentScore(
                component="Preferred Domain",
                awarded_points=max_domain_pts,
                max_points=max_domain_pts,
                explanation="Opportunity domain matches preferred domains."
            ))
            matched_factors.append(f"Domain: {opportunity.domain}")
        else:
            components.append(MatchComponentScore(
                component="Preferred Domain",
                awarded_points=0.0,
                max_points=max_domain_pts,
                explanation="Opportunity domain does not match preferred domains."
            ))
            mismatched_preferences.append("Preferred Domain")
    else:
        not_assessed.append("Preferred Domain")
        if not evidence.preferred_domains:
            limitations.append("Candidate has not specified preferred domains.")
        else:
            limitations.append("Opportunity does not specify a domain.")
            
    # Calculate Final Normalized Score
    if total_assessable_max > 0:
        normalized_score = (total_awarded / total_assessable_max) * 100
        score = round(normalized_score, 1)
        
        coverage_ratio = total_assessable_max / 100.0
        if coverage_ratio >= 0.8:
            data_coverage = "High"
        elif coverage_ratio >= 0.4:
            data_coverage = "Moderate"
        else:
            data_coverage = "Limited"
            
        if score >= 80:
            score_label = "Strong Match"
        elif score >= 50:
            score_label = "Good Match"
        else:
            score_label = "Weak Match"
    else:
        score = None
        score_label = None
        data_coverage = "Unavailable"
        limitations.append("Insufficient data to compute a match score.")

    summary = f"Match score is {score}/100 based on {data_coverage.lower()} data coverage." if score is not None else "Match score unavailable due to insufficient data."

    return OpportunityMatchResponse(
        scoring_version="1.0",
        score=score,
        score_label=score_label,
        data_coverage=data_coverage,
        matched_skills=matched_skills,
        missing_required_skills=missing_skills,
        matched_factors=matched_factors,
        mismatched_preferences=mismatched_preferences,
        component_scores=components,
        components_not_assessed=not_assessed,
        explanation=MatchExplanation(
            summary=summary,
            strengths=strengths,
            limitations=limitations
        )
    )


async def calculate_opportunity_match(
    db: AsyncSession,
    profile_id: uuid.UUID,
    opportunity_id: uuid.UUID
) -> OpportunityMatchResponse:
    opp_stmt = (
        select(Opportunity)
        .options(
            selectinload(Opportunity.skills).selectinload(OpportunitySkill.skill)
        )
        .where(Opportunity.id == opportunity_id)
    )
    opp_res = await db.execute(opp_stmt)
    opportunity = opp_res.scalar_one_or_none()
    
    if not opportunity:
        raise ValueError("Opportunity not found")

    evidence = await get_candidate_evidence(db, profile_id)
    return await calculate_match_with_evidence(opportunity, evidence)
