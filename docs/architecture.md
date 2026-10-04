# CareerPilot AI — Architecture

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                        │
│                   Next.js 16 + React 19 + TailwindCSS v4        │
│                        shadcn/ui (base-nova)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │  HTTPS / REST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend API Server                         │
│                   FastAPI + Uvicorn (Python)                     │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────────┐  │
│  │  Routers │→ │ Services │→ │  Models   │  │ Core (config, │  │
│  │ (API     │  │ (business│  │ (SQLAlch- │  │  database,    │  │
│  │  routes) │  │  logic)  │  │  emy ORM) │  │  deps)        │  │
│  └──────────┘  └──────────┘  └─────┬─────┘  └───────────────┘  │
└────────────────────────────────────┬────────────────────────────┘
                                     │  SQL (psycopg)
                                     ▼
                        ┌────────────────────────┐
                        │      PostgreSQL         │
                        │     (via Supabase)       │
                        └────────────────────────┘

              ┌──────────────────────────────────────┐
              │          External Services            │
              │                                       │
              │  • Supabase Auth (JWT-based auth)     │
              │  • Gemini API (AI/ML inference)        │
              │  • Sentence Transformers (embeddings)  │
              └──────────────────────────────────────┘
```

## 2. Frontend Architecture

```
frontend/
├── app/                    # Next.js App Router pages & layouts
│   ├── layout.tsx          # Root layout (fonts, metadata, providers)
│   ├── page.tsx            # Landing page
│   ├── globals.css         # Tailwind v4 theme & global styles
│   └── (dashboard)/        # Dashboard route group (future)
├── components/
│   ├── ui/                 # shadcn/ui primitives (Button, Card, etc.)
│   └── [feature]/          # Feature-specific components
├── lib/
│   ├── utils.ts            # Utility functions (cn, formatters)
│   └── api.ts              # Backend API client (future)
├── hooks/                  # Custom React hooks
├── types/                  # Shared TypeScript type definitions
└── public/                 # Static assets
```

## 3. Backend Architecture

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI app instance, middleware, router mounts
│   ├── core/
│   │   ├── config.py       # Pydantic Settings (env loading)
│   │   ├── database.py     # SQLAlchemy engine & session factory
│   │   └── dependencies.py # FastAPI dependency injection
│   ├── models/
│   │   └── base.py         # SQLAlchemy declarative base
│   ├── schemas/            # Pydantic request/response models
│   ├── routers/            # API route handlers
│   └── services/           # Business logic layer
├── tests/                  # Pytest test suite
├── requirements.txt
├── .env.example
└── .gitignore
```

## 4. Key Design Decisions

| Decision                    | Rationale                                                    |
|-----------------------------|--------------------------------------------------------------|
| Next.js App Router          | Server components, streaming, built-in routing               |
| FastAPI                     | Async-first Python, auto-generated OpenAPI docs, type safety |
| SQLAlchemy 2.x              | Modern async support, mature ORM, wide PostgreSQL support    |
| psycopg 3                   | Native async PostgreSQL driver, better performance           |
| Supabase Auth               | Managed auth with JWT, avoids building auth from scratch     |
| Pydantic Settings           | Type-safe configuration from environment variables           |
| shadcn/ui (base-nova)       | Accessible, composable, fully customizable components        |
| Tailwind CSS v4             | CSS-first config, native cascade layers, improved DX         |

## 5. Communication Patterns

- **Frontend → Backend:** REST API calls over HTTP. In development, Next.js rewrites proxy `/api/v1/*` to `localhost:8000`.
- **Backend → Database:** SQLAlchemy ORM with psycopg async driver.
- **Backend → AI Services:** Direct HTTP calls to Gemini API; local inference for Sentence Transformers.
- **Auth flow:** Supabase client-side SDK → JWT → Backend validates JWT on protected routes.

## 6. Security Considerations

- All secrets stored in environment variables, never committed
- CORS restricted to known frontend origins
- JWT validation on protected endpoints
- Input validation via Pydantic schemas
- SQL injection prevention via ORM parameterized queries
- Rate limiting on AI-powered endpoints (future phase)
