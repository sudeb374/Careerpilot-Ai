# CareerPilot AI — Requirements

## 1. Project Overview

CareerPilot AI is an AI-powered career discovery and internship matching platform for college students and freshers. It helps users discover relevant opportunities, assess their suitability, improve their resumes, and track career progress.

## 2. Target Users

- College students (undergrad and postgrad)
- Recent graduates / freshers
- Career-switching early professionals

## 3. Functional Requirements

### 3.1 User Management
- User registration and login via Supabase Auth
- Profile creation with education, skills, interests, and experience
- Profile editing and deletion

### 3.2 Opportunity Discovery
- Browse and search internships and entry-level jobs
- Filter by domain, location, duration, stipend, and skills
- AI-powered matching based on user profile

### 3.3 Resume Analysis
- Upload resume (PDF)
- AI-driven resume scoring and feedback
- Skill gap identification
- Suggestions for improvement

### 3.4 Career Insights
- Personalized career path recommendations
- Skill trend analysis
- Industry-specific guidance

### 3.5 Dashboard
- Overview of matched opportunities
- Application tracking
- Resume score history
- Skill progress visualization

## 4. Non-Functional Requirements

> **Note:** The performance and scalability numbers below are aspirational targets for the MVP. They have not been verified through load testing or production monitoring. Actual capabilities will be validated during Phase 9 (Testing and Evaluation).

| Requirement     | Target                                                       |
|-----------------|--------------------------------------------------------------|
| Performance     | API responses < 500ms for non-AI endpoints (target, untested)|
| Scalability     | Support 1,000 concurrent users at launch (target, untested)  |
| Security        | OWASP Top 10 compliance, encrypted secrets                   |
| Accessibility   | WCAG 2.1 AA compliance                                      |
| Responsiveness  | Mobile-first, supports 320px–1920px viewports                |
| Availability    | 99.5% uptime target (requires infrastructure validation)     |

## 5. Phase Breakdown

| Phase | Scope                                                  | Status      |
|-------|--------------------------------------------------------|-------------|
| 1     | Project foundation, structure, design system           | Complete    |
| 2     | Authentication and student profiles                    | Complete    |
| 3     | Opportunity management                                 | Complete    |
| 4     | Resume intelligence                                    | Complete    |
| 5     | AI matching engine                                     | Complete    |
| 6     | Authorized automated ingestion                         | Complete    |
| 7     | Career copilot                                         | In Progress (Phase 7.1 Complete) |
| 8     | Application tracker                                    | Planned     |
| 9     | Testing and evaluation                                 | Planned     |
| 10    | Deployment and presentation                            | Planned     |

### 5.1 Phase 6: Automated Ingestion Plan & Scope Decisions

See [docs/ingestion-plan.md](ingestion-plan.md) for full architectural specifications.

- **Phase 6.1 (API Ingestion)**: RapidAPI JSearch integration with bounded payloads, savepoints, and canonical skill matching (**Complete**).
- **Phase 6.2 (Discovery & Matching Workflow)**: End-to-end admin review gating, conflict prevention, student discovery filters, safe URL navigation, candidate data isolation (**Complete**).
- **Phase 6.3 (Authorized RSS Ingestion)**: Structured RSS 2.0 / Atom feed parsing, SSRF protection, shared normalization, and cross-source deduplication (**Complete**).
- **Phase 6.4 (Scheduled Refresh & Fallback Uploads)**: Automated refresh, deadline expiration, and bulk CSV/JSON upload fallback (**Complete**).

#### Architectural Decision: BeautifulSoup Web Scraping Deferred
Website scraping using BeautifulSoup, Selenium, or Playwright is **intentionally deferred and not implemented**:
1. JSearch provides an authorized API-based ingestion channel.
2. Approved RSS feeds provide clean, structured data with explicit schemas.
3. Avoiding brittle site-specific DOM parsers, unneeded network overhead, and scraping legal/permission uncertainty.
4. Admin fallback uploads support sources that cannot be integrated via direct API or RSS feeds safely.
Scraping will only be reconsidered if an authorized provider explicitly allows automated scraping and a clear technical need arises. Phase 6 is not complete until all remaining requirements are implemented or formally approved.

### 5.2 Phase 7: Career Copilot

- **Phase 7.1 (Personalized Skill-Gap Roadmap)**: (**Complete**)
  - Evidence-based analysis comparing authenticated student's profile skills and active-resume extracted skills against published opportunities.
  - Transparent, deterministic prioritization distinguishing required skills from desired/preferred skills.
  - Practical learning sequence stages (Stage 1: Essentials, Stage 2: Core Competencies, Stage 3: Differentiators) without fabricated courses, certificates, or prerequisites.
  - Clear identification and honest messaging for insufficient profile data or zero matching job postings.
  - Interactive profile skill saving directly from active-resume evidence or gap recommendations.
  - Heuristic skill coverage metric with score integrity disclaimers (preventing hiring probability claims).

## 6. AI Match Score Disclaimer

AI-generated match scores (e.g., opportunity-to-profile relevance) are **heuristic recommendations** based on semantic similarity, skill overlap, and profile metadata. They must **not** be represented or interpreted as:

- Probabilities of selection or hiring
- Guarantees of fit or suitability
- Rankings endorsed by employers

All user-facing match scores must include appropriate context (e.g., "Based on your profile, this opportunity appears relevant") and avoid language that implies certainty of outcome.

## 7. Constraints

- Must use the defined tech stack (Next.js, FastAPI, PostgreSQL, Supabase, Gemini API)
- No paid third-party APIs beyond Gemini during MVP
- Must work offline-capable for core browsing features (stretch goal)
