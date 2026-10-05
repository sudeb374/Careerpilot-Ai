# CareerPilot AI — Database Schema

> **Status:** Planning phase. Tables will be created incrementally as each feature phase begins.

## 1. Entity Relationship Overview

```
┌──────────┐       ┌──────────────┐       ┌─────────────────┐
│  users   │──1:N──│  profiles    │       │  opportunities  │
└──────────┘       └──────┬───────┘       └────────┬────────┘
                          │                        │
                          │ N:M                    │
                          ▼                        │
                   ┌──────────────┐                │
                   │ user_skills  │                │
                   └──────────────┘                │
                                                   │
                          ┌────────────────────────┘
                          ▼
                   ┌──────────────┐
                   │ applications │◄── tracks user applications
                   └──────────────┘

                   ┌──────────────┐
                   │  resumes     │── resume uploads & analysis results
                   └──────────────┘
```

## 2. Core Tables

### 2.1 users
Managed by Supabase Auth. The backend references the Supabase `auth.users` table via UUID.

| Column      | Type        | Constraints         | Notes                          |
|-------------|-------------|---------------------|--------------------------------|
| id          | UUID        | PK                  | From Supabase Auth             |
| email       | VARCHAR     | UNIQUE, NOT NULL    | From Supabase Auth             |
| created_at  | TIMESTAMPTZ | NOT NULL, DEFAULT   | From Supabase Auth             |

### 2.2 profiles
Extended user information stored in the application database.

| Column         | Type        | Constraints         | Notes                          |
|----------------|-------------|---------------------|--------------------------------|
| id             | UUID        | PK, DEFAULT gen     |                                |
| user_id        | UUID        | FK → users.id, UQ   | One profile per user           |
| full_name      | VARCHAR(255)| NOT NULL            |                                |
| headline       | VARCHAR(500)|                     | Short bio / tagline            |
| location       | VARCHAR(255)|                     |                                |
| created_at     | TIMESTAMPTZ | NOT NULL, DEFAULT   |                                |
| updated_at     | TIMESTAMPTZ | NOT NULL, DEFAULT   |                                |

### 2.2.1 educations
| Column         | Type        | Constraints             | Notes                          |
|----------------|-------------|-------------------------|--------------------------------|
| id             | UUID        | PK, DEFAULT gen         |                                |
| profile_id     | UUID        | FK → profiles.id        |                                |
| institution    | VARCHAR(255)| NOT NULL                |                                |
| degree         | VARCHAR(255)| NOT NULL                |                                |
| field_of_study | VARCHAR(255)|                         |                                |
| start_date     | DATE        |                         |                                |
| end_date       | DATE        |                         |                                |
| grade          | VARCHAR(50) |                         |                                |
| created_at     | TIMESTAMPTZ | NOT NULL, DEFAULT       |                                |
| updated_at     | TIMESTAMPTZ | NOT NULL, DEFAULT       |                                |

### 2.2.2 experiences
| Column         | Type        | Constraints             | Notes                          |
|----------------|-------------|-------------------------|--------------------------------|
| id             | UUID        | PK, DEFAULT gen         |                                |
| profile_id     | UUID        | FK → profiles.id        |                                |
| title          | VARCHAR(255)| NOT NULL                |                                |
| company        | VARCHAR(255)| NOT NULL                |                                |
| location       | VARCHAR(255)|                         |                                |
| description    | TEXT        |                         |                                |
| start_date     | DATE        |                         |                                |
| end_date       | DATE        |                         |                                |
| is_current     | BOOLEAN     | DEFAULT false           |                                |
| created_at     | TIMESTAMPTZ | NOT NULL, DEFAULT       |                                |
| updated_at     | TIMESTAMPTZ | NOT NULL, DEFAULT       |                                |

### 2.2.3 projects
| Column         | Type        | Constraints             | Notes                          |
|----------------|-------------|-------------------------|--------------------------------|
| id             | UUID        | PK, DEFAULT gen         |                                |
| profile_id     | UUID        | FK → profiles.id        |                                |
| name           | VARCHAR(255)| NOT NULL                |                                |
| description    | TEXT        |                         |                                |
| url            | VARCHAR(500)|                         |                                |
| start_date     | DATE        |                         |                                |
| end_date       | DATE        |                         |                                |
| created_at     | TIMESTAMPTZ | NOT NULL, DEFAULT       |                                |
| updated_at     | TIMESTAMPTZ | NOT NULL, DEFAULT       |                                |

### 2.2.4 career_preferences
| Column         | Type        | Constraints             | Notes                          |
|----------------|-------------|-------------------------|--------------------------------|
| id             | UUID        | PK, DEFAULT gen         |                                |
| profile_id     | UUID        | FK → profiles.id, UQ    | One preference per profile     |
| desired_roles  | VARCHAR(500)|                         |                                |
| locations      | VARCHAR(500)|                         |                                |
| job_type       | VARCHAR(100)|                         | e.g., full-time, internship    |
| created_at     | TIMESTAMPTZ | NOT NULL, DEFAULT       |                                |
| updated_at     | TIMESTAMPTZ | NOT NULL, DEFAULT       |                                |

### 2.3 opportunities
Internships and entry-level job listings.

