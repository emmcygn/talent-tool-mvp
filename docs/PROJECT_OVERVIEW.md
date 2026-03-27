# RecruitTech PoC — Deep Project Overview

> AI-powered recruitment platform for UK recruitment partners, mirroring a Mind + Mothership architecture.

---

## 1. What This Platform Does

RecruitTech connects **talent partners** (recruiters) with **hiring managers** (clients) through AI-powered candidate matching. The platform ingests candidates from multiple sources (Bullhorn ATS, HubSpot CRM, LinkedIn), uses LLMs to extract structured profiles, generates semantic embeddings, and produces ranked matches with plain-English explanations.

**Three user personas:**

| Persona | Interface | Purpose |
|---------|-----------|---------|
| **Talent Partner** | Mothership (`/mothership/*`) | Manage candidates, run matches, collaborate via handoffs, use copilot |
| **Hiring Manager** | Mind (`/mind/*`) | Post roles, browse anonymized candidates, request intros, manage quotes |
| **Admin** | Mothership Admin (`/mothership/admin/*`) | Monitor platform health, review dedup queue, manage users |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 16 / React 19 / TypeScript)                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  Mind UI         │  │  Mothership UI  │  │  Admin UI      │  │
│  │  (Client views)  │  │  (Partner views)│  │  (Ops views)   │  │
│  └────────┬────────┘  └────────┬────────┘  └───────┬────────┘  │
│           └────────────────────┼─────────────────────┘          │
│                       API Client (lib/api.ts)                   │
│                       Mock fallback (lib/api-mock.ts)           │
└───────────────────────────────┬─────────────────────────────────┘
                                │ REST + SSE
┌───────────────────────────────┼─────────────────────────────────┐
│  Backend (FastAPI / Python 3.12)                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ API      │ │ Pipelines│ │ Matching │ │ Copilot  │          │
│  │ (9 rtrs) │ │ (ETL)    │ │ (Engine) │ │ (NL→SQL) │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│  │ Services │ │ Signals  │ │ Adapters │                       │
│  │ (Biz)    │ │ (Events) │ │ (CRM/ATS)│                       │
│  └──────────┘ └──────────┘ └──────────┘                       │
│  Contracts (Pydantic v2) — single source of truth               │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────┐
│  Supabase (PostgreSQL 15 + pgvector)                            │
│  Tables: users, organisations, candidates, roles, matches,      │
│          signals, handoffs, quotes, collections                  │
│  RLS policies, Realtime subscriptions, HNSW vector indexes      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Data Flow

```
Adapters (Bullhorn/HubSpot/LinkedIn)
    │
    ▼
Ingest → Normalize (adapter-specific → canonical format)
    │
    ▼
Extract (GPT-4o → skills, experience, seniority, salary, availability)
    │
    ▼
Embed (text-embedding-3-small → 1536-dim vector)
    │
    ▼
Deduplicate (exact email → fuzzy name → semantic similarity)
    │  auto-merge >0.9 confidence
    │  human review 0.6–0.9
    ▼
Stored Candidate (enriched, deduplicated, embedded)
    │
    ▼
Match Engine:
    1. Structured filter (location, salary, seniority, availability)
    2. Semantic search (pgvector cosine similarity, top_k=50)
    3. Composite score (40% skill + 35% semantic + 25% experience)
    4. Confidence bucket (strong >0.75 / good 0.5–0.75 / possible <0.5)
    5. Explain (GPT-4o → strengths, gaps, recommendation)
    │
    ▼
Display (ranked matches with explanations → UI)
```

---

## 4. Backend Modules

### 4.1 API Layer (`backend/api/`) — 9 Routers

| Router | Key Endpoints | Access |
|--------|--------------|--------|
| **auth** | `GET /api/users/me` | All |
| **candidates** | CRUD + search + extract | Partner, Admin |
| **roles** | CRUD + extract-requirements | All (client-scoped) |
| **matches** | Per-role/candidate, generate, status update, anonymized | Role-based |
| **collections** | CRUD, add/remove candidates, stats | Partner, Admin |
| **handoffs** | Create, inbox/outbox, respond, attribution chain | Partner, Admin |
| **quotes** | Generate, list, status transitions | Client, Admin |
| **copilot** | Query (sync + SSE streaming), session management | Partner, Admin |
| **signals** | Recent activity, funnel, trending skills, performance | Role-based |
| **admin** | Stats, adapter health, pipeline status, dedup queue, user CRUD | Admin only |

### 4.2 Pipelines (`backend/pipelines/`)

