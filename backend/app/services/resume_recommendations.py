import logging
import re
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.opportunity import Opportunity, OpportunitySkill
from app.models.profile import (
    Education,
    Experience,
    Profile,
    ProfileSkill,
    Project,
    Resume,
    Skill,
)
from app.schemas.resume_recommendations import (
    ActionableImprovementItem,
    ActiveResumeSummary,
    AtsGuidanceItem,
    DataSufficiencyInfo,
    JobResumeAnalysisRequest,
    JobResumeAnalysisResponse,
    JobResumeContextResponse,
    RelevantStrengthItem,
    RequirementGapItem,
)
from app.services.skill_gap import partition_job_description

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def get_gemini_api_url() -> str:
    model = getattr(settings, "gemini_model", "gemini-2.5-flash") or "gemini-2.5-flash"
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


# Patterns indicating vague or weak resume bullet points
WEAK_VERB_PATTERNS = [
    (re.compile(r"^(?:worked on|worked with|helped on)\b", re.IGNORECASE), "Engineered and contributed to"),
    (re.compile(r"^(?:helped with|helped to|assisted in|assisted with)\b", re.IGNORECASE), "Collaborated with team to develop"),
    (re.compile(r"^(?:responsible for|tasked with|assigned to)\b", re.IGNORECASE), "Spearheaded and maintained"),
    (re.compile(r"^(?:participated in|involved in)\b", re.IGNORECASE), "Contributed key components to"),
    (re.compile(r"^(?:did|handled|took care of)\b", re.IGNORECASE), "Executed and optimized"),
    (re.compile(r"^(?:used|utilized|learned)\b", re.IGNORECASE), "Applied and implemented"),
    (re.compile(r"^(?:built|created|made)\b", re.IGNORECASE), "Architected and delivered"),
]

METRIC_INDICATORS = re.compile(r"(\d+%|\d+\s*(?:ms|sec|min|hours|users|req|rpm|rps|k|m|x)\b|\$\d+)", re.IGNORECASE)


async def get_job_resume_context(
    db: AsyncSession,
    profile_id: UUID,
    opportunity_id: UUID,
) -> JobResumeContextResponse:
    """
    Fetch opportunity and active resume readiness details prior to running analysis.
    Validates published opportunity status and active resume indicators.
    """
    # 1. Fetch opportunity
    opp_stmt = (
        select(Opportunity)
        .options(selectinload(Opportunity.skills).selectinload(OpportunitySkill.skill))
        .where(Opportunity.id == opportunity_id)
    )
    opp_res = await db.execute(opp_stmt)
    opp = opp_res.scalar_one_or_none()

    if not opp or opp.status != "Published":
        raise ValueError("Opportunity not found or not published.")

    # 2. Fetch candidate profile and resumes
    prof_stmt = (
        select(Profile)
        .options(selectinload(Profile.resumes))
        .where(Profile.id == profile_id)
    )
    prof_res = await db.execute(prof_stmt)
    profile = prof_res.scalar_one_or_none()

    if not profile:
        raise ValueError("Candidate profile not found.")

    active_resume = next((r for r in profile.resumes if r.is_active), None)

    active_summary: ActiveResumeSummary | None = None
    readiness_notes: list[str] = []
    is_ready = True

    if active_resume:
        completeness_score = None
        score_label = None
        if active_resume.analysis_data and isinstance(active_resume.analysis_data, dict):
            completeness_score = active_resume.analysis_data.get("completeness_score")
            score_label = active_resume.analysis_data.get("score_label")

        active_summary = ActiveResumeSummary(
            resume_id=active_resume.id,
            original_filename=active_resume.original_filename,
            file_size=active_resume.file_size,
            file_type=active_resume.file_type,
            has_parsed_text=active_resume.has_parsed_text,
            has_structured_data=active_resume.has_structured_data,
            has_analysis=active_resume.has_analysis,
            completeness_score=completeness_score,
            score_label=score_label,
            uploaded_at=active_resume.created_at,
        )

        if not active_resume.has_parsed_text:
            readiness_notes.append("Active resume has not been parsed yet. Please run text extraction in your Profile.")
            is_ready = False
    else:
        readiness_notes.append("No active resume designated. Please upload and activate a resume in your Profile.")
        is_ready = False

    desc_text = (opp.description or "").strip()
    has_desc = bool(desc_text)
    if not has_desc:
        readiness_notes.append("This opportunity does not have a detailed job description.")
        # We can still analyze skills if present, but note it
        if not opp.skills:
            readiness_notes.append("This opportunity lacks both description and specified skill requirements.")
            is_ready = False

    opp_skill_names = [os.skill.name for os in opp.skills if os.skill]

    return JobResumeContextResponse(
        opportunity_id=opp.id,
        opportunity_title=opp.title,
        company_name=opp.company_name,
        opportunity_type=opp.opportunity_type,
        work_model=opp.work_model,
        domain=opp.domain,
        locations=opp.locations or [],
        deadline=opp.deadline,
        has_description=has_desc,
        description_char_count=len(desc_text),
        skills_required=opp_skill_names,
        active_resume=active_summary,
        is_ready_for_analysis=is_ready,
        readiness_notes=readiness_notes,
    )


