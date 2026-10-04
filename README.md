# CareerPilot AI

AI-powered career discovery and internship matching platform for college students and freshers.

## Overview

CareerPilot AI helps students discover relevant opportunities, understand their suitability, improve their resumes, and track their career progress — all powered by artificial intelligence.

## Tech Stack

| Layer          | Technology                                          |
|----------------|-----------------------------------------------------|
| Frontend       | Next.js 16, React 19, TypeScript, Tailwind CSS v4   |
| UI Components  | shadcn/ui (base-nova style)                         |
| Backend        | Python, FastAPI, SQLAlchemy 2.x                     |
| Database       | PostgreSQL (via Supabase)                           |
| Authentication | Supabase Auth                                       |
| AI/ML          | Scikit-learn, Sentence Transformers, Gemini API     |

## Project Structure

```
Careerpilot-Ai/
├── frontend/          # Next.js application
├── backend/           # FastAPI application
│   └── app/
│       ├── main.py          # App entry point
│       ├── core/            # Config, database, dependencies
│       ├── models/          # SQLAlchemy ORM models
│       ├── schemas/         # Pydantic request/response schemas
│       ├── routers/         # API route handlers
│       └── services/        # Business logic
├── docs/              # Project documentation
│   ├── requirements.md
│   ├── architecture.md
│   ├── database-schema.md
│   └── design-system.md
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- PostgreSQL (or a Supabase project)

### Frontend Setup

```bash
cd frontend
cp .env.example .env.local    # Configure environment variables
npm install
npm run dev                    # Starts on http://localhost:3000
```

### Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # Configure environment variables
python3 -m uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

## API Endpoints

| Method | Path      | Description          |
|--------|-----------|----------------------|
| GET    | `/`       | Welcome message      |
| GET    | `/health` | Health check         |

## Environment Variables

See `backend/.env.example` and `frontend/.env.example` for all required configuration.

## Documentation

- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [Database Schema](docs/database-schema.md)
- [Design System](docs/design-system.md)

## Development Status

**Current Phase:** Phase 1 — Project Foundation

| Phase | Description                                  | Status      |
|-------|----------------------------------------------|-------------|
| 1     | Project foundation, structure, design system | In Progress |
| 2     | Authentication, user profiles, database      | Planned     |
| 3     | Opportunity listing, search, filtering       | Planned     |
| 4     | AI matching engine, resume analysis          | Planned     |
| 5     | Dashboard, analytics, career insights        | Planned     |
| 6     | Polish, testing, deployment                  | Planned     |

## License

This project is private and not yet licensed for public distribution.