| Column          | Type        | Constraints         | Notes                          |
|-----------------|-------------|---------------------|--------------------------------|
| id              | UUID        | PK, DEFAULT gen     |                                |
| title           | VARCHAR(500)| NOT NULL            |                                |
| company         | VARCHAR(255)| NOT NULL            |                                |
| description     | TEXT        |                     |                                |
| location        | VARCHAR(255)|                     |                                |
| type            | VARCHAR(50) |                     | internship / full-time / part-time |
| domain          | VARCHAR(100)|                     | engineering, design, etc.      |
| skills_required | JSONB       |                     | Array of skill strings         |
| stipend_min     | INTEGER     |                     |                                |
| stipend_max     | INTEGER     |                     |                                |
| duration_months | INTEGER     |                     |                                |
| apply_url       | TEXT        |                     |                                |
| is_active       | BOOLEAN     | DEFAULT true        |                                |
| source_name     | VARCHAR(100)|                     | Origin platform (e.g., "Internshala", "manual") |
| source_url      | TEXT        |                     | URL of the original listing    |
| external_id     | VARCHAR(255)|                     | ID from the source platform for deduplication |
| expires_at      | TIMESTAMPTZ |                     | When the listing expires       |
| last_verified_at| TIMESTAMPTZ |                     | Last time the listing was confirmed active |
| created_by      | UUID        | FK → users.id       | Admin or system user who created the listing |
| posted_at       | TIMESTAMPTZ | NOT NULL, DEFAULT   |                                |
| created_at      | TIMESTAMPTZ | NOT NULL, DEFAULT   |                                |

### 2.4 applications
Tracks which users applied to which opportunities.

| Column          | Type        | Constraints               | Notes                    |
|-----------------|-------------|---------------------------|--------------------------|
| id              | UUID        | PK, DEFAULT gen           |                          |
| user_id         | UUID        | FK → users.id, NOT NULL   |                          |
| opportunity_id  | UUID        | FK → opportunities.id, NOT NULL |                    |
| status          | VARCHAR(50) | DEFAULT 'interested'      | interested / applied / interviewing / offered / rejected |
| applied_at      | TIMESTAMPTZ |                           |                          |
| notes           | TEXT        |                           | User's private notes     |
| created_at      | TIMESTAMPTZ | NOT NULL, DEFAULT         |                          |
| updated_at      | TIMESTAMPTZ | NOT NULL, DEFAULT         |                          |
| UNIQUE          |             | (user_id, opportunity_id) | Prevents duplicate applications per user per opportunity |

### 2.5 resumes
Resume uploads and AI analysis results.

| Column          | Type        | Constraints               | Notes                    |
|-----------------|-------------|---------------------------|--------------------------|
| id              | UUID        | PK, DEFAULT gen           |                          |
| user_id         | UUID        | FK → users.id, NOT NULL   |                          |
| filename        | VARCHAR(255)| NOT NULL                  |                          |
| file_url        | TEXT        | NOT NULL                  | Storage path / URL       |
| score           | FLOAT       |                           | AI-generated score (0–100) |
| analysis        | JSONB       |                           | Structured feedback      |
| created_at      | TIMESTAMPTZ | NOT NULL, DEFAULT         |                          |

### 2.6 skills (Global)
Global list of skills to avoid duplication.

| Column          | Type        | Constraints               | Notes                    |
|-----------------|-------------|---------------------------|--------------------------|
| id              | UUID        | PK, DEFAULT gen           |                          |
| name            | VARCHAR(100)| UNIQUE, NOT NULL          |                          |
| created_at      | TIMESTAMPTZ | NOT NULL, DEFAULT         |                          |

### 2.7 profile_skills
Skills associated with a user profile.

| Column          | Type        | Constraints               | Notes                    |
|-----------------|-------------|---------------------------|--------------------------|
| id              | UUID        | PK, DEFAULT gen           |                          |
| profile_id      | UUID        | FK → profiles.id, NOT NULL|                          |
| skill_id        | UUID        | FK → skills.id, NOT NULL  |                          |
| proficiency     | VARCHAR(50) |                           | beginner / intermediate / advanced |
| UNIQUE          |             | (profile_id, skill_id)    |                          |

## 3. Indexes (Planned)

- `profiles.user_id` — unique index for fast profile lookup
- `opportunities.domain` — filter by domain
- `opportunities.is_active` — filter active listings
- `opportunities(source_name, external_id)` — composite index for deduplication during ingestion
- `applications(user_id, opportunity_id)` — **unique composite constraint**, prevents duplicate applications
- `resumes.user_id` — list resumes by user

## 4. Resume Storage — Privacy and Security

Resume files contain sensitive personal information (PII). The following considerations apply:

### 4.1 Access Control
- Resume files must only be accessible to the owning user and authorized system processes (e.g., AI analysis).
- API endpoints serving resume data must validate that the requesting user owns the resource.
- Admin access to raw resume files should be restricted and auditable.

### 4.2 Storage
- Resume files should be stored in a private storage bucket (e.g., Supabase Storage with RLS policies), never in a publicly accessible location.
- File URLs must be signed/temporary and expire after a short duration.
- Stored files should be encrypted at rest.

### 4.3 Retention and Deletion
- Users must be able to delete their uploaded resumes at any time.
- Deleting a resume must remove both the file from storage and the corresponding database record (including any cached analysis results).
- A data retention policy should be defined before production launch (e.g., auto-delete resumes after 12 months of inactivity).
- Account deletion must cascade to all associated resume files and analysis data.

### 4.4 AI Analysis Data
- AI-generated analysis (scores, feedback) stored in the `analysis` JSONB column must be deleted when the parent resume record is deleted.
- Analysis results must not be shared with other users or third parties.
- The `score` field is a heuristic recommendation and must not be presented as a probability of hiring success (see requirements.md § 6).

## 5. Notes

- All timestamps use `TIMESTAMPTZ` (timezone-aware).
- JSONB columns allow flexible nested data without excessive normalization.
- UUIDs are used as primary keys throughout for Supabase compatibility.
- This schema will be implemented incrementally using SQLAlchemy models and Alembic migrations starting in Phase 2.
- The `source_name`, `source_url`, and `external_id` fields on opportunities support authorized automated ingestion (Phase 6) and deduplication.