- **ingest.py** — Pulls from adapters, normalizes, stores, emits signals
- **normalize.py** — Adapter-specific field mapping (Bullhorn employment history, HubSpot tags, LinkedIn endorsements)
- **enrich.py** — GPT-4o structured extraction + text-embedding-3-small embeddings; per-field confidence; flags low-confidence (<0.7) for review
- **deduplicate.py** — Three-strategy matching (exact/fuzzy/semantic); auto-merge, review queue, or no-match

### 4.3 Matching Engine (`backend/matching/`)

- **structured.py** — Hard-requirement filters (location, salary, seniority, availability)
- **semantic.py** — pgvector `match_candidates` RPC (cosine similarity, HNSW index)
- **scorer.py** — Composite: 40% skill overlap (with aliases like JS↔JavaScript), 35% semantic, 25% experience fit
- **explainer.py** — GPT-4o generates 2-3 sentence explanation + strengths + gaps + recommendation; template fallback
- **engine.py** — Orchestrates: filter → search → score → bucket → upsert → explain

### 4.4 Services (`backend/services/`)

- **quote.py** — Fee by seniority (£8K junior → £35K principal), 20% pool discount, 14-day validity
- **collection.py** — Visibility (private/shared_all/shared_specific), stats aggregation
- **handoff.py** — Attribution ID tracking, response time metrics, signal emission

### 4.5 Signals & Analytics (`backend/signals/`)

12 signal types emitted on every meaningful action. Analytics queries aggregate signals for:
- **Funnel**: ingested → matched → shortlisted → intro_requested → placed (with conversion rates)
- **Trending skills**: demand scoring across active roles
- **Partner performance**: candidates added, handoffs, placements (30-day window)
- **Client engagement**: shortlist rates, quote acceptance
- **Time series**: daily/weekly event counts

### 4.6 Copilot (`backend/copilot/`)

- **parser.py** — NL → structured query via GPT-4o (8 query types; multi-turn context, last 10 turns)
- **executor.py** — Runs structured queries against Supabase (operators: eq, neq, gt, lt, like, ilike, in, contains)
- **formatter.py** — User-friendly summary + contextual actions + follow-up suggestions

### 4.7 Adapters (`backend/adapters/`)

Abstract `BaseAdapter` with mock implementations for Bullhorn, HubSpot, LinkedIn. Registry pattern for discovery and health aggregation.

---

## 5. Frontend Architecture

### 5.1 Tech Stack

