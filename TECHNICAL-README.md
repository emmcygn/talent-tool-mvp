# talent-tool-mvp -- Technical README

> Product stakeholders: see [README.md](README.md) for the product overview, persona journeys, and demo access.

---

## Architecture

```mermaid
graph TB
    subgraph Frontend ["Frontend (Next.js 16 / TypeScript)"]
        FE1[Mind Views -- /mind/*]
        FE2[Mothership Views -- /mothership/*]
        FE3[Shared Components -- shadcn/ui + custom]
        FE4[API Client -- typed fetch]
        FE5[Supabase Client -- auth + realtime]
    end

    subgraph Backend ["Backend (FastAPI / Python 3.12)"]
        BE1[REST API -- api/]
        BE2[Adapters -- Bullhorn, HubSpot, LinkedIn]
        BE3[Pipelines -- ingest, normalize, dedup, enrich]
        BE4[Matching -- structured + semantic + explainer]
        BE5[Copilot -- NL parser + executor + formatter]
        BE6[Signals -- event tracking + analytics]
        BE7[Services -- handoffs, quotes, collections]
    end

    subgraph Data ["Data Layer (Supabase)"]
        DB[(PostgreSQL + pgvector)]
        AUTH[Auth + RLS]
        RT[Realtime Subscriptions]
    end

    subgraph AI ["AI Services"]
        LLM[OpenAI GPT-4o]
        EMB[text-embedding-3-small]
    end

    Frontend -->|REST| Backend
    Frontend -->|Auth + Realtime| Data
    Backend --> Data
    Backend --> AI
```

The data flow through the system:

```
Adapters --> Ingest --> Normalize --> Deduplicate --> Enrich (LLM + embeddings)
    --> Match (structured + semantic + composite) --> Explain (LLM) --> Display (UI)
```

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend | Next.js (App Router) | 16.x |
| Language (FE) | TypeScript | 5.x |
| Styling | Tailwind CSS + shadcn/ui | 4.x / latest |
| Backend | FastAPI | 0.115+ |
| Language (BE) | Python | 3.12 |
| Database | PostgreSQL via Supabase | 15+ |
| Vector Search | pgvector | 0.7+ |
| Auth | Supabase Auth (JWT + RLS) | -- |
| Realtime | Supabase Realtime | -- |
| LLM | OpenAI GPT-4o | -- |
| Embeddings | OpenAI text-embedding-3-small | -- |
| Contracts | Pydantic (Python) / TypeScript types | v2 |

---

## Project Structure

