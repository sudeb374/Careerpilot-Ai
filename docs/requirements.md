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
| 7     | Career copilot                                         | Complete (Phases 7.1, 7.2, 7.3, 7.4 & 7.5 Complete) |
| 8     | Application tracker                                    | Complete    |
| 9     | Testing and evaluation                                 | Planned     |
| 10    | Deployment and presentation                            | Planned     |

### 5.3 Phase 8: Application Tracker

- **Application Lifecycle Tracking**:
  - Full workflow pipeline supporting statuses: `Saved`, `Applied`, `Assessment`, `Interview`, `Offer`, `Rejected`, and `Withdrawn`.
  - Clear architectural distinction between saving an opportunity (`SavedOpportunity` / `Saved` status) and marking it as submitted (`Applied` status with explicit `applied_at` timestamp).
  - Additive database tables: `applications` and `application_status_history` with foreign keys, unique constraint preventing duplicate application records per candidate and opportunity, and cascading cleanup.
  - Strict candidate data isolation: all application reads, updates, and deletions are scoped strictly to the authenticated student's `profile_id`.
  - Status transition audit logging: all status changes append to `application_status_history` with optional student notes and timestamps.
- **Deadlines & Personal Reminders**:
  - Independent deadline and reminder dates: official application deadlines are tracked separately from personal follow-up reminder datetimes.
  - In-app reminder workflow: partitions candidate reminders into `due_reminders` (past or due today) and `upcoming_reminders` (scheduled within the next 7 days).
  - Dismissible and editable reminder dates and reminder notes directly within the tracker.
- **Candidate Analytics & Honest Metrics**:
  - Summarizes total tracked, total submitted, active in-progress (assessments/interviews), offers, and status breakdowns.
  - Response rate and interview conversion rate calculations with explicit small-sample-size disclosures (`< 5 submitted applications is too small for statistical certainty`).
- **User Interface & Experience**:
  - Student page at `/applications` with dashboard navigation, status filter tabs, search by company/role/notes, and sorting options.
  - Interactive Application Management & History modal with status changer, date pickers, personal notes editor, and chronological milestone audit timeline.
  - "Track Application" flow allows selecting from saved opportunities or published listings, setting initial pipeline status, and custom notes.
  - Embedded `TrackApplicationButton` on opportunity detail pages and opportunity cards for seamless one-click tracking or status checks.

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

- **Phase 7.2 (Personalized Cover Letter Generation)**: (**Complete**)
  - Tailored cover letter drafting grounded strictly in verified candidate records (name, education, projects, skills, experiences, and active-resume evidence) and published opportunity specifications.
  - Controls for professional tone (Professional, Enthusiastic, Confident) and length (Concise, Standard, Detailed), plus optional student focus notes.
  - Provider abstraction: Gemini API integration with honest, transparent deterministic template fallback when unconfigured or unreachable.
  - Audit trail of verified candidate evidence cited, in-browser editable preview, copy-to-clipboard, and text export.
  - Validation guardrails preventing empty profile generation or unpublished opportunity access, with zero automatic application submission.

- **Phase 7.3 (AI-Powered Application Question Assistance)**: (**Complete**)
  - Evidence-based answer generation for screening and application questions (e.g., Why hire you, project deep-dive, role interest, strengths, skills match).
  - Works with a selected published opportunity or in general application mode (`opportunity_id=None`).
  - Answer style options (Professional, Concise, Detailed), optional custom word limit, and specific student focus note.
  - Primary provider: Configurable Gemini API (`gemini-2.5-flash`) with strict anti-hallucination prompting and untrusted input isolation.
  - Deterministic grounded fallback engine when Gemini is unconfigured, rate-limited, timed out, or unavailable, with transparent provider disclosure.
  - Factual evidence audit trail distinguishing verified profile skills from resume-extracted skills, and explicitly flagging unassumed personal facts (visa/authorization/salary).
  - In-browser editable textarea draft, 1-click clipboard copy, .txt download, and draft review disclaimers.

- **Phase 7.4 (Database-Driven Interview Preparation)**: (**Complete**)
  - Shared PostgreSQL interview question bank with version-controlled, curated seed dataset (110 questions across 6 role families: General HR/Behavioural, Data Analyst, Data Scientist, AI/ML Engineer, Full-Stack Developer, General Software Engineering).
  - Zero-API default practice workflow: random sampling with duplicate avoidance, category/difficulty filtering, and graceful fallback to general questions for custom roles.
  - Deterministic local rubric feedback engine evaluating answers instantly without external network calls (word count, sentence count, completeness level, rubric point matching, STAR structure checks for behavioural questions, and engineering trade-offs).
  - Explicit, optional "Get AI Feedback (uses Gemini quota)" action with transparent error/fallback handling for quota exhaustion (HTTP 429), timeouts, or missing API keys.
  - Strict candidate privacy: student answers are practice-only and never persisted in the shared question bank or database tables.
  - Student-facing page `/interview-prep` with responsive stepper, live word/speaking-time counters, collapsible rubric points and guidance frameworks, and seamless opportunity cross-links.

- **Phase 7.5 (Job-Specific Resume Recommendations)**: (**Complete**)
  - Evidence-grounded analysis comparing authenticated student's active resume against any published opportunity.
  - Overview showing job metadata, active resume completeness score from Phase 4, and data sufficiency audit.
  - Categorized strengths (skills, projects, experience, education) displaying clear evidence and relevance explanations.
  - Requirement gaps distinguishing missing qualifications from unevidenced/incomplete data with actionable candidate advice (preventing unsupported claims of student inadequacy).
  - Actionable resume improvements: project/experience emphasis guidance, contextual keyword alignment, and grounded bullet rewrites targeting weak or metric-free lines.
  - Bullet rewrites strictly preserve factual accuracy, never invent technologies or metrics, and insert explicit bracketed metric placeholders (e.g., `[insert metric, e.g. X% improvement]`).
  - Dual-provider strategy: Gemini API with strict anti-hallucination rules and seamless deterministic fallback when unconfigured, rate-limited, or unavailable.
  - ATS-oriented structural and readability guidance (headings, single-column parsing, keyword distribution) with prominent disclaimers that CareerPilot AI does not fake proprietary ATS pass scores or guarantee hiring.
  - Document safety: active resume remains strictly unchanged during analysis; suggestions can be copied without automatic file modification.
  - Student page at `/resume-recommendations` with opportunity selector, verified active resume preview, interactive tabs, one-click copy actions, and seamless cross-links from dashboard and opportunity details.
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
