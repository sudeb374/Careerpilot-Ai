import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Resume
from app.schemas.profile import (
    ResumeAnalysisData,
    ResumeAnalysisResponse,
    ResumeCategoryScores,
    ResumeFinding,
    ResumeStructuredData,
)


class ResumeAnalyzerError(Exception):
    pass


async def analyze_resume(db: AsyncSession, profile_id: UUID, resume_id: str) -> ResumeAnalysisResponse:
    # 1. Fetch Resume
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.profile_id == profile_id))
    resume = result.scalar_one_or_none()

    if not resume:
        raise ResumeAnalyzerError("Resume not found or unauthorized")
    
    if not resume.parsed_text:
        return ResumeAnalysisResponse(
            id=resume.id,
            status="error",
            message="Resume text has not been extracted yet."
        )

    if not resume.structured_data:
        return ResumeAnalysisResponse(
            id=resume.id,
            status="error",
            message="Structured data has not been generated yet. Please run extraction first."
        )

    structured = ResumeStructuredData.model_validate(resume.structured_data)
    analysis_data = compute_resume_analysis(structured, resume.parsed_text or "")

    resume.analysis_data = analysis_data.model_dump(mode="json")
    await db.commit()
    await db.refresh(resume)

    return ResumeAnalysisResponse(
        id=resume.id,
        status="success",
        analysis=analysis_data
    )