```
recruittech/
├── backend/                        # Python -- Mothership engine
│   ├── api/                        # FastAPI routes
│   │   ├── candidates.py           # Candidate CRUD + search
│   │   ├── roles.py                # Role CRUD + matching triggers
│   │   ├── matches.py              # Match results + explanations
│   │   ├── collections.py          # Collection management
│   │   ├── handoffs.py             # Handoff lifecycle
│   │   ├── quotes.py               # Quote generation
│   │   ├── copilot.py              # Natural language query endpoint
│   │   ├── signals.py              # Event stream / analytics
│   │   ├── admin.py                # Admin-only endpoints
│   │   └── auth.py                 # Auth helpers
│   ├── adapters/                   # Source integrations (mocked)
│   │   ├── base.py                 # Abstract adapter interface
│   │   ├── bullhorn.py             # Bullhorn ATS adapter
│   │   ├── hubspot.py              # HubSpot CRM adapter
│   │   └── linkedin.py             # LinkedIn Recruiter adapter
│   ├── contracts/                  # Canonical data contracts (Pydantic v2)
│   │   ├── candidate.py            # Candidate canonical model
│   │   ├── role.py                 # Role canonical model
│   │   ├── match.py                # Match result model
│   │   ├── signal.py               # Signal event model
│   │   └── shared.py               # Shared enums, value objects
│   ├── pipelines/                  # ETL/ELT
│   │   ├── ingest.py               # Raw data ingestion
│   │   ├── normalize.py            # Map adapter output to canonical
│   │   ├── deduplicate.py          # Identity resolution + dedup
│   │   └── enrich.py               # AI extraction + embedding generation
│   ├── matching/                   # Hybrid AI matching
│   │   ├── structured.py           # Filter by structured fields
│   │   ├── semantic.py             # pgvector similarity search
│   │   ├── scorer.py               # Composite scoring (40/35/25)
│   │   └── explainer.py            # LLM-generated match explanations
│   ├── copilot/                    # Natural language query layer
│   │   ├── parser.py               # NL to structured query translation
│   │   ├── executor.py             # Query execution against data
│   │   └── formatter.py            # Response formatting with actions
│   ├── signals/                    # Event tracking + recommendations
│   │   ├── tracker.py              # Event emission
│   │   ├── triggers.py             # Notification triggers
│   │   └── analytics.py            # Aggregate analytics queries
│   ├── services/                   # Business logic
│   │   ├── handoff.py              # Handoff lifecycle management
│   │   ├── quote.py                # Quote generation logic
│   │   └── collection.py           # Collection management
│   ├── seed/                       # Demo data generation
│   │   ├── candidates.py           # 50+ realistic UK-market candidates
│   │   ├── roles.py                # 15+ roles across sectors
│   │   ├── organisations.py        # 10+ client companies
│   │   └── users.py                # Demo users for each persona
│   ├── tests/                      # pytest test suite
│   ├── config.py                   # App configuration
│   ├── main.py                     # FastAPI app entry point
│   ├── Dockerfile                  # Backend container
│   └── requirements.txt            # Python dependencies
├── frontend/                       # Next.js -- Mind + Mothership UI
│   ├── app/
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # Landing / login
│   │   ├── mind/                   # Client / Hiring Manager views
│   │   │   ├── layout.tsx          # Mind layout (minimal chrome)
│   │   │   ├── dashboard/          # Client dashboard
│   │   │   ├── roles/              # Post + manage roles
│   │   │   ├── candidates/         # Browse matched candidates
│   │   │   ├── quotes/             # Quote requests + status
│   │   │   └── pipeline/           # Hiring pipeline kanban
│   │   └── mothership/             # Talent Partner + Admin views
│   │       ├── layout.tsx          # Mothership layout (sidebar + copilot)
│   │       ├── dashboard/          # Partner dashboard
│   │       ├── candidates/         # Candidate ingestion + management
│   │       ├── matching/           # Match results + exploration
│   │       ├── collections/        # Collection management
│   │       ├── handoffs/           # Handoff inbox/outbox
│   │       ├── copilot/            # Copilot conversation view
│   │       ├── admin/              # Admin-only views
│   │       │   ├── analytics/      # Platform analytics + funnels
│   │       │   ├── quality/        # Data quality + dedup review
│   │       │   ├── adapters/       # Adapter health + management
│   │       │   └── users/          # User management
│   │       └── demo/               # Guided demo walkthrough
│   ├── components/
│   │   ├── ui/                     # shadcn/ui primitives
│   │   ├── mind/                   # Mind-specific components
│   │   ├── mothership/             # Mothership-specific components
│   │   └── shared/                 # Cross-product components
│   ├── lib/
│   │   ├── api.ts                  # Typed API client
│   │   ├── supabase.ts             # Supabase client + auth helpers
│   │   ├── types.ts                # TypeScript canonical types
│   │   └── utils.ts                # Shared utilities
│   ├── package.json
│   └── tsconfig.json
├── contracts/
│   └── canonical.ts                # TypeScript mirror of Python contracts
├── supabase/
│   ├── migrations/                 # Database migrations
│   ├── seed.sql                    # Seed data SQL
│   └── config.toml                 # Supabase project config
├── plans/                          # Agent orchestration framework
│   ├── ORCHESTRATOR.md             # Master orchestration protocol
│   ├── BOOTSTRAP.md                # Pre-flight checklist
│   ├── STATE.md                    # Progress tracker
│   ├── HANDOFF.md                  # Inter-agent communication log
│   ├── ISSUES.md                   # Cross-agent issue tracker
│   ├── agent-a/                    # Data Engineer task plans (task-01 to task-16)
│   └── agent-b/                    # Product Engineer task plans (task-01 to task-16)
├── tasks/
│   ├── todo.md                     # Task backlog
│   └── lessons.md                  # Shared lessons learned
├── CLAUDE.md                       # Agent instructions and conventions
├── docker-compose.yml              # Local dev (Supabase + backend)
├── README.md                       # Product README (non-technical)
└── TECHNICAL-README.md             # This file
```

