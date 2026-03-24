# RecruitTech PoC Implementation Plan

> **For agentic workers:** This plan is designed for the `agents-scaffolding` dual-agent framework. Agent A and Agent B execute their task files autonomously in parallel. See `plans/ORCHESTRATOR.md` for the execution protocol, `plans/STATE.md` for progress tracking.

**Goal:** Build a polished recruitment platform PoC mirroring the Mind + Mothership architecture, demonstrating AI matching, copilot dashboards, and multi-persona workflows for a UK recruitment practice.

**Architecture:** Monorepo with FastAPI Python backend (Mothership engine) and Next.js TypeScript frontend (Mind + Mothership UI). Supabase provides PostgreSQL + pgvector + Auth + Realtime + RLS. Dual autonomous agents split on data/backend (Agent A) vs UI/frontend (Agent B) with canonical data contracts as the interface boundary.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, OpenAI API, Supabase (PostgreSQL + pgvector), Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, Recharts

**Spec:** `docs/superpowers/specs/2026-03-24-recruittech-design.md`

---

## Agent Roles

### Agent A — Data Engineer (Mothership Brain)
**Owns:** `backend/`, `supabase/`, `contracts/canonical.py` (doesn't exist — contracts live in `backend/contracts/`), `docker-compose.yml`, `seed/`
**Focus:** Data contracts, database schema, API endpoints, AI pipeline, copilot, signals, seed data

### Agent B — Product Engineer (Mind + Mothership UI)
**Owns:** `frontend/`, `contracts/canonical.ts`
**Focus:** All UI views, components, layouts, API client, realtime subscriptions, demo mode, polish

### Shared Interface Boundary
- Agent A: `backend/contracts/*.py` (Pydantic models — source of truth)
- Agent B: `contracts/canonical.ts` (TypeScript mirror)
- Agent A commits contracts first on Task 01. Agent B mirrors on their Task 01.

---

## File Map

### Agent A Files

```
backend/
├── main.py                          # FastAPI app, CORS, router includes
├── config.py                        # Settings (Supabase URL, OpenAI key, etc.)
├── requirements.txt                 # Python dependencies
├── contracts/
│   ├── __init__.py
│   ├── shared.py                    # Enums, value objects (SeniorityLevel, etc.)
│   ├── candidate.py                 # Candidate canonical model
│   ├── role.py                      # Role canonical model
│   ├── match.py                     # Match result model
│   ├── signal.py                    # Signal event model
│   ├── handoff.py                   # Handoff model
│   ├── quote.py                     # Quote model
│   └── collection.py               # Collection model
├── api/
│   ├── __init__.py
│   ├── auth.py                      # Auth helpers, role extraction from JWT
│   ├── candidates.py                # Candidate CRUD + search
│   ├── roles.py                     # Role CRUD + match trigger
│   ├── matches.py                   # Match results + explanations
│   ├── collections.py               # Collection management
│   ├── handoffs.py                  # Handoff lifecycle
│   ├── quotes.py                    # Quote generation
│   ├── copilot.py                   # NL query endpoint (streaming)
│   ├── signals.py                   # Signal event stream + analytics
│   └── admin.py                     # Admin-only endpoints
├── adapters/
│   ├── __init__.py
│   ├── base.py                      # Abstract adapter interface
│   ├── bullhorn.py                  # Bullhorn mock adapter
│   ├── hubspot.py                   # HubSpot mock adapter
│   └── linkedin.py                  # LinkedIn mock adapter
├── pipelines/
│   ├── __init__.py
│   ├── ingest.py                    # Raw data ingestion from adapters
│   ├── normalize.py                 # Adapter output → canonical format
│   ├── deduplicate.py               # Identity resolution + dedup
│   └── enrich.py                    # AI extraction + embedding generation
├── matching/
│   ├── __init__.py
│   ├── structured.py                # Structured field filtering
│   ├── semantic.py                  # pgvector similarity search
│   ├── scorer.py                    # Composite scoring (40/35/25)
│   └── explainer.py                 # LLM match explanations
├── copilot/
│   ├── __init__.py
│   ├── parser.py                    # NL → structured query
│   ├── executor.py                  # Query execution
│   └── formatter.py                 # Response formatting + actions
├── signals/
│   ├── __init__.py
│   ├── tracker.py                   # Signal event emission
│   ├── triggers.py                  # Action triggers (notifications)
│   └── analytics.py                 # Aggregate analytics queries
├── services/
│   ├── __init__.py
│   ├── handoff.py                   # Handoff business logic
│   ├── quote.py                     # Quote generation logic
│   └── collection.py               # Collection management logic
├── seed/
│   ├── __init__.py
│   ├── generate.py                  # Master seed script
│   ├── candidates.py                # 50+ realistic candidates
│   ├── roles.py                     # 15+ realistic roles
│   ├── organisations.py             # 10+ client companies
│   └── users.py                     # Demo users per persona
└── tests/
    ├── __init__.py
    ├── test_contracts.py            # Contract validation
    ├── test_pipelines.py            # Pipeline unit tests
    ├── test_matching.py             # Matching engine tests
    ├── test_copilot.py              # Copilot query tests
    ├── test_api.py                  # API endpoint tests
    └── conftest.py                  # Shared fixtures

supabase/
├── config.toml                      # Supabase project config
├── migrations/
│   └── 001_initial_schema.sql       # Full schema + pgvector + RLS
└── seed.sql                         # Seed data SQL (generated from Python seed/)

docker-compose.yml                   # Supabase local + backend
```

### Agent B Files

```
frontend/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.ts
├── app/
│   ├── layout.tsx                   # Root layout + providers
│   ├── page.tsx                     # Landing → login redirect
│   ├── login/
│   │   └── page.tsx                 # Demo login (one-click per persona)
│   ├── mind/
│   │   ├── layout.tsx               # Mind shell (minimal nav)
│   │   ├── dashboard/
│   │   │   └── page.tsx             # Client dashboard
│   │   ├── roles/
│   │   │   ├── page.tsx             # Role list
│   │   │   └── new/
│   │   │       └── page.tsx         # Guided role posting wizard
│   │   ├── candidates/
│   │   │   └── page.tsx             # Browse matched candidates
│   │   ├── quotes/
│   │   │   └── page.tsx             # Quote requests + status
│   │   └── pipeline/
│   │       └── page.tsx             # Hiring pipeline kanban
│   └── mothership/
│       ├── layout.tsx               # Mothership shell (sidebar + copilot)
│       ├── dashboard/
│       │   └── page.tsx             # Talent partner dashboard
│       ├── candidates/
│       │   ├── page.tsx             # Candidate list + management
│       │   └── new/
│       │       └── page.tsx         # CV upload + extraction
│       ├── matching/
│       │   └── page.tsx             # Match results exploration
│       ├── collections/
│       │   └── page.tsx             # Collection management
│       ├── handoffs/
│       │   └── page.tsx             # Handoff inbox/outbox
│       ├── copilot/
│       │   └── page.tsx             # Copilot full-page view
│       └── admin/
│           ├── layout.tsx           # Admin sub-layout
│           ├── analytics/
│           │   └── page.tsx         # Platform analytics + funnels
│           ├── quality/
│           │   └── page.tsx         # Dedup review queue
│           ├── adapters/
│           │   └── page.tsx         # Adapter health
│           └── users/
│               └── page.tsx         # User management
├── components/
│   ├── ui/                          # shadcn/ui primitives (auto-generated)
│   ├── shared/
│   │   ├── candidate-card.tsx       # Candidate display card
│   │   ├── match-card.tsx           # Match result with explanation
│   │   ├── skill-chips.tsx          # Skill tag chips (green/amber/grey)
│   │   ├── confidence-badge.tsx     # Strong/Good/Possible badge
│   │   ├── data-table.tsx           # Reusable data table
│   │   ├── kanban-board.tsx         # Reusable kanban
│   │   ├── empty-state.tsx          # Empty state with hints
│   │   ├── loading-skeleton.tsx     # Skeleton loaders
│   │   └── notification-toast.tsx   # Toast system
│   ├── mind/
│   │   ├── role-wizard.tsx          # Step-by-step role posting
│   │   ├── quote-display.tsx        # Quote breakdown card
│   │   └── recommendation-card.tsx  # Proactive suggestion card
│   ├── mothership/
│   │   ├── copilot-sidebar.tsx      # Copilot conversation panel
│   │   ├── copilot-message.tsx      # Single copilot message
│   │   ├── extraction-viewer.tsx    # Real-time extraction animation
│   │   ├── dedup-comparison.tsx     # Side-by-side dedup view
│   │   ├── handoff-card.tsx         # Handoff inbox item
│   │   ├── collection-card.tsx      # Collection summary card
│   │   ├── adapter-status.tsx       # Adapter health card
│   │   └── signal-feed.tsx          # Activity feed component
│   └── charts/
│       ├── funnel-chart.tsx         # Pipeline funnel visualization
│       ├── trend-chart.tsx          # Time-series line chart
│       └── skill-cloud.tsx          # Trending skills visualization
├── lib/
│   ├── api.ts                       # Typed API client
│   ├── supabase.ts                  # Supabase client + auth
│   ├── types.ts                     # Re-exports from canonical.ts
│   └── utils.ts                     # Helpers (formatting, etc.)
└── contracts/
    └── canonical.ts                 # TypeScript canonical types

contracts/
└── canonical.ts                     # Symlink or copy — same file
```

---

## Task Breakdown

### Agent A Tasks (16 tasks)

| # | Title | Day | Depends On | Description |
|---|-------|-----|------------|-------------|
| 01 | Bootstrap: Project structure + contracts | 1 | — | PAIR. Monorepo init, Python project, canonical Pydantic contracts, shared enums |
| 02 | Supabase schema + migrations | 1 | A-01 | Full database schema with pgvector, RLS policies, Supabase config |
| 03 | FastAPI skeleton + auth | 1 | A-02 | App entry point, CORS, auth helpers, health check endpoint |
| 04 | Adapter interfaces + mocks | 2 | A-01 | Abstract adapter, Bullhorn/HubSpot/LinkedIn mocks with realistic data |
| 05 | Ingest + normalize pipeline | 2 | A-02, A-04 | ETL: adapter → raw → canonical format |
| 06 | Deduplication pipeline | 2 | A-05 | Identity resolution: exact, fuzzy, semantic matching + merge logic |
| 07 | AI extraction pipeline | 2 | A-03, A-05 | LLM skill extraction + embedding generation + confidence scoring |
| 08 | Candidate + Role CRUD endpoints | 3 | A-03, A-07 | Full CRUD for candidates and roles with search |
| 09 | Structured + semantic matching | 3 | A-07 | Structured filters, pgvector search, composite scorer |
| 10 | Match explanation generator | 3 | A-09 | LLM explanations, strengths/gaps, confidence levels |
| 11 | Match + Collection endpoints | 3 | A-09, A-10 | Match results API, collection CRUD |
| 12 | Signal tracking + analytics | 4 | A-03 | Event emission, aggregate queries, funnel data |
| 13 | Handoff + Quote endpoints | 4 | A-08, A-12 | Handoff lifecycle, quote generation with pool pricing |
| 14 | Copilot query layer | 4 | A-08, A-09 | NL parser, query executor, response formatter (streaming) |
| 15 | Admin endpoints + monitoring | 5 | A-12 | Platform stats, adapter health, pipeline monitoring, dedup review |
| 16 | Seed data + final integration | 5-6 | A-01..A-15 | 50+ candidates, 15+ roles, pre-generated matches, signal history |

### Agent B Tasks (16 tasks)

| # | Title | Day | Depends On | Description |
|---|-------|-----|------------|-------------|
| 01 | Bootstrap: Next.js + TypeScript contracts | 1 | A-01 | PAIR. Next.js init, Tailwind, shadcn/ui, TS canonical types from Python contracts |
| 02 | Layout shells + auth flow | 1 | B-01 | Root layout, Mind layout, Mothership layout, Supabase auth, demo login |
| 03 | Shared UI components (batch 1) | 2 | B-01 | candidate-card, match-card, skill-chips, confidence-badge, loading-skeleton, empty-state |
| 04 | API client + mock layer | 2 | B-01, A-01 | Typed fetch client against FastAPI, mock responses for offline dev |
| 05 | Mothership: Candidate ingestion | 2 | B-03, B-04 | CV upload, extraction animation, dedup comparison modal |
| 06 | Mind: Role posting wizard | 3 | B-03, B-04 | Step-by-step guided workflow with real-time requirement extraction |
| 07 | Mind: Candidate browse + matching | 3 | B-03, B-04 | Anonymized candidate cards, match explanations, filter bar, shortlist/dismiss |
| 08 | Mothership: Match results view | 3 | B-03, B-04 | Ranked matches with traceability expand, skill chips, one-click actions |
| 09 | Mothership: Collections UI | 4 | B-03, B-04 | Create/edit collections, visibility toggles, browse shared collections |
| 10 | Mothership: Handoff inbox/outbox | 4 | B-03, B-04 | Send handoffs, receive inbox, accept/decline, attribution trail |
| 11 | Mind: Quotes + pipeline | 4 | B-03, B-04 | Quote request flow, fee breakdown display, kanban pipeline |
| 12 | Mothership: Copilot sidebar | 5 | B-04 | Conversation panel, streaming responses, inline results, one-click actions |
| 13 | Mind + Mothership: Dashboards | 5 | B-03..B-11 | Talent partner dashboard, client dashboard with metrics and action cards |
| 14 | Admin: Analytics + quality | 6 | B-04, A-15 | Funnel chart, trending skills, partner performance, dedup review queue |
| 15 | Admin: Adapters + monitoring + users | 6 | B-14 | Adapter health cards, AI pipeline stats, user management |
| 16 | Polish: Demo mode + final pass | 7-8 | B-01..B-15 | Demo walkthrough overlay, dark mode, animations, responsive, toast system, accessibility |

---

## Detailed Task Plans

Each task has a self-contained plan file in `plans/agent-a/` or `plans/agent-b/`. See the individual task files for implementation details, checklists, acceptance criteria, and handoff notes.

### Cross-Agent Dependency Graph

```
Day 1 (PAIR):  A-01 ──→ B-01
               A-01 → A-02 → A-03
                      B-01 → B-02

Day 2:         A-04 ─→ A-05 ─→ A-06
               A-03,A-05 → A-07
               B-01 → B-03, B-04 → B-05

Day 3:         A-07,A-03 → A-08
               A-07 → A-09 → A-10
               A-09,A-10 → A-11
               B-03,B-04 → B-06, B-07, B-08

Day 4:         A-03 → A-12
               A-08,A-12 → A-13
               A-08,A-09 → A-14
               B → B-09, B-10, B-11

Day 5:         A-12 → A-15
               B-04 → B-12
               B-03..B-11 → B-13

Day 5-6:       A-all → A-16
               B-04,A-15 → B-14 → B-15

Day 7-8:       B-all → B-16
```

### Integration Milestones

| Milestone | When | What to verify |
|-----------|------|----------------|
| **Contracts aligned** | End of Day 1 | Python Pydantic + TS types match exactly |
| **First API call** | Day 2 | Frontend can hit backend health endpoint through typed client |
| **Candidate flow** | End of Day 3 | Upload CV → extraction → stored → matched → displayed in UI |
| **Full persona flows** | End of Day 5 | All three personas can complete their primary workflows |
| **Demo-ready** | End of Day 7 | Seed data loaded, demo mode works, all flows polished |
| **Ship** | End of Day 8 | Cross-validated, README complete, tagged release |