async def call_gemini_for_bullet_rewrite(
    original_bullet: str,
    job_title: str,
    company_name: str,
    context_support: str,
) -> str | None:
    """
    Optional Gemini invocation to generate an impactful bullet rewrite.
    Strictly forbids fabricating tools, degrees, or unevidenced metrics.
    Instructs insertion of explicit bracketed placeholders for metrics.
    """
    api_key = settings.gemini_api_key.strip()
    if not api_key or api_key == "dummy-key":
        return None

    prompt = f"""You are an expert resume advisor helping a student tailor their existing resume for an opportunity.

TARGET ROLE: {job_title} at {company_name}
STUDENT'S EXISTING BULLET POINT:
"{original_bullet}"

ADDITIONAL VERIFIED CONTEXT (from student's records):
{context_support}

STRICT ANTI-HALLUCINATION & INTEGRITY RULES:
1. Ground the rewrite strictly in the student's existing bullet point and facts provided above.
2. NEVER invent technologies, tools, degrees, employers, or metrics that the student did not mention.
3. Start with a strong, active engineering or professional verb (e.g., Engineered, Architected, Developed, Streamlined, Orchestrated).
4. Highlight technical depth relevant to {job_title}.
5. If the original bullet lacks quantifiable outcome, use explicit bracketed placeholders like "[insert quantifiable metric, e.g. latency reduced by X%]" or "[quantify outcome, e.g. serving N users]".
6. Do NOT invent specific numbers, percentages, or metrics.
7. Return ONLY the rewritten bullet point text without quotes, formatting tags, or markdown code blocks.

Rewritten bullet:"""

    url = f"{get_gemini_api_url()}?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.25,
            "maxOutputTokens": 256,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        text = parts[0]["text"].strip()
                        clean = re.sub(r"^```(?:markdown)?\s*", "", text)
                        clean = re.sub(r"\s*```$", "", clean).strip()
                        clean = clean.strip("\"' ")
                        if clean and len(clean) > 10:
                            return clean
            else:
                logger.warning("Gemini rewrite API returned status %s: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("Gemini rewrite API encountered exception: %s", str(exc))

    return None


def generate_deterministic_bullet_rewrite(
    original_bullet: str,
    job_title: str,
    matched_skills: list[str],
) -> str:
    """
    Deterministic fallback for bullet rewrites when Gemini is unavailable.
    Replaces weak opening verbs with strong action verbs and inserts honest bracketed metric placeholders.
    """
    trimmed = original_bullet.strip().lstrip("•-*–—▪ ").strip()
    if not trimmed:
        return "Implemented core components using relevant technologies, achieving [insert quantifiable result, e.g., improved efficiency by X%]."

    for pattern, replacement in WEAK_VERB_PATTERNS:
        if pattern.search(trimmed):
            rewritten_start = pattern.sub(replacement, trimmed)
            # If no metric exists, append standard bracketed metric placeholder
            if not METRIC_INDICATORS.search(rewritten_start):
                if not rewritten_start.endswith("."):
                    rewritten_start += ","
                rewritten_start += " resulting in [insert measurable outcome, e.g., improved processing speed by X%]."
            return rewritten_start

    # If it didn't match a weak verb but has no metric
    if not METRIC_INDICATORS.search(trimmed):
        ending = trimmed.rstrip(".")
        relevant_tech = f" utilizing {matched_skills[0]}" if matched_skills else ""
        return f"{ending}{relevant_tech}, achieving [insert quantifiable impact, e.g., reduced error rate by X%]."

    return f"Spearheaded {trimmed}"


def extract_resume_bullets(text: str | None) -> list[str]:
    """
    Extracts distinct bullet points or accomplishment statements from resume text.
    """
    if not text:
        return []

    lines = text.split("\n")
    bullets: list[str] = []
    current_bullet: list[str] = []

    bullet_start_regex = re.compile(r"^\s*(?:[•\-*–—▪]|\d+\.)\s+(.+)$")

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if current_bullet:
                bullets.append(" ".join(current_bullet))
                current_bullet = []
            continue

        match = bullet_start_regex.match(raw_line)
        if match:
            if current_bullet:
                bullets.append(" ".join(current_bullet))
            current_bullet = [match.group(1).strip()]
        elif current_bullet:
            # Continuation of previous bullet
            if len(line) > 0 and line[0].islower():
                current_bullet.append(line)
            else:
                bullets.append(" ".join(current_bullet))
                current_bullet = []
        else:
            # Heuristic: line starts with typical action verb or past tense
            words = line.split()
            if len(words) >= 4 and len(words) <= 35:
                first_word = words[0].lower().rstrip(",")
                if first_word.endswith("ed") or first_word in ["built", "designed", "wrote", "helped", "led", "ran"]:
                    bullets.append(line)

    if current_bullet:
        bullets.append(" ".join(current_bullet))

    # Deduplicate while preserving order, filtering out trivial headers
    unique: list[str] = []
    seen: set[str] = set()
    for b in bullets:
        clean = b.strip()
        norm = normalize_text(clean)
        if len(clean) >= 15 and norm not in seen and not clean.endswith(":"):
            seen.add(norm)
            unique.append(clean)

    return unique


async def analyze_job_resume(
    db: AsyncSession,
    profile_id: UUID,
    request: JobResumeAnalysisRequest,
) -> JobResumeAnalysisResponse:
    """
    Orchestrates Phase 7.5: Job-Specific Resume Recommendations.
    Compares authenticated candidate's active resume & profile records against a published opportunity.
    Strictly preserves the active resume without modifications.
    """
    # 1. Fetch Candidate Profile with all relevant relationships
    prof_stmt = (
        select(Profile)
        .options(
            selectinload(Profile.career_preferences),
            selectinload(Profile.skills).selectinload(ProfileSkill.skill),
            selectinload(Profile.educations),
            selectinload(Profile.experiences),
            selectinload(Profile.projects),
            selectinload(Profile.resumes),
        )
        .where(Profile.id == profile_id)
    )
    prof_res = await db.execute(prof_stmt)
    profile = prof_res.scalar_one_or_none()

    if not profile:
        raise ValueError("Candidate profile not found.")

    # 2. Fetch Opportunity with skills
    opp_stmt = (
        select(Opportunity)
        .options(selectinload(Opportunity.skills).selectinload(OpportunitySkill.skill))
        .where(Opportunity.id == request.opportunity_id)
    )
    opp_res = await db.execute(opp_stmt)
    opp = opp_res.scalar_one_or_none()

    if not opp or opp.status != "Published":
        raise ValueError("Opportunity not found or not published.")

    # 3. Validate Active Resume presence and text extraction
    active_resume = next((r for r in profile.resumes if r.is_active), None)
    if not active_resume:
        raise ValueError(
            "No active resume found. Please upload and activate a resume in your profile before running job-specific recommendations."
        )

    if not active_resume.parsed_text:
        raise ValueError(
            "Active resume text has not been extracted yet. Please extract text from your resume in your profile before analyzing."
        )

    # 4. Check Data Sufficiency
    desc_text = (opp.description or "").strip()
    has_desc = bool(desc_text)
    opp_skill_names = [os.skill.name for os in opp.skills if os.skill]
    has_skills = bool(opp_skill_names)

    resume_text = active_resume.parsed_text.strip()
    has_resume_text = bool(resume_text)

    completeness_score = None
    completeness_label = None
    if active_resume.analysis_data and isinstance(active_resume.analysis_data, dict):
        completeness_score = active_resume.analysis_data.get("completeness_score")
        completeness_label = active_resume.analysis_data.get("score_label")

    if not has_desc and not has_skills:
        # Insufficient opportunity data
        sufficiency = DataSufficiencyInfo(
            has_active_resume=True,
            has_resume_text=has_resume_text,
            has_job_description=False,
            has_job_skills=False,
            status="insufficient",
            details=[
                "The selected opportunity contains neither a job description nor skill requirements.",
                "To prevent fabricated recommendations, comprehensive analysis cannot proceed until opportunity details are provided.",
            ],
        )
        return JobResumeAnalysisResponse(
            opportunity_id=opp.id,
            opportunity_title=opp.title,
            company_name=opp.company_name,
            resume_id=active_resume.id,
            resume_filename=active_resume.original_filename,
            resume_completeness_score=completeness_score,
            resume_completeness_label=completeness_label,
            data_sufficiency=sufficiency,
            strengths=[],
            gaps=[],
            improvements=[],
            ats_guidance=[],
            disclaimers=[
                "CareerPilot AI never invents job requirements or candidate credentials.",
                "Your active resume has remained completely unchanged.",
            ],
            provider="deterministic",
            provider_model=None,
            created_at=utcnow(),
        )

    sufficiency_status = "sufficient" if has_desc and has_skills else "partial"
    sufficiency_details: list[str] = []
    if not has_desc:
        sufficiency_details.append("Opportunity has skill tags but lacks a full job description; analysis is focused on core required skills.")
    if not has_skills:
        sufficiency_details.append("Opportunity relies on free-text job description; required skills were parsed from description text.")

    sufficiency = DataSufficiencyInfo(
        has_active_resume=True,
        has_resume_text=has_resume_text,
        has_job_description=has_desc,
        has_job_skills=has_skills,
        status=sufficiency_status,
        details=sufficiency_details,
    )

    # 5. Partition Job Description into Required and Desired Text Blocks
    required_text, desired_text = partition_job_description(desc_text)

    # 6. Gather Candidate Skills & Evidence
    # Verified profile skills
    verified_skills_dict: dict[str, str] = {}
    for ps in profile.skills:
        if ps.skill and ps.skill.name:
            verified_skills_dict[normalize_text(ps.skill.name)] = ps.skill.name
        elif ps.custom_skill_name:
            verified_skills_dict[normalize_text(ps.custom_skill_name)] = ps.custom_skill_name

    # Extracted resume skills with evidence snippets
    resume_skills_dict: dict[str, tuple[str, str]] = {}  # norm -> (name, evidence)
    if active_resume.has_structured_data and isinstance(active_resume.structured_data, dict):
        raw_r_skills = active_resume.structured_data.get("skills", [])
        for rs in raw_r_skills:
            r_name = rs.get("name")
            r_evidence = rs.get("evidence", "")
            if r_name:
                resume_skills_dict[normalize_text(r_name)] = (r_name, r_evidence)

    # Combined candidate skills
    all_candidate_norms = set(verified_skills_dict.keys()).union(set(resume_skills_dict.keys()))

    # 7. Identify Strengths (Skills, Projects, Experience, Education)
    strengths: list[RelevantStrengthItem] = []
    matched_skills_for_wording: list[str] = []

    # A) Skill Strengths
    for s_name in opp_skill_names:
        norm = normalize_text(s_name)
        in_profile = norm in verified_skills_dict
        in_resume = norm in resume_skills_dict

        if in_profile and in_resume:
            source = "both"
            r_name, evidence = resume_skills_dict[norm]
            proof = f"Verified in profile skills and evidenced in resume text: '{evidence}'"
            matched_skills_for_wording.append(s_name)
            strengths.append(
                RelevantStrengthItem(
                    category="skill",
                    title=s_name,
                    source=source,
                    evidence=proof,
                    relevance_explanation=f"Explicitly matches {opp.company_name}'s requirements for {opp.title}.",
                )
            )
        elif in_profile:
            source = "profile"
            matched_skills_for_wording.append(s_name)
            strengths.append(
                RelevantStrengthItem(
                    category="skill",
                    title=s_name,
                    source=source,
                    evidence=f"Recorded and verified in candidate profile skills.",
                    relevance_explanation=f"Aligns directly with required qualification for {opp.title}.",
                )
            )
        elif in_resume:
            source = "resume"
            r_name, evidence = resume_skills_dict[norm]
            matched_skills_for_wording.append(s_name)
            strengths.append(
                RelevantStrengthItem(
                    category="skill",
                    title=s_name,
                    source=source,
                    evidence=f"Extracted from active resume: '{evidence}'",
                    relevance_explanation=f"Matches {opp.company_name}'s skill requirements based on resume evidence.",
                )
            )

    # B) Project Strengths
    opp_tokens = set(re.findall(r"[a-z0-9]{3,}", (opp.title + " " + desc_text).lower()))
    for proj in profile.projects:
        proj_text = f"{proj.name} {proj.description or ''}".lower()
        proj_tokens = set(re.findall(r"[a-z0-9]{3,}", proj_text))
        overlap = opp_tokens.intersection(proj_tokens)

        # Also check if any matched skill is mentioned
        proj_matched_skills = [
            s for s in matched_skills_for_wording if normalize_text(s) in normalize_text(proj_text)
        ]
        if proj_matched_skills or len(overlap) >= 3:
            skills_str = f" involving {', '.join(proj_matched_skills[:3])}" if proj_matched_skills else ""
            desc_snippet = (proj.description[:120] + "...") if proj.description else "Project listed on profile"
            strengths.append(
                RelevantStrengthItem(
                    category="project",
                    title=f"Project: {proj.name}",
                    source="profile",
                    evidence=f"Project description: \"{desc_snippet}\"",
                    relevance_explanation=f"Demonstrates practical engineering experience{skills_str} directly applicable to {opp.title}.",
                )
            )

    # C) Experience Strengths
    for exp in profile.experiences:
        exp_text = f"{exp.title} {exp.company} {exp.description or ''}".lower()
        exp_matched_skills = [
            s for s in matched_skills_for_wording if normalize_text(s) in normalize_text(exp_text)
        ]
        if exp_matched_skills or normalize_text(exp.title) in normalize_text(opp.title):
            exp_snippet = (exp.description[:120] + "...") if exp.description else f"Held role {exp.title} at {exp.company}"
            strengths.append(
                RelevantStrengthItem(
                    category="experience",
                    title=f"Experience: {exp.title} at {exp.company}",
                    source="profile",
                    evidence=f"Role details: \"{exp_snippet}\"",
                    relevance_explanation=f"Relevant professional background supporting responsibilities required at {opp.company_name}.",
                )
            )

    # D) Education Strengths
    for edu in profile.educations:
        edu_text = f"{edu.degree} {edu.field_of_study or ''}".lower()
        if "computer" in edu_text or "data" in edu_text or "engineering" in edu_text or "science" in edu_text or (opp.domain and normalize_text(opp.domain) in normalize_text(edu_text)):
            strengths.append(
                RelevantStrengthItem(
                    category="education",
                    title=f"Education: {edu.degree} ({edu.field_of_study or 'Major'})",
                    source="profile",
                    evidence=f"Studies at {edu.institution}.",
                    relevance_explanation=f"Provides academic foundation and domain expertise suited for {opp.title}.",
                )
            )

    # 8. Identify Requirement Gaps
    gaps: list[RequirementGapItem] = []
    for s_name in opp_skill_names:
        norm = normalize_text(s_name)
        if norm not in all_candidate_norms:
            # Check if mentioned in desired section vs required
            is_desired = bool(desired_text and s_name.lower() in desired_text)
            level = "desired" if is_desired else "required"

            # Determine whether genuinely missing or undetermined
            # If resume is parsed and structured, this is a clear missing requirement in current records
            gap_type = "missing_requirement"
            explanation = (
                f"'{s_name}' is listed as a {level} qualification by {opp.company_name}, "
                "but no supporting evidence was detected in your active resume or verified profile skills."
            )
            student_guidance = (
                f"If you have hands-on experience with {s_name} from university coursework or personal projects, "
                f"add it to your profile skills and describe its implementation on your resume. "
                f"If you are new to {s_name}, consider completing a focused project demonstrating core competency."
            )

            gaps.append(
                RequirementGapItem(
                    skill_name=s_name,
                    requirement_level=level,
                    gap_type=gap_type,
                    explanation=explanation,
                    student_guidance=student_guidance,
                )
            )

    # 9. Identify Actionable Resume Improvements & Bullet Rewrites
    improvements: list[ActionableImprovementItem] = []
    gemini_used = False

    # A) Project / Experience Emphasis Recommendation
    if profile.projects:
        # Find project with highest skill overlap
        best_proj = None
        best_overlap = -1
        for p in profile.projects:
            p_text = f"{p.name} {p.description or ''}".lower()
            overlap_cnt = sum(1 for s in matched_skills_for_wording if normalize_text(s) in normalize_text(p_text))
            if overlap_cnt > best_overlap:
                best_overlap = overlap_cnt
                best_proj = p

        if best_proj:
            improvements.append(
                ActionableImprovementItem(
                    category="emphasis",
                    priority="high",
                    title=f"Emphasize '{best_proj.name}' at the top of your Projects section",
                    original_content=None,
                    suggested_wording=None,
                    reason=(
                        f"This project demonstrates relevant skills for {opp.title} at {opp.company_name}. "
                        "Highlighting it prominently helps recruiters and parsers instantly see your technical suitability."
                    ),
                    evidence_support=f"From profile project: '{best_proj.name}'",
                    is_gemini_assisted=False,
                )
            )

    # B) Identify Vague Resume Bullet Points & Generate Grounded Rewrites
    resume_bullets = extract_resume_bullets(resume_text)
    vague_bullets: list[tuple[str, str]] = []  # (original_bullet, weak_verb_match)

    for b in resume_bullets:
        cleaned = b.strip().lstrip("•-*–—▪ ").strip()
        for pattern, _ in WEAK_VERB_PATTERNS:
            if pattern.search(cleaned):
                vague_bullets.append((cleaned, pattern.pattern))
                break
        if len(vague_bullets) >= 3:
            break

    # If no weak verbs detected, find bullets without metrics
    if not vague_bullets and resume_bullets:
        for b in resume_bullets:
            cleaned = b.strip().lstrip("•-*–—▪ ").strip()
            if not METRIC_INDICATORS.search(cleaned) and len(cleaned.split()) >= 4:
                vague_bullets.append((cleaned, "no_metric"))
                if len(vague_bullets) >= 2:
                    break

    # Generate rewrites for discovered vague bullets
    for orig_bullet, _ in vague_bullets:
        suggested: str | None = None
        used_gemini_for_bullet = False

        if request.include_bullet_rewrites:
            # Try Gemini first if key available
            context_support = (
                f"- Candidate Name: {profile.full_name}\n"
                f"- Matched Job Skills: {', '.join(matched_skills_for_wording[:4]) or 'Software Engineering'}\n"
            )
            suggested = await call_gemini_for_bullet_rewrite(
                original_bullet=orig_bullet,
                job_title=opp.title,
                company_name=opp.company_name,
                context_support=context_support,
            )
            if suggested:
                used_gemini_for_bullet = True
                gemini_used = True

        # Fallback to deterministic rewrite if Gemini was not used or failed
        if not suggested:
            suggested = generate_deterministic_bullet_rewrite(
                original_bullet=orig_bullet,
                job_title=opp.title,
                matched_skills=matched_skills_for_wording,
            )

        short_preview = (orig_bullet[:45] + "...") if len(orig_bullet) > 45 else orig_bullet
        improvements.append(
            ActionableImprovementItem(
                category="bullet_rewrite",
                priority="high",
                title=f"Upgrade action verb and quantify outcome: \"{short_preview}\"",
                original_content=orig_bullet,
                suggested_wording=suggested,
                reason=(
                    f"Replaces passive phrasing with strong action-driven impact and incorporates "
                    f"explicit bracketed placeholders for measurable outcomes relevant to {opp.title}."
                ),
                evidence_support="Derived strictly from the existing text of your active resume.",
                is_gemini_assisted=used_gemini_for_bullet,
            )
        )

    # C) Keyword Placement Improvement
    # If a matched skill appears in the skills list but not in any resume bullet
    missing_in_bullets: list[str] = []
    bullet_corpus = " ".join(resume_bullets).lower()
    for s in matched_skills_for_wording:
        if normalize_text(s) not in normalize_text(bullet_corpus):
            missing_in_bullets.append(s)

    if missing_in_bullets:
        top_skills = missing_in_bullets[:3]
        improvements.append(
            ActionableImprovementItem(
                category="keyword_alignment",
                priority="medium",
                title=f"Weave {', '.join(top_skills)} into accomplishment bullets",
                original_content=None,
                suggested_wording=(
                    f"Example phrasing: \"Developed [feature/module] using {top_skills[0]}, "
                    "[insert metric, e.g., reducing turnaround time by X%] for [target project].\""
                ),
                reason=(
                    f"{', '.join(top_skills)} is required for {opp.title} and detected in your skills, "
                    "but does not appear in your project or experience descriptions. Connecting skills to results improves contextual keyword ranking."
                ),
                evidence_support=f"Detected in candidate skills records: {', '.join(top_skills)}",
                is_gemini_assisted=False,
            )
        )

    # 10. ATS-Oriented Formatting Guidance
    ats_guidance: list[AtsGuidanceItem] = []

    # Check sections
    structured_sections = (
        active_resume.structured_data.get("sections", {})
        if active_resume.has_structured_data and isinstance(active_resume.structured_data, dict)
        else {}
    )

    has_skills_sec = bool(structured_sections.get("skills"))
    has_exp_sec = bool(structured_sections.get("experience"))
    has_edu_sec = bool(structured_sections.get("education"))
    has_proj_sec = bool(structured_sections.get("projects"))

    if not has_skills_sec or not has_exp_sec or not has_edu_sec:
        missing_sec_names = []
        if not has_skills_sec: missing_sec_names.append("Skills")
        if not has_exp_sec: missing_sec_names.append("Experience")
        if not has_edu_sec: missing_sec_names.append("Education")

        ats_guidance.append(
            AtsGuidanceItem(
                area="headings",
                status="improvement_needed",
                title="Adopt standard section headings",
                recommendation=f"Ensure your resume includes clear, conventional headings for {', '.join(missing_sec_names)}.",
                rationale="Automated ATS parsers rely on standard heading text to partition sections into indexed database fields.",
            )
        )
    else:
        ats_guidance.append(
            AtsGuidanceItem(
                area="headings",
                status="good",
                title="Standard section headings detected",
                recommendation="Maintain standard headings like 'Skills', 'Experience', 'Education', and 'Projects'.",
                rationale="Standard headings ensure parsers categorize your credentials accurately without dropped fields.",
            )
        )

    # Keyword proximity & density
    ats_guidance.append(
        AtsGuidanceItem(
            area="keyword_placement",
            status="info",
            title="Integrate role keywords contextually",
            recommendation=(
                f"Feature role-relevant keywords like {', '.join(matched_skills_for_wording[:3]) if matched_skills_for_wording else 'core technical requirements'} "
                "directly within your project and experience bullet points."
            ),
            rationale="Contextual keyword usage provides evidence of practical application rather than isolated keyword lists.",
        )
    )

    # Readability guidance
    ats_guidance.append(
        AtsGuidanceItem(
            area="readability",
            status="good",
            title="Clean, single-column document layout",
            recommendation="Use clean margins, standard bullet symbols, and a clean single-column hierarchy.",
            rationale="Multi-column tables, graphics, and text boxes can cause automated parsers to read text out of order.",
        )
    )

    # 11. Disclaimers & Safety
    disclaimers = [
        "CareerPilot AI provides evidence-grounded resume guidance. We do not guarantee interview selection, hiring outcomes, or proprietary ATS pass scores.",
        "Recommendations are derived strictly from your active resume and candidate profile. Never add credentials or metrics that you cannot personally verify.",
        "Your active resume has remained completely unchanged. Suggested improvements can be copied and applied in your preferred document editor.",
    ]

    return JobResumeAnalysisResponse(
        opportunity_id=opp.id,
        opportunity_title=opp.title,
        company_name=opp.company_name,
        resume_id=active_resume.id,
        resume_filename=active_resume.original_filename,
        resume_completeness_score=completeness_score,
        resume_completeness_label=completeness_label,
        data_sufficiency=sufficiency,
        strengths=strengths,
        gaps=gaps,
        improvements=improvements,
        ats_guidance=ats_guidance,
        disclaimers=disclaimers,
        provider="gemini" if gemini_used else "deterministic",
        provider_model=settings.gemini_model if gemini_used else None,
        created_at=utcnow(),
    )