---

## Prerequisites

- **Python** 3.12+
- **Node.js** 20+ and npm
- **Docker** and Docker Compose (for local Supabase)
- **Supabase CLI** (optional, for migration management)
- **OpenAI API key** (for AI features)
- A Supabase project (or use the Docker Compose local setup)

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/emmcygn/talent-tool-mvp.git
cd talent-tool-mvp
```

### 2. Start the database (Supabase via Docker)

```bash
docker-compose up -d
```

This starts a local Supabase instance with PostgreSQL + pgvector, Auth, and Realtime.

### 3. Set up the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Set up the frontend

```bash
cd frontend
npm install
```

### 5. Configure environment variables

Create `.env` files in both `backend/` and `frontend/` directories (see Environment Variables section below).

### 6. Run database migrations and seed data

```bash
# Apply migrations
cd supabase
supabase db push

# Seed demo data
cd ../backend
python -m seed.run
```

### 7. Start development servers

In separate terminals:

```bash
# Terminal 1: Backend API
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

The frontend runs at `http://localhost:3000` and the backend API at `http://localhost:8000`.

---

## Environment Variables

### Backend (`backend/.env`)

```bash
# Supabase
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# App
APP_ENV=development
CORS_ORIGINS=http://localhost:3000
```

### Frontend (`frontend/.env.local`)

```bash
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Database Setup

The database uses Supabase (PostgreSQL) with the pgvector extension for semantic search. Key tables:

| Table | Purpose |
|---|---|
| `candidates` | Candidate profiles with structured extracted data |
| `roles` | Job roles with extracted requirements |
| `matches` | AI-generated match results with scoring breakdown |
| `collections` | Themed candidate groups with sharing controls |
| `handoffs` | Partner-to-partner candidate referrals |
| `quotes` | Introduction pricing with pool discounts |
| `signals` | Event stream for analytics and recommendations |
| `organisations` | Client companies |
| `users` | Platform users with role-based access |

Row-Level Security (RLS) policies enforce access control at the database level:

- `talent_partner` -- own candidates + shared collections + received handoffs
- `client` -- own roles + matched candidates (anonymized) + own quotes
- `admin` -- full platform access

---

## Running Tests

```bash
# Backend tests
cd backend
python -m pytest -v

# Frontend build + lint validation
cd frontend
npm run build
npm run lint

