import re
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.opportunity import Opportunity, OpportunitySkill
from app.models.profile import Profile, ProfileSkill, Skill
from app.schemas.skill_gap import (
    AcquiredSkillItem,
    InsufficientDataStatus,
    JobEvidenceItem,
    LearningSequenceStage,
    MissingSkillItem,
    PriorityTier,
    RequirementLevel,
    SkillCoverageSummary,
    SkillGapRoadmapResponse,
    SkillSource,
)
from app.services.embeddings import calculate_max_similarity, is_model_available
from app.services.opportunity import expire_overdue_opportunities


PREFERRED_HEADER_REGEX = re.compile(
    r'(?i)(?:preferred|nice\s+to\s+have|bonus|plus|desired|optional|good\s+to\s+have)\s*(?:qualifications|skills|requirements|competencies)?\s*[:\n]'
)
REQUIRED_HEADER_REGEX = re.compile(
    r'(?i)(?:required|must\s+have|minimum|basic|core)\s*(?:qualifications|skills|requirements|competencies)?\s*[:\n]'
)


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r'[^a-z0-9]', '', text.lower())


def partition_job_description(description: str | None) -> tuple[str, str]:
    """
    Deterministically partitions a job description into required and desired text blocks.
    Returns (required_text, desired_text).
    """
    if not description:
        return ("", "")

    desc_lower = description.lower()
    pref_match = PREFERRED_HEADER_REGEX.search(desc_lower)
    req_match = REQUIRED_HEADER_REGEX.search(desc_lower)

    if not pref_match:
        # No explicit preferred section found; entire description is treated as general/required
        return (desc_lower, "")

    pref_start = pref_match.start()

    if req_match:
        req_start = req_match.start()
        if req_start < pref_start:
            # Required section comes first, then preferred
            required_part = desc_lower[req_start:pref_start]
            desired_part = desc_lower[pref_start:]
            return (required_part, desired_part)
        else:
            # Preferred comes first, then required
            desired_part = desc_lower[pref_start:req_start]
            required_part = desc_lower[req_start:]
            return (required_part, desired_part)
    else:
        # Only preferred header was detected
        required_part = desc_lower[:pref_start]
        desired_part = desc_lower[pref_start:]
        return (required_part, desired_part)


def is_skill_in_text(skill_name: str, text: str) -> bool:
    if not skill_name or not text:
        return False
    # Use word boundary where reasonable
    escaped = re.escape(skill_name.lower())
    if skill_name.isalnum():
        return bool(re.search(rf'\b{escaped}\b', text))
    return skill_name.lower() in text


async def role_matches_opportunity(
    target_role: str, opp: Opportunity, model_available: bool = False
) -> bool:
    """
    Evaluates whether an opportunity matches a target role via semantic similarity or normalized text.
    """
    norm_target = normalize_text(target_role)
    if not norm_target:
        return False

    norm_title = normalize_text(opp.title)
    norm_domain = normalize_text(opp.domain) if opp.domain else ""

    # Direct substring / containment match
    if norm_target in norm_title or norm_title in norm_target:
        return True
    if norm_domain and (norm_target in norm_domain or norm_domain in norm_target):
        return True

    # Word-level token match (e.g. "Software", "Engineer", "Frontend", "Backend")
    target_tokens = set(re.findall(r'[a-z0-9]+', target_role.lower()))
    title_tokens = set(re.findall(r'[a-z0-9]+', opp.title.lower()))
    if target_tokens and target_tokens.issubset(title_tokens):
        return True
    # If >= 2 tokens match or > 50% of tokens match
    overlap = target_tokens.intersection(title_tokens)
    if len(overlap) >= 2 or (len(target_tokens) > 0 and (len(overlap) / len(target_tokens)) >= 0.6):
        return True

    # Semantic similarity if available
    if model_available:
        try:
            score, _ = await calculate_max_similarity(opp.title, [target_role])
            if score is not None and score >= 0.5:
                return True
        except Exception:
            pass

    return False