- **Next.js 16** (App Router) + **React 19** + **TypeScript**
- **Tailwind CSS v4** + **shadcn/ui** (base-nova style)
- **Supabase** client for auth
- **Recharts** for data visualization
- **Sonner** for toast notifications
- Dark-first design: navy background (#0A0E1A), teal accent (#00D4AA), glassmorphism cards

### 5.2 Routing

**Mothership (Talent Partner + Admin):**
- `/mothership/dashboard` — Activity feed, handoff inbox, active roles, signals
- `/mothership/candidates/new` — CV upload, text paste, adapter sync, extraction review
- `/mothership/matching` — Match results by role, confidence filtering, bulk actions
- `/mothership/collections` — Create/manage/share candidate groups
- `/mothership/handoffs` — Inbox/outbox, accept/decline, timeline
- `/mothership/admin/analytics` — Funnel, trending skills, partner performance
- `/mothership/admin/quality` — Duplicate detection & merging
- `/mothership/admin/adapters` — CRM/ATS integration health
- `/mothership/admin/users` — User management

**Mind (Client/Hiring Manager):**
- `/mind/dashboard` — Roles overview, pipeline summary
- `/mind/roles/new` — 5-step role wizard (Basics → Description → Requirements → Details → Review)
- `/mind/candidates` — Anonymized AI-matched candidates, filter & shortlist
- `/mind/quotes` — Placement fee quotes
- `/mind/pipeline` — Kanban board (matched → placed)

**Auth:**
- `/login` — Demo user selection (3 personas)

### 5.3 Layout Structure

- **Mothership**: Fixed left sidebar (264px) + main content + optional right copilot panel; mobile: sheet drawer
- **Mind**: Horizontal sticky header + max-width container; mobile: sheet drawer
- **Copilot sidebar**: Full conversational AI with context-aware suggestions, SSE streaming

### 5.4 API Client (`lib/api.ts`)

- Bearer token auth from Supabase session
- Retry logic (max 2 retries, exponential backoff)
- FormData auto-detection for file uploads
- Mock fallback (`NEXT_PUBLIC_USE_MOCKS=true`) with deterministic test data
- Abstraction layer (`lib/api-client.ts`) switches real/mock based on env

### 5.5 Auth System

- **Supabase JWT** for production
- **Demo mode**: sessionStorage + browser cookie (`recruittech_demo_role`)
- Three demo users: Sarah Chen (talent_partner), Alex Thompson (client), Admin User (admin)
- Role extracted from JWT `user_metadata.role` or demo session

---

## 6. Data Contracts

**Python (backend/contracts/)** — Pydantic v2, source of truth
**TypeScript (contracts/canonical.ts)** — Mirror of Python contracts

### Key Entities

| Entity | Key Fields |
|--------|-----------|
| **Candidate** | id, name, email, skills (name/years/confidence), experience, seniority, salary, availability, embedding (1536-dim), sources, extraction_confidence |
| **Role** | id, title, company, description, required_skills, preferred_skills, seniority, salary_band, location, remote_policy, embedding |
| **Match** | id, candidate_id, role_id, overall_score, structured_score, semantic_score, experience_score, skill_overlap, confidence, explanation, strengths, gaps |
| **Collection** | id, name, description, owner_id, visibility, candidate_ids, tags |
| **Handoff** | id, sender_id, recipient_id, candidate_ids, role_id, status, attribution_id, notes |
| **Quote** | id, role_id, candidate_id, client_id, base_fee, discount_pct, final_fee, fee_breakdown, status, expires_at |
| **Signal** | id, type, actor_id, entity_type, entity_id, metadata, timestamp |

### Key Enums

- `UserRole`: talent_partner, client, admin
- `SeniorityLevel`: junior, mid, senior, lead, principal
- `ConfidenceLevel`: strong, good, possible
- `MatchStatus`: generated, shortlisted, dismissed, intro_requested
- `HandoffStatus`: pending, accepted, declined, expired
- `QuoteStatus`: generated, sent, accepted, declined, expired

---

## 7. Database (Supabase)

### Schema

- **10 tables**: users, organisations, candidates, roles, matches, signals, handoffs, quotes, collections, collection_candidates
- **pgvector**: `candidates.embedding` and `roles.embedding` as `vector(1536)`
- **JSONB columns**: skills, experience, sources, extraction_flags, skill_overlap, strengths, gaps, fee_breakdown, candidate_ids, shared_with, tags
- **Indexes**: B-tree on common filters, HNSW on embeddings (cosine distance)
- **RLS policies**: Row-level security by user role
- **Realtime**: Enabled on matches, handoffs, quotes, signals
- **RPC**: `match_candidates(query_embedding, match_count, candidate_ids?)` for pgvector search

---

## 8. Business Logic Highlights

### Matching Scoring Weights
- **40%** Skill overlap (required skills weighted 2x, preferred 1x; alias matching)
- **35%** Semantic similarity (embedding cosine distance)
- **25%** Experience fit (seniority level proximity)

### Quote Pricing
| Seniority | Base Fee | With Pool Discount (20%) |
|-----------|----------|--------------------------|
| Junior | £8,000 | £6,400 |
| Mid | £12,000 | £9,600 |
| Senior | £18,000 | £14,400 |
| Lead | £25,000 | £20,000 |
| Principal | £35,000 | £28,000 |

### Deduplication Thresholds
- **>0.9 confidence**: Auto-merge (combine skills, sources, experience)
- **0.6–0.9**: Queue for human review
- **<0.6**: No match, separate records

### Seniority Inference (from years of experience)
- 10+ → principal, 7+ → lead, 4+ → senior, 2+ → mid, else → junior

---

## 9. Testing

**Backend**: 17 pytest modules covering:
- Matching scorer (perfect/partial/confidence buckets)
- Deduplication (merge helpers, confidence)
- Extraction (candidate/role LLM response parsing)
- Explainer (match explanation generation)
- All API endpoints (CRUD, collections, quotes, handoffs, copilot, signals, admin)
- Integration (end-to-end flows)
- Contracts (model validation)
- Adapters (interface compliance)

**Frontend**: Build + lint validation (`npm run build && npm run lint`)

---

## 10. Dev Commands

```bash
# Backend
cd backend && pip install -r requirements.txt
cd backend && python -m pytest -v                    # tests
cd backend && uvicorn main:app --reload --port 8000  # dev server

# Frontend
cd frontend && npm install
cd frontend && npm run build                         # build
cd frontend && npm run lint                          # lint
cd frontend && npm run dev                           # dev server (port 3000)

# Validation gate (must pass before any task is complete)
cd backend && python -m pytest -v
cd frontend && npm run build && npm run lint
```

---

## 11. Project Status

**All 32 tasks (16 per agent) completed as of 2025-03-24.**

The platform is a functional PoC with:
- Full data ingestion pipeline (3 adapters)
- AI-powered extraction and embedding
- Hybrid matching engine (structured + semantic)
- LLM match explanations
- Collections, handoffs, and quote management
- Conversational copilot with streaming
- Signal-based analytics
- Admin monitoring dashboard
- Polished dark-theme UI for both personas
- Demo mode with pre-seeded data