# Full validation gate (must pass before completing any task)
cd backend && python -m pytest -v && cd ../frontend && npm run build && npm run lint
```

---

## Deployment

The live demo is deployed to:

| Service | Platform | URL |
|---|---|---|
| Frontend | Vercel | [talent-tool-mvp.vercel.app](https://talent-tool-mvp.vercel.app) |
| Backend | Railway | [talent-tool-mvp-production.up.railway.app](https://talent-tool-mvp-production.up.railway.app) |
| Database | Supabase Cloud | Managed PostgreSQL + pgvector |

### Deploy Backend to Railway

```bash
# Railway auto-deploys from the backend/ directory
# Dockerfile is at backend/Dockerfile
railway up
```

### Deploy Frontend to Vercel

```bash
cd frontend
vercel --prod
```

Set the environment variables in each platform's dashboard before deploying.

---

## API Documentation

FastAPI auto-generates interactive API docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Path | Description |
|---|---|---|
| **Candidates** | | |
| `GET` | `/api/candidates` | List candidates with filtering and pagination |
| `POST` | `/api/candidates` | Create a candidate (triggers AI extraction) |
| `GET` | `/api/candidates/{id}` | Get candidate detail with full profile |
| `POST` | `/api/candidates/upload` | Upload CV for AI extraction |
| `POST` | `/api/candidates/search` | Semantic search across candidates |
| **Roles** | | |
| `GET` | `/api/roles` | List roles with status filter |
| `POST` | `/api/roles` | Create a role (triggers requirement extraction) |
| `GET` | `/api/roles/{id}` | Get role detail with extracted requirements |
| `POST` | `/api/roles/{id}/match` | Trigger matching for a role |
| **Matches** | | |
| `GET` | `/api/matches` | List matches with filtering |
| `GET` | `/api/matches/{id}` | Get match detail with full explanation |
| `PATCH` | `/api/matches/{id}/status` | Update match status (shortlist, dismiss) |
| **Collections** | | |
| `GET` | `/api/collections` | List own + shared collections |
| `POST` | `/api/collections` | Create a collection |
| `POST` | `/api/collections/{id}/candidates` | Add candidates to collection |
| `PATCH` | `/api/collections/{id}/visibility` | Update sharing settings |
| **Handoffs** | | |
| `GET` | `/api/handoffs` | List handoff inbox/outbox |
| `POST` | `/api/handoffs` | Create a handoff to another partner |
| `PATCH` | `/api/handoffs/{id}/respond` | Accept or decline a handoff |
| **Quotes** | | |
| `POST` | `/api/quotes` | Generate a quote for intro request |
| `PATCH` | `/api/quotes/{id}/status` | Accept or decline a quote |
| **Copilot** | | |
| `POST` | `/api/copilot/query` | Submit a natural language query |
| **Signals** | | |
| `GET` | `/api/signals` | List signal events (activity feed) |
| `GET` | `/api/signals/analytics` | Aggregate analytics (funnels, trends) |
| **Admin** | | |
| `GET` | `/api/admin/stats` | Platform-wide statistics |
| `GET` | `/api/admin/adapters` | Adapter health status |
| `GET` | `/api/admin/dedup-queue` | Pending dedup reviews |
| `GET` | `/api/admin/pipeline` | AI pipeline monitoring |
| **Auth** | | |
| `POST` | `/api/auth/login` | Authenticate and get JWT |
| `GET` | `/api/auth/me` | Get current user profile |

---

## Agent Architecture

This project was built using the **agents-scaffolding** framework with two autonomous AI agents executing in parallel. The full orchestration protocol and task plans live in the `plans/` directory.

### Agent Roles

| Agent | Role | Owns | Plans |
|---|---|---|---|
| **Agent A** | Data Engineer | `backend/`, `supabase/`, `docker-compose.yml` | `plans/agent-a/task-01.md` through `task-16.md` |
| **Agent B** | Product Engineer | `frontend/`, `contracts/canonical.ts` | `plans/agent-b/task-01.md` through `task-16.md` |

### Orchestration Files

| File | Purpose |
|---|---|
| `plans/ORCHESTRATOR.md` | Master orchestration protocol -- task sequencing, dependency graph, execution rules |
| `plans/BOOTSTRAP.md` | Pre-flight checklist run before any work begins |
| `plans/STATE.md` | Progress tracker -- each task's status, timestamps, completion notes |
| `plans/HANDOFF.md` | Inter-agent communication log -- what one agent needs to tell the other |
| `plans/ISSUES.md` | Cross-agent issue tracker -- blocking problems that need the other agent's attention |

### Contract Boundary

The canonical data contracts are the interface between agents:

- **Agent A** writes `backend/contracts/*.py` (Pydantic v2 models) -- the single source of truth for all data shapes
- **Agent B** writes `contracts/canonical.ts` (TypeScript types) -- mirrors the Python contracts for frontend consumption
- Agent A's API endpoints accept and return these contract shapes
- Agent B's frontend consumes them via the typed API client in `frontend/lib/api.ts`

Agent B can build UI against the contract types before Agent A's endpoints are live, using mocked responses that conform to the contracts.

### Execution Protocol

Each agent follows this loop:

1. Check `plans/ISSUES.md` for open issues assigned to them
2. Read `plans/STATE.md` to find next `not_started` task
3. Verify dependencies are marked `completed`
4. Read the task file (fully self-contained with checklist, implementation details, acceptance criteria)
5. Implement, validate against acceptance criteria
6. Run the validation gate (`pytest` + `npm run build` + `npm run lint`)
7. Update `STATE.md`, write `HANDOFF.md` entry if needed
8. Commit with message format: `Agent {A|B} Task {XX}: {title}`
9. Loop

---

## Contributing

1. Read `CLAUDE.md` for project conventions and the agent execution model
2. Read `plans/ORCHESTRATOR.md` for the orchestration protocol
3. Check `plans/STATE.md` for current progress and available tasks
4. Follow the task execution protocol described above
5. Run the full validation gate before marking any task complete:
   ```bash
   cd backend && python -m pytest -v
   cd frontend && npm run build && npm run lint
   ```
6. Commit with descriptive messages following the `Agent {A|B} Task {XX}: {title}` format
