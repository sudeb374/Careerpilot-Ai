import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import Skill
from app.schemas.profile import (
    ResumeContact,
    ResumeSections,
    ResumeSkillInfo,
    ResumeStructuredData,
)

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
# A robust, standard phone number regex (matches 10 digits potentially with separators and country code)
PHONE_REGEX = re.compile(r'(?:(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})')
LINKEDIN_REGEX = re.compile(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+')
GITHUB_REGEX = re.compile(r'(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9-]+')
# Simple portfolio generic link (must start with http or www)
PORTFOLIO_REGEX = re.compile(r'(?:https?://|www\.)(?!linkedin\.com|github\.com)[a-zA-Z0-9-]+\.(?:com|org|net|io|me|dev)(?:/[^\s]*)?')

# Section headers
SECTION_REGEX = {
    "summary": re.compile(r'^\s*(summary|about|about me|profile|professional summary)\s*$', re.IGNORECASE),
    "skills": re.compile(r'^\s*(skills|technical skills|core competencies)\s*$', re.IGNORECASE),
    "education": re.compile(r'^\s*(education|academic background)\s*$', re.IGNORECASE),
    "experience": re.compile(r'^\s*(experience|work experience|employment|internships)\s*$', re.IGNORECASE),
    "projects": re.compile(r'^\s*(projects|personal projects|academic projects)\s*$', re.IGNORECASE),
    "certifications": re.compile(r'^\s*(certifications|licenses)\s*$', re.IGNORECASE),
    "achievements": re.compile(r'^\s*(achievements|awards|honors)\s*$', re.IGNORECASE),
    "publications": re.compile(r'^\s*(publications|papers)\s*$', re.IGNORECASE),
}

async def extract_structured_data(db: AsyncSession, parsed_text: str) -> ResumeStructuredData:
    contact = _extract_contact(parsed_text)
    sections = _extract_sections(parsed_text)
    
    # Prioritize 'skills' section for skill matching, fallback to whole text if not found
    search_text = sections.skills if sections.skills else parsed_text
    skills, warnings = await _extract_skills(db, search_text)
    
    if not skills:
        warnings.append("No recognized skills were found in the resume. Consider updating the resume or checking the skill catalog.")
    if not contact.phones:
        warnings.append("No phone number could be confidently identified. Please review contact details.")
    
    return ResumeStructuredData(
        schema_version=1,
        contact=contact,
        skills=skills,
        sections=sections,
        warnings=warnings
    )

def _extract_contact(text: str) -> ResumeContact:
    emails = list(set(EMAIL_REGEX.findall(text)))
    
    linkedin = list(set(LINKEDIN_REGEX.findall(text)))
    github = list(set(GITHUB_REGEX.findall(text)))
    
    portfolio_candidates = list(set(PORTFOLIO_REGEX.findall(text)))
    portfolio = []
    for p in portfolio_candidates:
        if "@" not in p and p not in linkedin and p not in github:
            portfolio.append(p)

    phones = []
    # 1. Prefer candidates near contact headings or labels
    phone_label_regex = re.compile(r'(?i)(?:phone|mobile|tel|telephone|whatsapp|contact)\s*[:\-]?\s*(\+?[\d\s\-\(\)]{7,25})')
    for match in phone_label_regex.finditer(text):
        candidate = match.group(1).strip()
        digits = sum(c.isdigit() for c in candidate)
        if 7 <= digits <= 15:
            phones.append(candidate)
    
    # 2. Consider the resume's initial contact block when labels are absent
    if not phones:
        header_text = text[:1500]
        # Match sequences that look like phone numbers
        fallback_regex = re.compile(r'(?<![a-zA-Z0-9])(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4,6}(?![a-zA-Z0-9])')
        for candidate in fallback_regex.findall(header_text):
            candidate = candidate.strip()
            digits = sum(c.isdigit() for c in candidate)
            if 7 <= digits <= 15:
                # Reject obvious non-phone candidates like years/dates
                if re.search(r'20\d{2}\s*-\s*20\d{2}', candidate) or re.search(r'19\d{2}\s*-\s*(?:19|20)\d{2}', candidate):
                    continue
                # Reject if contains letters
                if any(c.isalpha() for c in candidate):
                    continue
                phones.append(candidate)

    # Deduplicate while preserving order
    unique_phones = []
    for p in phones:
        if p not in unique_phones:
            unique_phones.append(p)
            
    return ResumeContact(
        emails=emails,
        phones=unique_phones,
        linkedin_urls=linkedin,
        github_urls=github,
        portfolio_urls=portfolio
    )

def _extract_sections(text: str) -> ResumeSections:
    lines = text.split('\n')
    current_section = None
    section_content: dict[str, list[str]] = {k: [] for k in SECTION_REGEX}
    
    for line in lines:
        matched_section = None
        for sec_name, regex in SECTION_REGEX.items():
            if regex.match(line):
                matched_section = sec_name
                break
                
        if matched_section:
            current_section = matched_section
        elif current_section:
            section_content[current_section].append(line)
            
    # Clean up contents
    result = {}
    for k, v in section_content.items():
        content = '\n'.join(v).strip()
        result[k] = content if content else None
        
    return ResumeSections(**result)

async def _extract_skills(db: AsyncSession, search_text: str) -> tuple[list[ResumeSkillInfo], list[str]]:
    stmt = select(Skill).options(selectinload(Skill.aliases))
    result = await db.execute(stmt)
    all_skills = result.scalars().unique().all()
    
    detected_skills = []
    seen_ids = set()
    warnings = []
    
    # We want to match whole words/phrases ignoring case.
    # To avoid regex compilation overhead for thousands of aliases per request,
    # we can construct a unified matcher or just iterate.
    # We will use boundary matching if it starts/ends with alphanumeric.
    
    search_text_lower = search_text.lower()
    
    def match_phrase(phrase: str) -> bool:
        phrase_lower = phrase.lower()
        if not phrase_lower:
            return False
            
        # If it's a simple alphanumeric phrase, check boundaries
        if phrase_lower.replace(" ", "").replace(".", "").replace("+", "").replace("-", "").isalnum():
            # escape special chars
            escaped = re.escape(phrase_lower)
            # if phrase ends/starts in alphanumeric, use \b, else not
            prefix = r'\b' if phrase_lower[0].isalnum() else ''
            suffix = r'\b' if phrase_lower[-1].isalnum() else ''
            pattern = f"{prefix}{escaped}{suffix}"
            return bool(re.search(pattern, search_text_lower))
        else:
            # Fallback for weird characters like C# or C++
            return phrase_lower in search_text_lower
    
    for skill in all_skills:
        # Check aliases first or canonical name
        phrases_to_check = [skill.name] + [a.alias for a in skill.aliases]
        
        for phrase in phrases_to_check:
            # Skip very short generic phrases that could cause false positives like 'C' or 'R'
            # unless properly bounded, but 'C' and 'R' are commonly false positives.
            # We rely on the boundary matcher, but it's still risky.
            
            if match_phrase(phrase):
                if skill.id not in seen_ids:
                    seen_ids.add(skill.id)
                    detected_skills.append(ResumeSkillInfo(
                        skill_id=skill.id,
                        name=skill.name,
                        evidence=phrase # The exact matched alias or canonical name
                    ))
                break
                
    return detected_skills, warnings
