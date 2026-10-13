import logging
import re
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
from app.schemas.cover_letter import (
    CoverLetterGenerateRequest,
    CoverLetterGenerateResponse,
    CoverLetterLength,
    CoverLetterTone,
    OpportunityContextForLetter,
    VerifiedEvidenceSummary,
)

logger = logging.getLogger(__name__)


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r'[^a-z0-9]', '', text.lower())


def get_gemini_api_url(model: str = "gemini-1.5-flash") -> str:
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def format_cover_letter_footer(full_name: str) -> str:
    """
    Returns the required, standardized footer structure with editable placeholders.
    Never includes hardcoded or stored personal social links.
    """
    clean_name = full_name.strip() if full_name and full_name.strip() else "Candidate"
    return (
        f"Sincerely,\n"
        f"{clean_name}\n\n"
        f"LinkedIn: Your LinkedIn URL\n"
        f"GitHub: Your GitHub URL\n"
        f"Portfolio: Your Portfolio URL"
    )


CLOSING_PATTERN = re.compile(
    r"\n\s*(?:Sincerely(?: yours)?|Yours sincerely|With (?:best|warm|kind)? regards|Warm regards|Warmly|Best regards|Kind regards|Regards|Respectfully(?: yours)?)(?:\s*,|\s*\n).*$",
    re.IGNORECASE | re.DOTALL,
)


def enforce_cover_letter_footer(text: str, full_name: str) -> str:
    """
    Enforces the mandatory, standardized candidate sign-off footer across all generated cover letters.
    Guarantees generic editable placeholders for LinkedIn, GitHub, and Portfolio URLs,
    and prevents LLM hallucinations, personal URLs, or inconsistent closing structures.
    """
    clean_name = full_name.strip() if full_name and full_name.strip() else "Candidate"
    raw = text.strip()

    m = CLOSING_PATTERN.search(raw)
    if m:
        body = raw[:m.start()].rstrip()
    else:
        # Check if the text concludes with candidate name, generic name placeholder, or loose social link headers
        fallback_patterns = [
            re.compile(r"\n\s*" + re.escape(clean_name) + r"\s*(?:\n.*)?$", re.IGNORECASE | re.DOTALL),
            re.compile(r"\n\s*\[?(?:Candidate(?:\x27?s)? Name|Your Name|Full Name|Candidate)\]?\s*(?:\n.*)?$", re.IGNORECASE | re.DOTALL),
            re.compile(r"\n\s*(?:LinkedIn|GitHub|Portfolio):\s*.*$", re.IGNORECASE | re.DOTALL),
        ]
        body = raw
        for pat in fallback_patterns:
            fm = pat.search(body)
            if fm:
                body = body[:fm.start()].rstrip()
                break

    return f"{body}\n\n{format_cover_letter_footer(clean_name)}"


class CandidateProfileContext:
    def __init__(
        self,
        full_name: str,
        headline: str | None,
        location: str | None,
        about: str | None,
        educations: list[Education],
        experiences: list[Experience],
        projects: list[Project],
        skills: list[str],
        resume_skills: list[dict[str, str]],
        warnings: list[str],
        linkedin_url: str | None = None,
        github_url: str | None = None,
        portfolio_url: str | None = None,
    ):
        self.full_name = full_name
        self.headline = headline
        self.location = location
        self.about = about
        self.educations = educations
        self.experiences = experiences
        self.projects = projects
        self.skills = skills
        self.resume_skills = resume_skills
        self.warnings = warnings
        self.linkedin_url = linkedin_url
        self.github_url = github_url
        self.portfolio_url = portfolio_url