async def generate_skill_gap_roadmap(
    db: AsyncSession,
    profile_id: UUID,
    target_role: str | None = None,
) -> SkillGapRoadmapResponse:
    """
    Generates a personalized, evidence-based skill-gap roadmap for an authenticated candidate.
    Uses candidate's manual profile skills, active resume extraction, and published job market data.
    """
    # 1. Ensure expired opportunities are transitioned before matching
    await expire_overdue_opportunities(db)

    # 2. Fetch authenticated candidate profile with relationships
    prof_stmt = (
        select(Profile)
        .options(
            selectinload(Profile.career_preferences),
            selectinload(Profile.skills).selectinload(ProfileSkill.skill).selectinload(Skill.category),
            selectinload(Profile.resumes),
        )
        .where(Profile.id == profile_id)
    )
    prof_res = await db.execute(prof_stmt)
    profile = prof_res.scalar_one_or_none()

    if not profile:
        raise ValueError("Profile not found")

    # 3. Extract Candidate's Acquired Skills (Manual Profile & Active Resume)
    acquired_skills_dict: dict[str, AcquiredSkillItem] = {}

    # Manual Profile Skills
    for ps in profile.skills:
        skill_id = ps.skill_id
        if ps.skill:
            name = ps.skill.name
            category = ps.skill.category.name if ps.skill.category else None
        else:
            name = ps.custom_skill_name or "Custom Skill"
            category = None

        norm_key = normalize_text(name)
        acquired_skills_dict[norm_key] = AcquiredSkillItem(
            skill_id=skill_id,
            name=name,
            source=SkillSource.PROFILE,
            proficiency=ps.proficiency,
            resume_evidence=None,
            is_saved_to_profile=True,
            category=category,
        )

    # Active Resume Extracted Skills
    active_resume = next((r for r in profile.resumes if r.is_active), None)
    if active_resume and active_resume.has_structured_data:
        resume_skills_raw = active_resume.structured_data.get("skills", [])
        for rs in resume_skills_raw:
            rs_name = rs.get("name")
            if not rs_name:
                continue
            norm_key = normalize_text(rs_name)
            evidence = rs.get("evidence")
            rs_skill_id = rs.get("skill_id")
            try:
                parsed_rs_id = UUID(str(rs_skill_id)) if rs_skill_id else None
            except (ValueError, TypeError):
                parsed_rs_id = None

            if norm_key in acquired_skills_dict:
                # Present in both manual profile and resume
                item = acquired_skills_dict[norm_key]
                item.source = SkillSource.BOTH
                item.resume_evidence = evidence
                if not item.skill_id and parsed_rs_id:
                    item.skill_id = parsed_rs_id
            else:
                # Present only in active resume
                acquired_skills_dict[norm_key] = AcquiredSkillItem(
                    skill_id=parsed_rs_id,
                    name=rs_name,
                    source=SkillSource.RESUME,
                    proficiency=None,
                    resume_evidence=evidence,
                    is_saved_to_profile=False,
                    category=None,
                )

    candidate_acquired_list = sorted(acquired_skills_dict.values(), key=lambda x: x.name.lower())
    candidate_skill_norms: set[str] = set(acquired_skills_dict.keys())
    candidate_skill_ids: set[UUID] = {
        item.skill_id for item in acquired_skills_dict.values() if item.skill_id is not None
    }

    # 4. Analyze Preferences & Determine Target Role Scope
    prefs = profile.career_preferences
    desired_roles = [r.strip() for r in (prefs.desired_roles or []) if r and r.strip()] if prefs else []
    preferred_domains = [d.strip() for d in (prefs.preferred_domains or []) if d and d.strip()] if prefs else []

    selected_role: str | None = None
    if target_role and target_role.strip():
        selected_role = target_role.strip()
    elif desired_roles:
        selected_role = desired_roles[0]

    has_insufficient_profile = False
    profile_message: str | None = None

    if not desired_roles and not preferred_domains and not selected_role:
        has_insufficient_profile = True
        profile_message = (
            "Your profile has no desired roles or career preferences configured. "
            "Skill demand is being analyzed across all published opportunities. "
            "Add desired roles to your profile for tailored recommendations."
        )

    # 5. Load Published Opportunities with Skills and Categories
    opp_stmt = (
        select(Opportunity)
        .options(
            selectinload(Opportunity.skills)
            .selectinload(OpportunitySkill.skill)
            .selectinload(Skill.category)
        )
        .where(Opportunity.status == "Published")
    )
    opp_res = await db.execute(opp_stmt)
    all_published_opps = opp_res.scalars().all()

    # 6. Filter Published Opportunities for Relevance
    model_available = is_model_available()
    relevant_opps: list[Opportunity] = []

    if selected_role:
        for opp in all_published_opps:
            if await role_matches_opportunity(selected_role, opp, model_available):
                relevant_opps.append(opp)
    elif desired_roles or preferred_domains:
        for opp in all_published_opps:
            matched = False
            for dr in desired_roles:
                if await role_matches_opportunity(dr, opp, model_available):
                    matched = True
                    break
            if not matched and preferred_domains and opp.domain:
                norm_domain = normalize_text(opp.domain)
                for pd in preferred_domains:
                    if normalize_text(pd) in norm_domain:
                        matched = True
                        break
            if matched:
                relevant_opps.append(opp)
    else:
        # Fallback to all published opportunities
        relevant_opps = list(all_published_opps)

    total_relevant = len(relevant_opps)
    has_insufficient_jobs = False
    jobs_message: str | None = None

    if total_relevant == 0:
        has_insufficient_jobs = True
        role_desc = f" '{selected_role}'" if selected_role else ""
        jobs_message = (
            f"No published opportunities currently match the role{role_desc}. "
            "CareerPilot AI does not fabricate skill recommendations without active job postings."
        )

        return SkillGapRoadmapResponse(
            target_role=selected_role,
            available_target_roles=desired_roles,
            total_analyzed_opportunities=0,
            coverage=SkillCoverageSummary(
                total_market_skills=0,
                acquired_skills_count=0,
                missing_skills_count=0,
                coverage_percentage=0.0,
            ),
            data_status=InsufficientDataStatus(
                has_insufficient_profile=has_insufficient_profile,
                profile_message=profile_message,
                has_insufficient_jobs=has_insufficient_jobs,
                jobs_message=jobs_message,
            ),
            acquired_skills=candidate_acquired_list,
            missing_skills=[],
            learning_sequence=[],
        )

    # 7. Collect Market Skills and Distinguish Required vs Desired
    # Key: normalized skill name
    market_skill_stats: dict[str, dict[str, Any]] = {}

    for opp in relevant_opps:
        req_text, desired_text = partition_job_description(opp.description)

        for os in opp.skills:
            if not os.skill:
                continue

            skill = os.skill
            norm_name = normalize_text(skill.name)

            # Determine whether this skill in this opportunity is Required or Desired
            is_desired = False
            if desired_text and is_skill_in_text(skill.name, desired_text):
                # If it's explicitly in desired text and NOT in required text
                if not req_text or not is_skill_in_text(skill.name, req_text):
                    is_desired = True

            is_required = not is_desired

            if norm_name not in market_skill_stats:
                market_skill_stats[norm_name] = {
                    "skill_id": skill.id,
                    "name": skill.name,
                    "category": skill.category.name if skill.category else None,
                    "required_count": 0,
                    "desired_count": 0,
                    "evidence_jobs": [],
                }

            entry = market_skill_stats[norm_name]
            if is_required:
                entry["required_count"] += 1
            else:
                entry["desired_count"] += 1

            # Keep up to 6 distinct job evidence items
            if len(entry["evidence_jobs"]) < 6:
                entry["evidence_jobs"].append(
                    JobEvidenceItem(
                        opportunity_id=opp.id,
                        title=opp.title,
                        company_name=opp.company_name,
                        is_required=is_required,
                    )
                )

    total_market_skills_count = len(market_skill_stats)

    # Check if candidate has each market skill
    matched_market_skills_count = 0
    missing_skills: list[MissingSkillItem] = []

    for norm_name, stats in market_skill_stats.items():
        is_candidate_has = (
            norm_name in candidate_skill_norms
            or (stats["skill_id"] and stats["skill_id"] in candidate_skill_ids)
        )

        if is_candidate_has:
            matched_market_skills_count += 1
        else:
            req_count = stats["required_count"]
            des_count = stats["desired_count"]
            total_freq = req_count + des_count
            pct = round((total_freq / total_relevant) * 100, 1)

            # Requirement Level
            if req_count > 0 and des_count == 0:
                req_level = RequirementLevel.REQUIRED
            elif des_count > 0 and req_count == 0:
                req_level = RequirementLevel.DESIRED
            else:
                req_level = RequirementLevel.COMMON

            # Priority Tier determination:
            # - High: High-frequency required skill (>= 50% of matching jobs or required in >= 2 postings)
            # - Medium: Core required skill (required in at least 1 job, or widely desired in >= 2 jobs with >= 50% demand)
            # - Low: Purely preferred/desired skills or low-frequency supplementary requirements
            if (pct >= 50.0 and req_count > 0) or (req_count >= 2 and pct >= 40.0):
                tier = PriorityTier.HIGH
            elif req_count >= 1:
                tier = PriorityTier.MEDIUM
            elif des_count >= 2 and pct >= 50.0:
                tier = PriorityTier.MEDIUM
            else:
                tier = PriorityTier.LOW

            # Plain-English Rationale
            opp_names = [e.company_name for e in stats["evidence_jobs"][:2]]
            opp_summary = f" (e.g., {', '.join(opp_names)})" if opp_names else ""

            if tier == PriorityTier.HIGH:
                rationale = (
                    f"High-Demand Core Requirement: Required in {req_count} of {total_relevant} "
                    f"({pct}%) published opportunities for this role{opp_summary}. "
                    "Mastering this skill yields the greatest immediate improvement in qualification."
                )
            elif tier == PriorityTier.MEDIUM:
                rationale = (
                    f"Active Job Requirement: Observed in {total_freq} of {total_relevant} "
                    f"({pct}%) postings{opp_summary}. Expected for day-to-day role responsibilities."
                )
            else:
                status_str = "preferred qualification" if req_level == RequirementLevel.DESIRED else "supplementary skill"
                rationale = (
                    f"Differentiating Skill: Listed as a {status_str} in {total_freq} "
                    f"opportunity{opp_summary}. Enhances your profile once core requirements are fulfilled."
                )

            missing_skills.append(
                MissingSkillItem(
                    skill_id=stats["skill_id"],
                    name=stats["name"],
                    priority_tier=tier,
                    demand_frequency=total_freq,
                    demand_percentage=pct,
                    requirement_level=req_level,
                    required_count=req_count,
                    desired_count=des_count,
                    evidence_jobs=stats["evidence_jobs"],
                    rationale=rationale,
                    category=stats["category"],
                )
            )

    # 8. Deterministic Sort of Missing Skills
    tier_order = {PriorityTier.HIGH: 0, PriorityTier.MEDIUM: 1, PriorityTier.LOW: 2}
    missing_skills.sort(
        key=lambda s: (
            tier_order[s.priority_tier],
            -s.required_count,
            -s.demand_frequency,
            s.name.lower(),
        )
    )

    # 9. Practical Learning Sequence Stages
    high_skills = [s for s in missing_skills if s.priority_tier == PriorityTier.HIGH]
    med_skills = [s for s in missing_skills if s.priority_tier == PriorityTier.MEDIUM]
    low_skills = [s for s in missing_skills if s.priority_tier == PriorityTier.LOW]

    stages: list[LearningSequenceStage] = []
    stage_idx = 1

    if high_skills:
        stages.append(
            LearningSequenceStage(
                stage_number=stage_idx,
                title="Stage 1: High-Impact Essentials",
                description=(
                    "Start here. These core skills have the highest mandatory requirement rate "
                    f"across published {selected_role or 'opportunity'} listings. Completing these unlocks "
                    "baseline eligibility for the majority of positions."
                ),
                skills=high_skills,
            )
        )
        stage_idx += 1

    if med_skills:
        stages.append(
            LearningSequenceStage(
                stage_number=stage_idx,
                title=f"Stage {stage_idx}: Core Role Competencies",
                description=(
                    "Expand your technical scope. Frequently required or standard technical expectations "
                    "for this role that round out your day-to-day readiness."
                ),
                skills=med_skills,
            )
        )
        stage_idx += 1

    if low_skills:
        stages.append(
            LearningSequenceStage(
                stage_number=stage_idx,
                title=f"Stage {stage_idx}: Differentiators & Desired Qualifications",
                description=(
                    "Differentiate your application. Nice-to-have or specialized skills that make "
                    "your profile stand out once core qualifications are satisfied."
                ),
                skills=low_skills,
            )
        )

    # 10. Coverage Metric
    if total_market_skills_count > 0:
        coverage_pct = round((matched_market_skills_count / total_market_skills_count) * 100, 1)
    else:
        coverage_pct = 0.0

    coverage_summary = SkillCoverageSummary(
        total_market_skills=total_market_skills_count,
        acquired_skills_count=matched_market_skills_count,
        missing_skills_count=len(missing_skills),
        coverage_percentage=coverage_pct,
        disclaimer=(
            "This metric measures observed skill overlap with published job listings. "
            "It is a heuristic readiness indicator and does not represent a probability of hiring or selection."
        ),
    )

    # If there are relevant opportunities but none have skills attached
    if total_relevant > 0 and total_market_skills_count == 0:
        has_insufficient_jobs = True
        jobs_message = (
            f"Matching opportunities ({total_relevant}) for '{selected_role or 'your preferences'}' "
            "currently have no specific skills declared by employers."
        )

    data_status = InsufficientDataStatus(
        has_insufficient_profile=has_insufficient_profile,
        profile_message=profile_message,
        has_insufficient_jobs=has_insufficient_jobs,
        jobs_message=jobs_message,
    )

    return SkillGapRoadmapResponse(
        target_role=selected_role,
        available_target_roles=desired_roles,
        total_analyzed_opportunities=total_relevant,
        coverage=coverage_summary,
        data_status=data_status,
        acquired_skills=candidate_acquired_list,
        missing_skills=missing_skills,
        learning_sequence=stages,
    )
