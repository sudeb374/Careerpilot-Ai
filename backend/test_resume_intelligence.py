"""
Unit tests for Resume Intelligence improvements:
- Completeness vs Quality separation
- Non-empty section validation
- Substantive bullet points and active verbs analysis
- Measurable outcomes recommendations with substantiation reminder
- Hyperlink presence detection without web crawling
"""

import unittest
from app.services.structured_extractor import (
    _extract_contact,
    _extract_sections,
    LINKEDIN_REGEX,
    GITHUB_REGEX,
    PORTFOLIO_REGEX,
)
from app.services.resume_analyzer import compute_resume_analysis
from app.schemas.profile import ResumeStructuredData, ResumeSkillInfo


class TestResumeIntelligence(unittest.TestCase):
    def test_regex_patterns(self):
        # Test LinkedIn variations
        self.assertTrue(LINKEDIN_REGEX.search("Check out https://www.linkedin.com/in/john-doe-123 for profile"))
        self.assertTrue(LINKEDIN_REGEX.search("linkedin.com/in/johndoe"))
        self.assertTrue(LINKEDIN_REGEX.search("https://in.linkedin.com/in/johndoe"))

        # Test GitHub variations
        self.assertTrue(GITHUB_REGEX.search("https://github.com/johndoe"))
        self.assertTrue(GITHUB_REGEX.search("github.com/johndoe/project-repo"))

        # Test Portfolio domains
        self.assertTrue(PORTFOLIO_REGEX.search("https://johndoe.dev"))
        self.assertTrue(PORTFOLIO_REGEX.search("https://portfolio.johndoe.me"))
        self.assertTrue(PORTFOLIO_REGEX.search("https://johndoe.github.io"))

    def test_structured_extractor_link_detection(self):
        text = """
        John Doe
        Email: john.doe@example.com
        Phone: +91 9876543210
        LinkedIn: https://www.linkedin.com/in/johndoe
        GitHub: https://github.com/johndoe
        Portfolio: https://johndoe.dev

        EDUCATION
        B.Tech Computer Science, ABC University, 2024

        SKILLS
        Python, FastAPI, React, PostgreSQL

        EXPERIENCE
        Software Engineering Intern, TechCorp
        - Responsible for helping the team with bug fixes
        - Built automated ingestion pipeline reducing latency by 35%

        PROJECTS
        CareerPilot AI: Built full stack matching system
        """
        contact = _extract_contact(text)
        self.assertIn("john.doe@example.com", contact.emails)
        self.assertTrue(any("9876543210" in p for p in contact.phones))
        self.assertEqual(contact.linkedin_urls, ["https://www.linkedin.com/in/johndoe"])
        self.assertEqual(contact.github_urls, ["https://github.com/johndoe"])
        self.assertEqual(contact.portfolio_urls, ["https://johndoe.dev"])

    def test_resume_analyzer_completeness_and_quality(self):
        text = """
        John Doe
        john.doe@example.com | +91 9876543210
        LinkedIn: https://linkedin.com/in/johndoe
        GitHub: https://github.com/johndoe

        SUMMARY
        Motivated software engineer with experience in cloud architectures and Python backend services.

        EDUCATION
        B.Tech in Computer Science and Engineering, 2024. CGPA: 8.8

        SKILLS
        Python, FastAPI, SQL, Docker, React, Git

        EXPERIENCE
        Backend Intern at CloudSolutions
        - Responsible for working on API development with senior staff.
        - Designed and deployed RESTful services serving 10,000 daily users.

        PROJECTS
        Distributed Cache: Architected high-throughput in-memory caching layer in Go.
        """
        contact = _extract_contact(text)
        sections = _extract_sections(text)
        from uuid import uuid4
        skills = [
            ResumeSkillInfo(skill_id=uuid4(), name="Python", evidence="Python"),
            ResumeSkillInfo(skill_id=uuid4(), name="FastAPI", evidence="FastAPI"),
            ResumeSkillInfo(skill_id=uuid4(), name="SQL", evidence="SQL"),
            ResumeSkillInfo(skill_id=uuid4(), name="Docker", evidence="Docker"),
        ]

        structured = ResumeStructuredData(
            schema_version=1,
            contact=contact,
            skills=skills,
            sections=sections,
            warnings=[],
        )

        analysis = compute_resume_analysis(structured, text)

        # 1. Completeness score
        self.assertGreaterEqual(analysis.completeness_score, 70)
        self.assertIn("completeness", analysis.score_label.lower())

        # 2. LinkedIn & GitHub detected strengths
        titles = [s.title for s in analysis.strengths]
        self.assertTrue(any("LinkedIn" in t for t in titles))
        self.assertTrue(any("GitHub" in t or "Portfolio" in t for t in titles))

        # 3. Action verbs and measurable impact suggestions
        finding_titles = [f.title for f in analysis.findings]
        # Since we included "Responsible for working on...", it should suggest active contribution verbs
        self.assertTrue(any("Contribution" in t or "Action" in t for t in finding_titles))

        # 4. Check that recommendations explicitly note substantiation integrity
        recommendations = " ".join([f.recommendation for f in analysis.findings])
        self.assertTrue("substantiate" in recommendations.lower() or "quantifiable" in recommendations.lower())

    def test_no_perfect_score_for_empty_sections(self):
        # A resume with just empty headers should not get full organization/section points
        empty_headers_text = """
        John Doe
        john@example.com

        EDUCATION

        SKILLS

        EXPERIENCE

        PROJECTS
        """
        contact = _extract_contact(empty_headers_text)
        sections = _extract_sections(empty_headers_text)
        structured = ResumeStructuredData(
            schema_version=1,
            contact=contact,
            skills=[],
            sections=sections,
            warnings=[],
        )

        analysis = compute_resume_analysis(structured, empty_headers_text)
        self.assertLess(analysis.completeness_score, 60)
        self.assertEqual(analysis.category_scores.experience_projects, 0)


if __name__ == "__main__":
    unittest.main()
