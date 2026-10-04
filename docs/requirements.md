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
| 1     | Project foundation, structure, design system           | In Progress |
| 2     | Authentication and student profiles                    | Planned     |
| 3     | Opportunity management                                 | Planned     |
| 4     | Resume intelligence                                    | Planned     |
| 5     | AI matching engine                                     | Planned     |
| 6     | Authorized automated ingestion                         | Planned     |
| 7     | Career copilot                                         | Planned     |
| 8     | Application tracker                                    | Planned     |
| 9     | Testing and evaluation                                 | Planned     |
| 10    | Deployment and presentation                            | Planned     |

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