async def gather_candidate_context(
    db: AsyncSession, profile_id: UUID
) -> CandidateProfileContext:
    stmt = (
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
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()

    if not profile:
        raise ValueError("Candidate profile not found")

    full_name = profile.full_name.strip() if profile.full_name else ""
    if not full_name:
        raise ValueError("Candidate profile does not have a full name configured.")

    # Gather manual skills
    skill_names: list[str] = []
    for ps in profile.skills:
        if ps.skill:
            skill_names.append(ps.skill.name)
        elif ps.custom_skill_name:
            skill_names.append(ps.custom_skill_name)

    # Gather active resume extracted skills & evidence
    resume_skills: list[dict[str, str]] = []
    active_resume = next((r for r in profile.resumes if r.is_active), None)
    if active_resume and active_resume.has_structured_data:
        r_skills = active_resume.structured_data.get("skills", [])
        for rs in r_skills:
            r_name = rs.get("name")
            r_evidence = rs.get("evidence", "")
            if r_name:
                resume_skills.append({"name": r_name, "evidence": r_evidence})
                if r_name not in skill_names:
                    skill_names.append(r_name)

    # Check for sufficient profile data
    has_content = bool(profile.educations or skill_names or profile.experiences or profile.projects)
    if not has_content:
        raise ValueError(
            "Your profile does not contain educational history or skills. "
            "Please add at least one education record or skill before generating a cover letter."
        )

    warnings: list[str] = []
    if not profile.educations:
        warnings.append("No education records listed; academic background omitted.")
    if not profile.experiences:
        warnings.append("No prior work experience listed; focusing on academic projects and verified skills.")
    if not skill_names:
        warnings.append("No verified skills recorded in profile or resume.")

    return CandidateProfileContext(
        full_name=full_name,
        headline=profile.headline,
        location=profile.location,
        about=profile.about,
        linkedin_url=profile.linkedin_url,
        github_url=profile.github_url,
        portfolio_url=profile.portfolio_url,
        educations=list(profile.educations),
        experiences=list(profile.experiences),
        projects=list(profile.projects),
        skills=skill_names,
        resume_skills=resume_skills,
        warnings=warnings,
    )


async def get_opportunity_context_for_candidate(
    db: AsyncSession, profile_id: UUID, opportunity_id: UUID
) -> OpportunityContextForLetter:
    opp_stmt = (
        select(Opportunity)
        .options(selectinload(Opportunity.skills).selectinload(OpportunitySkill.skill))
        .where(Opportunity.id == opportunity_id)
    )
    opp_res = await db.execute(opp_stmt)
    opp = opp_res.scalar_one_or_none()

    if not opp or opp.status != "Published":
        raise ValueError("Opportunity not found or not published.")

    candidate = await gather_candidate_context(db, profile_id)

    opp_skill_names = [os.skill.name for os in opp.skills if os.skill]
    cand_norms = {normalize_text(s): s for s in candidate.skills}

    matched: list[str] = []
    for os_name in opp_skill_names:
        if normalize_text(os_name) in cand_norms:
            matched.append(os_name)

    has_sufficient = bool(candidate.full_name and (candidate.educations or candidate.skills))
    val_msg = None if has_sufficient else "Profile needs education or skills to tailor letter."

    return OpportunityContextForLetter(
        opportunity_id=opp.id,
        title=opp.title,
        company_name=opp.company_name,
        opportunity_type=opp.opportunity_type,
        work_model=opp.work_model,
        locations=opp.locations or [],
        domain=opp.domain,
        skills_required=opp_skill_names,
        has_sufficient_candidate_data=has_sufficient,
        candidate_matched_skills=matched,
        validation_message=val_msg,
    )


def build_verified_evidence_summary(
    candidate: CandidateProfileContext, opp: Opportunity
) -> VerifiedEvidenceSummary:
    opp_skills = [os.skill.name for os in opp.skills if os.skill]
    cand_norms = {normalize_text(s): s for s in candidate.skills}

    matched_skills = [s for s in opp_skills if normalize_text(s) in cand_norms]
    if not matched_skills and candidate.skills:
        # Fall back to top 3 candidate skills
        matched_skills = candidate.skills[:3]

    included_projects = [p.name for p in candidate.projects[:3]]
    included_experiences = [f"{e.title} at {e.company}" for e in candidate.experiences[:2]]

    included_edu: list[str] = []
    for edu in candidate.educations[:2]:
        edu_str = f"{edu.degree} in {edu.field_of_study}" if edu.field_of_study else edu.degree
        included_edu.append(f"{edu_str} ({edu.institution})")

    resume_snippets = [
        f"{rs['name']}: {rs['evidence']}" for rs in candidate.resume_skills[:3] if rs.get("evidence")
    ]

    return VerifiedEvidenceSummary(
        matched_skills=matched_skills,
        included_projects=included_projects,
        included_experiences=included_experiences,
        included_education=included_edu,
        resume_evidence_snippets=resume_snippets,
    )


def generate_deterministic_cover_letter(
    candidate: CandidateProfileContext,
    opp: Opportunity,
    tone: CoverLetterTone,
    length: CoverLetterLength,
    additional_notes: str | None,
    evidence: VerifiedEvidenceSummary,
) -> tuple[str, str]:
    """
    Generates an honest, tailored cover letter strictly grounded in verified facts.
    Never invents employers, degrees, skills, or metrics.
    Returns (subject_line, cover_letter_text).
    """
    subject_line = f"Application for {opp.title} — {candidate.full_name}"

    # Salutation
    salutation = f"Dear {opp.company_name} Hiring Team,"

    # Opening Paragraph
    edu_ref = ""
    if candidate.educations:
        primary_edu = candidate.educations[0]
        deg_str = f"{primary_edu.degree} in {primary_edu.field_of_study}" if primary_edu.field_of_study else primary_edu.degree
        edu_ref = f" as a current student completing my {deg_str} at {primary_edu.institution}"
    elif candidate.headline:
        edu_ref = f" as a {candidate.headline}"

    if tone == CoverLetterTone.ENTHUSIASTIC:
        p1 = (
            f"I am thrilled to submit my application for the {opp.title} position at {opp.company_name}{edu_ref}. "
            f"Having followed {opp.company_name}'s work in the {opp.domain or 'technology'} space, I am deeply inspired by your team's mission. "
            f"I am eager to contribute my technical foundation and enthusiasm to your team."
        )
    elif tone == CoverLetterTone.CONFIDENT:
        p1 = (
            f"I am writing to express my strong interest in the {opp.title} role at {opp.company_name}{edu_ref}. "
            f"With a solid grounding in {', '.join(evidence.matched_skills[:3]) if evidence.matched_skills else 'software development'}, "
            f"I am confident in my ability to quickly add tangible value to your engineering initiatives."
        )
    else:  # Professional
        p1 = (
            f"Please accept this letter as an expression of my strong interest in the {opp.title} position currently open at {opp.company_name}{edu_ref}. "
            f"With my background and demonstrated commitment to quality software development, I welcome the opportunity to contribute to your team."
        )

    # Paragraph 2: Skills & Experience / Projects
    skills_phrase = f"core proficiencies in {', '.join(evidence.matched_skills)}" if evidence.matched_skills else "practical programming abilities"

    if candidate.experiences:
        top_exp = candidate.experiences[0]
        exp_desc = f" ({top_exp.description.strip()})" if top_exp.description and len(top_exp.description.strip()) < 120 else ""
        p2 = (
            f"Through my role as {top_exp.title} at {top_exp.company}{exp_desc}, I developed hands-on familiarity with professional workflows, "
            f"team collaboration, and delivering resilient solutions. Paired with my {skills_phrase}, this background has prepared me to tackle "
            f"the practical challenges of the {opp.title} position."
        )
    elif candidate.projects:
        top_proj = candidate.projects[0]
        proj_desc = f", where I {top_proj.description.strip()}" if top_proj.description and len(top_proj.description.strip()) < 150 else ""
        p2 = (
            f"My technical capabilities are reflected in my hands-on project work, such as {top_proj.name}{proj_desc}. "
            f"Developing this project reinforced my {skills_phrase} and taught me how to architect clean, maintainable code."
        )
    else:
        p2 = (
            f"My academic coursework and independent technical training have provided me with {skills_phrase}. "
            f"I focus on writing readable, well-tested code and continuously expanding my problem-solving capabilities."
        )

    # Paragraph 3: Technical Deep Dive / Academic Preparation (Expanded for Standard/Detailed)
    p3 = ""
    if length in (CoverLetterLength.STANDARD, CoverLetterLength.DETAILED):
        if len(candidate.projects) >= 2:
            second_proj = candidate.projects[1]
            p3 = (
                f"In addition, through my work on {second_proj.name}, I applied practical problem-solving to build and test functionality from the ground up. "
                f"I enjoy diving into technical specifications and collaborating cross-functionally to turn requirements into polished software."
            )
        elif len(candidate.experiences) >= 2:
            second_exp = candidate.experiences[1]
            p3 = (
                f"Additionally, my experience as {second_exp.title} at {second_exp.company} reinforced my understanding of deadlines, "
                f"system stability, and proactive communication."
            )
        elif evidence.matched_skills:
            p3 = (
                f"Specifically, my practical work with {', '.join(evidence.matched_skills)} aligns closely with the core technologies mentioned "
                f"in your posting for {opp.title}. I am comfortable reading documentation, writing modular code, and troubleshooting technical edge cases."
            )
        else:
            p3 = (
                f"Throughout my academic studies, I have emphasized foundational computer science principles, data structures, and disciplined engineering practices. "
                f"I take pride in writing well-documented, testable code and rapidly learning new tools as project requirements evolve."
            )

        if length == CoverLetterLength.DETAILED:
            p3 += (
                f" I actively seek out challenging problems that require thoughtful system design, continuous learning, and close attention to user requirements. "
                f"Whether working independently or pairing with senior engineers, I strive to deliver robust results that uphold high engineering standards."
            )

    # Paragraph 4 / Closing Alignment
    work_model_str = f" in a {opp.work_model.lower()} setting" if opp.work_model else ""
    location_str = f" in {', '.join(opp.locations)}" if opp.locations else ""

    note_phrase = ""
    if additional_notes and additional_notes.strip():
        clean_note = additional_notes.strip().rstrip('.')
        note_phrase = f" In particular, I am excited to {clean_note}."

    p_close = (
        f"I am eager to bring my work ethic and dedication to {opp.company_name}{work_model_str}{location_str}.{note_phrase} "
        f"Thank you for your time and consideration of my application. I look forward to the possibility of discussing how my background "
        f"and skills can support {opp.company_name}'s goals."
    )

    # Sign-off footer
    sign_off = format_cover_letter_footer(candidate.full_name)

    paragraphs = [p for p in [salutation, p1, p2, p3, p_close, sign_off] if p]
    cover_letter_text = "\n\n".join(paragraphs)

    return (subject_line, cover_letter_text)


async def call_gemini_api(
    candidate: CandidateProfileContext,
    opp: Opportunity,
    tone: CoverLetterTone,
    length: CoverLetterLength,
    additional_notes: str | None,
    evidence: VerifiedEvidenceSummary,
) -> str | None:
    """
    Calls the Gemini API with strict anti-hallucination prompting grounded exclusively
    in the candidate's verified profile data.
    """
    api_key = settings.gemini_api_key.strip()
    if not api_key or api_key == "dummy-key":
        return None

    # Construct verified facts prompt
    edu_bullets = "\n".join([f"- {e.degree} ({e.field_of_study or ''}) at {e.institution}" for e in candidate.educations]) or "None"
    exp_bullets = "\n".join([f"- {e.title} at {e.company}: {e.description or ''}" for e in candidate.experiences]) or "None"
    proj_bullets = "\n".join([f"- {p.name}: {p.description or ''}" for p in candidate.projects]) or "None"
    skill_bullets = ", ".join(candidate.skills) or "None"
    resume_bullets = "\n".join([f"- {rs['name']}: {rs['evidence']}" for rs in candidate.resume_skills]) or "None"

    word_targets = {
        CoverLetterLength.CONCISE: "approximately 200 to 250 words",
        CoverLetterLength.STANDARD: "approximately 300 to 350 words",
        CoverLetterLength.DETAILED: "approximately 400 to 450 words",
    }

    prompt = f"""You are a professional career advisor assisting a student candidate in drafting a targeted cover letter for an internship or entry-level job.

CRITICAL INTEGRITY AND ACCURACY RULES:
1. STRICT TRUTHFULNESS: You must ONLY reference the verified candidate facts provided below.
2. DO NOT INVENT or hallucinate any skills, previous employers, projects, degrees, GPAs, certifications, or metrics not explicitly listed below.
3. If an experience or project is not in the facts, DO NOT mention it.
4. Tone: {tone.value}
5. Target Length: {word_targets.get(length, 'approximately 300 words')}.
6. Structure: Salutation, 3-4 structured body paragraphs, followed by the exact closing footer below.
7. REQUIRED FOOTER: The letter MUST end with this exact closing and literal placeholders (do NOT insert real URLs or alter the placeholder text):
Sincerely,
{candidate.full_name}

LinkedIn: Your LinkedIn URL
GitHub: Your GitHub URL
Portfolio: Your Portfolio URL
8. Do not include markdown code block formatting (e.g. do not wrap in ```markdown or ```).

JOB DETAILS:
- Title: {opp.title}
- Company: {opp.company_name}
- Opportunity Type: {opp.opportunity_type}
- Work Model: {opp.work_model}
- Required Skills: {', '.join(evidence.matched_skills) if evidence.matched_skills else 'General software development'}
- Description Summary: {opp.description[:800] if opp.description else 'Not provided'}

CANDIDATE VERIFIED FACTS:
- Full Name: {candidate.full_name}
- Education:
{edu_bullets}
- Work Experience:
{exp_bullets}
- Projects:
{proj_bullets}
- Verified Skills:
{skill_bullets}
- Active Resume Evidence:
{resume_bullets}
- Additional Student Note: {additional_notes or 'None'}

Draft the personalized cover letter:"""

    url = f"{get_gemini_api_url()}?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1024,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        raw_text = parts[0]["text"].strip()
                        # Clean markdown code blocks if the model wrapped output
                        clean_text = re.sub(r'^```(?:markdown)?\s*', '', raw_text)
                        clean_text = re.sub(r'\s*```$', '', clean_text).strip()
                        return clean_text
            else:
                logger.warning("Gemini API call returned status %s: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("Gemini API call failed with exception: %s", str(exc))

    return None


async def generate_cover_letter(
    db: AsyncSession,
    profile_id: UUID,
    request: CoverLetterGenerateRequest,
) -> CoverLetterGenerateResponse:
    """
    Main cover letter generation pipeline.
    Validates candidate and opportunity, gathers verified evidence, and either calls
    configured LLM (Gemini) or executes the safe deterministic template fallback.
    """
    # 1. Fetch Opportunity
    opp_stmt = (
        select(Opportunity)
        .options(selectinload(Opportunity.skills).selectinload(OpportunitySkill.skill))
        .where(Opportunity.id == request.opportunity_id)
    )
    opp_res = await db.execute(opp_stmt)
    opp = opp_res.scalar_one_or_none()

    if not opp or opp.status != "Published":
        raise ValueError("Opportunity not found or not published.")

    # 2. Gather Candidate Context
    candidate = await gather_candidate_context(db, profile_id)

    # 3. Build Evidence Summary
    evidence = build_verified_evidence_summary(candidate, opp)

    # 4. Attempt Gemini LLM Generation if configured
    gemini_text = await call_gemini_api(
        candidate=candidate,
        opp=opp,
        tone=request.tone,
        length=request.length,
        additional_notes=request.additional_notes,
        evidence=evidence,
    )

    if gemini_text:
        enforced_gemini_text = enforce_cover_letter_footer(gemini_text, candidate.full_name)
        subject_line = f"Application for {opp.title} — {candidate.full_name}"
        return CoverLetterGenerateResponse(
            opportunity_id=opp.id,
            opportunity_title=opp.title,
            company_name=opp.company_name,
            recipient_name=f"{opp.company_name} Hiring Team",
            tone=request.tone,
            length=request.length,
            subject_line=subject_line,
            cover_letter_text=enforced_gemini_text,
            provider="gemini",
            provider_model="gemini-1.5-flash",
            is_template_fallback=False,
            provider_note=None,
            verified_evidence=evidence,
            data_warnings=candidate.warnings,
        )

    # 5. Deterministic Fallback Template Engine
    subject_line, fallback_text = generate_deterministic_cover_letter(
        candidate=candidate,
        opp=opp,
        tone=request.tone,
        length=request.length,
        additional_notes=request.additional_notes,
        evidence=evidence,
    )
    enforced_fallback_text = enforce_cover_letter_footer(fallback_text, candidate.full_name)

    provider_note = (
        "Generated using CareerPilot AI deterministic template engine because GEMINI_API_KEY is not configured "
        "or temporarily unreachable. Set GEMINI_API_KEY in backend/.env for AI-enhanced drafting."
    )

    return CoverLetterGenerateResponse(
        opportunity_id=opp.id,
        opportunity_title=opp.title,
        company_name=opp.company_name,
        recipient_name=f"{opp.company_name} Hiring Team",
        tone=request.tone,
        length=request.length,
        subject_line=subject_line,
        cover_letter_text=enforced_fallback_text,
        provider="template_fallback",
        provider_model=None,
        is_template_fallback=True,
        provider_note=provider_note,
        verified_evidence=evidence,
        data_warnings=candidate.warnings,
    )