def compute_resume_analysis(structured: ResumeStructuredData, parsed_text: str = "") -> ResumeAnalysisData:
    findings: list[ResumeFinding] = []
    strengths: list[ResumeFinding] = []
    
    score_contact = 0
    score_summary = 0
    score_education = 0
    score_skills = 0
    score_projects_experience = 0
    score_organization = 0

    # --- 1. Contact (15 points) ---
    has_email = bool(structured.contact.emails)
    has_phone = bool(structured.contact.phones)
    
    if has_email: score_contact += 10
    if has_phone: score_contact += 5

    if has_email and has_phone:
        strengths.append(ResumeFinding(
            identifier="contact_essential", category="contact", severity="info",
            title="Essential Contact Info Present",
            explanation="Your resume includes both an email address and a phone number.",
            recommendation="Ensure your contact information is placed clearly at the top of the resume."
        ))
    elif has_email or has_phone:
        findings.append(ResumeFinding(
            identifier="contact_partial", category="contact", severity="medium",
            title="Incomplete Contact Information",
            explanation="Either an email address or a phone number is missing or could not be confidently identified.",
            recommendation="Ensure both your email and a valid phone number are clearly listed at the top of your resume."
        ))
    else:
        findings.append(ResumeFinding(
            identifier="contact_missing", category="contact", severity="high",
            title="Missing Contact Information",
            explanation="Neither an email address nor a phone number was detected.",
            recommendation="Add your email address and phone number to the header of your resume so employers can reach you."
        ))

    # Contact Link Detection (LinkedIn, GitHub, Portfolio)
    # Rules: Do not require internet access / crawling. Report presence accurately.
    if structured.contact.linkedin_urls:
        strengths.append(ResumeFinding(
            identifier="linkedin_detected", category="contact", severity="info",
            title="LinkedIn Link Detected",
            explanation=f"LinkedIn link detected ({structured.contact.linkedin_urls[0]}). Found in resume text or extracted hyperlinks.",
            recommendation="Ensure your external profiles are up to date and consistent with your resume."
        ))
    else:
        findings.append(ResumeFinding(
            identifier="linkedin_optional", category="contact", severity="low",
            title="Optional: Add LinkedIn Profile",
            explanation="LinkedIn link not found in the resume text or extracted hyperlinks.",
            recommendation="Adding a LinkedIn profile link is an optional, role-appropriate way for reviewers to learn more about your background."
        ))

    has_code_or_portfolio = bool(structured.contact.github_urls or structured.contact.portfolio_urls)
    if has_code_or_portfolio:
        all_links = structured.contact.github_urls + structured.contact.portfolio_urls
        strengths.append(ResumeFinding(
            identifier="portfolio_detected", category="contact", severity="info",
            title="GitHub / Portfolio Link Detected",
            explanation=f"GitHub/Portfolio link detected ({all_links[0]}). Found in resume text or extracted hyperlinks.",
            recommendation="Ensure linked repositories include concise README files and live demos where applicable."
        ))
    else:
        findings.append(ResumeFinding(
            identifier="portfolio_optional", category="contact", severity="low",
            title="Optional: Add GitHub or Portfolio",
            explanation="GitHub/Portfolio link not found in the resume text or extracted hyperlinks.",
            recommendation="For technical and engineering roles, adding a link to your GitHub or personal portfolio is an optional, high-impact addition when available."
        ))

    # --- 2. Summary (10 points) ---
    summary_text = (structured.sections.summary or "").strip()
    if len(summary_text) >= 30:
        score_summary = 10
        strengths.append(ResumeFinding(
            identifier="summary_present", category="summary", severity="info",
            title="Professional Summary Detected",
            explanation="A professional summary section was found with substantive content.",
            recommendation="Ensure your summary highlights your unique value proposition rather than just stating your objective."
        ))
    elif len(summary_text) > 0:
        score_summary = 5
        findings.append(ResumeFinding(
            identifier="summary_short", category="summary", severity="low",
            title="Brief Professional Summary",
            explanation="A summary section header was identified, but contains very brief content.",
            recommendation="Expand your summary to 2-3 focused sentences articulating your target role and top skills."
        ))
    else:
        score_summary = 0
        findings.append(ResumeFinding(
            identifier="summary_missing", category="summary", severity="medium",
            title="No Professional Summary",
            explanation="No professional summary section was detected.",
            recommendation="Add a 2-3 sentence summary at the top of your resume highlighting your top skills and career goals."
        ))

    # --- 3. Education (15 points) ---
    edu_text = (structured.sections.education or "").strip()
    if len(edu_text) >= 30:
        score_education = 15
        strengths.append(ResumeFinding(
            identifier="education_present", category="education", severity="info",
            title="Education Section Detected",
            explanation="An education section was recognized.",
            recommendation="Make sure to list your graduation date, degree, and major clearly."
        ))
    elif len(edu_text) > 0:
        score_education = 8
        findings.append(ResumeFinding(
            identifier="education_brief", category="education", severity="medium",
            title="Brief Education Details",
            explanation="An education heading was found, but extracted content is limited.",
            recommendation="Detail your degree, university or institute name, and expected graduation year."
        ))
    else:
        score_education = 0
        findings.append(ResumeFinding(
            identifier="education_missing", category="education", severity="high",
            title="No Education Section",
            explanation="No education section was recognized.",
            recommendation="Add an 'Education' section detailing your degree, university, and graduation year."
        ))

    # --- 4. Skills (20 points) ---
    skill_count = len(structured.skills)
    if skill_count >= 5:
        score_skills = 20
        strengths.append(ResumeFinding(
            identifier="skills_strong", category="skills", severity="info",
            title="Good Skill Coverage",
            explanation=f"{skill_count} catalog skills were detected.",
            recommendation="Review the extracted skills to ensure they accurately reflect your strengths."
        ))
    elif skill_count > 0:
        score_skills = 10
        findings.append(ResumeFinding(
            identifier="skills_partial", category="skills", severity="low",
            title="Limited Skills Detected",
            explanation=f"Only {skill_count} catalog skills were detected.",
            recommendation="Consider adding a dedicated 'Skills' section or explicitly mentioning key technologies in your experience."
        ))
    else:
        score_skills = 0
        findings.append(ResumeFinding(
            identifier="skills_missing", category="skills", severity="medium",
            title="No Recognized Skills",
            explanation="No skills from our standard catalog were detected.",
            recommendation="Ensure you clearly state your technical and professional skills. Note: Our catalog matcher may not recognize every niche skill."
        ))

    # --- 5. Projects and Experience (25 points max) ---
    exp_text = (structured.sections.experience or "").strip()
    proj_text = (structured.sections.projects or "").strip()
    has_substantive_exp = len(exp_text) >= 40
    has_substantive_proj = len(proj_text) >= 40
    
    if has_substantive_exp and has_substantive_proj:
        score_projects_experience = 25
        strengths.append(ResumeFinding(
            identifier="exp_proj_both", category="experience", severity="info",
            title="Strong Experience Profile",
            explanation="Both professional experience and projects were detected.",
            recommendation="Ensure you use measurable metrics to describe your outcomes in both sections."
        ))
    elif has_substantive_exp:
        score_projects_experience = 25
        strengths.append(ResumeFinding(
            identifier="exp_only", category="experience", severity="info",
            title="Professional Experience Detected",
            explanation="Experience section found. Projects can be optional if you have extensive experience.",
            recommendation="Consider describing project outcomes with measurable evidence where accurate."
        ))
    elif has_substantive_proj:
        score_projects_experience = 20
        strengths.append(ResumeFinding(
            identifier="proj_only", category="experience", severity="info",
            title="Projects Building Experience",
            explanation="Projects section found. This provides strong evidence of your abilities.",
            recommendation="Ensure your project descriptions highlight your specific contributions and technical stack."
        ))
        findings.append(ResumeFinding(
            identifier="no_formal_exp", category="experience", severity="low",
            title="No Professional Experience",
            explanation="No formal experience section was recognized.",
            recommendation="If you have internships or relevant jobs, ensure they are clearly labeled under 'Experience'."
        ))
    elif exp_text or proj_text:
        score_projects_experience = 10
        findings.append(ResumeFinding(
            identifier="brief_exp_proj", category="experience", severity="medium",
            title="Brief Project or Experience Information",
            explanation="A section heading was found, but very few details or bullet points were detected.",
            recommendation="Add descriptive bullet points detailing the problems you solved and tools you applied."
        ))
    else:
        score_projects_experience = 0
        findings.append(ResumeFinding(
            identifier="no_exp_proj", category="experience", severity="high",
            title="Missing Experience and Projects",
            explanation="Neither an experience nor a projects section was detected.",
            recommendation="It is critical to add either an 'Experience' or 'Projects' section to demonstrate your practical abilities."
        ))

    # --- 6. Quality & Actionable Content Recommendations ---
    # Bullet specificity, active contributions, measurable results
    combined_body = f"{exp_text}\n{proj_text}".lower()
    if combined_body:
        passive_indicators = ["worked on", "assisted with", "helped to", "responsible for", "participated in", "member of", "was involved in"]
        active_indicators = ["built", "developed", "architected", "engineered", "implemented", "created", "designed", "led", "automated", "optimized", "refactored"]

        has_passive = any(p in combined_body for p in passive_indicators)
        has_active = any(a in combined_body for a in active_indicators)

        if has_passive:
            findings.append(ResumeFinding(
                identifier="contribution_clarity", category="experience", severity="medium",
                title="Clarify Specific Individual Contributions",
                explanation="Some project or experience bullets use general phrasing ('worked on', 'responsible for') rather than specifying your direct contribution.",
                recommendation="A project bullet would be clearer if it described the candidate's specific contribution (e.g., 'Architected database schema and built REST API' instead of 'Worked on backend')."
            ))
        elif has_active:
            strengths.append(ResumeFinding(
                identifier="strong_action_verbs", category="experience", severity="info",
                title="Action-Oriented Contribution Language",
                explanation="Your project or experience bullets use active verbs describing concrete technical ownership.",
                recommendation="Continue leading each bullet point with strong action verbs that highlight what you personally built or achieved."
            ))

        # Check for measurable results
        has_metrics = bool(re.search(r'\b(?:\d+%(?:\s+increase|\s+reduction|\s+growth|\s+improvement)?|\d+\+?\s*(?:users|clients|requests|ms|seconds|minutes|downloads|queries|endpoints))\b', combined_body))
        if has_metrics:
            strengths.append(ResumeFinding(
                identifier="measurable_results_detected", category="experience", severity="info",
                title="Measurable Outcomes Detected",
                explanation="Your descriptions include quantifiable indicators or scale (percentages, latency, or counts).",
                recommendation="Be prepared to substantiate any metrics cited during technical interview discussions."
            ))
        elif len(combined_body) >= 60:
            findings.append(ResumeFinding(
                identifier="measurable_results_suggestion", category="experience", severity="low",
                title="Consider Adding Measurable Results",
                explanation="Accomplishments describe activities and tools, but do not yet include quantifiable outcomes or scale.",
                recommendation="An accomplishment could benefit from a measurable result (e.g., scale handled, latency improved, or tests written), provided the user can substantiate it."
            ))

    # --- 7. Section Organization (15 points) ---
    sections_found = sum(1 for v in [structured.sections.summary, structured.sections.education, structured.sections.experience, structured.sections.skills, structured.sections.projects] if v and len(v.strip()) >= 20)
    if sections_found >= 4:
        score_organization = 15
        strengths.append(ResumeFinding(
            identifier="org_good", category="organization", severity="info",
            title="Well Organized Sections",
            explanation="Your resume has standard, easily recognizable sections.",
            recommendation="Maintain clear headings so automated parsers and human reviewers can quickly scan your document."
        ))
    elif sections_found >= 2:
        score_organization = 10
        findings.append(ResumeFinding(
            identifier="org_partial", category="organization", severity="medium",
            title="Improve Section Organization",
            explanation="Some standard resume sections could not be identified.",
            recommendation="Use clear, standard headings like 'Experience', 'Education', 'Projects', and 'Skills'."
        ))
    else:
        score_organization = 5
        findings.append(ResumeFinding(
            identifier="org_poor", category="organization", severity="high",
            title="Unclear Section Organization",
            explanation="Very few standard sections were identified.",
            recommendation="Reformat your resume to use standard, clear headings for each section to improve readability."
        ))

    total_score = score_contact + score_summary + score_education + score_skills + score_projects_experience + score_organization
    
    if total_score >= 80:
        score_label = "Strong completeness"
    elif total_score >= 60:
        score_label = "Good completeness"
    elif total_score >= 40:
        score_label = "Fair completeness"
    else:
        score_label = "Needs improvement"

    analysis_data = ResumeAnalysisData(
        schema_version=1,
        analysis_generated_at=datetime.now(timezone.utc),
        completeness_score=total_score,
        score_label=score_label,
        category_scores=ResumeCategoryScores(
            contact=score_contact,
            summary=score_summary,
            education=score_education,
            skills=score_skills,
            experience_projects=score_projects_experience,
            organization=score_organization,
        ),
        findings=findings,
        strengths=strengths,
        limitations=[
            "This score measures completeness and structure, not ATS compatibility or hiring probability.",
            "Contact link presence is detected from text and document hyperlinks without requiring external web crawling.",
            "Suggestions for metrics and links are optional, role-appropriate recommendations. Never invent accomplishments or credentials."
        ]
    )

    return analysis_data


async def get_resume_analysis(db: AsyncSession, profile_id: UUID, resume_id: str) -> ResumeAnalysisResponse:
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.profile_id == profile_id))
    resume = result.scalar_one_or_none()

    if not resume:
        raise ResumeAnalyzerError("Resume not found or unauthorized")

    if not resume.analysis_data:
        return ResumeAnalysisResponse(
            id=resume.id,
            status="pending",
            message="No analysis exists for this resume yet."
        )

    return ResumeAnalysisResponse(
        id=resume.id,
        status="success",
        analysis=ResumeAnalysisData(**resume.analysis_data)
    )
