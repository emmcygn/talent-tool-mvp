# RecruitTech PoC — Design Specification

## Overview

A proof-of-concept recruitment platform mirroring the Mind + Mothership architecture described in the founding engineer job brief. Built to demonstrate competence for both the **Founding Product Engineer — Software** and **Founding Product Engineer — Data** roles simultaneously.

**Timeline:** 8 days, 2 agents working in parallel (16 engineer-days total)
**Audience:** Non-technical recruitment partners — polish and clarity matter more than technical depth
**Execution model:** Dual autonomous agents via `agents-scaffolding` framework

---

## Product Architecture

Two products, mirroring the job brief:

### Mind (External-Facing)
Task-based, workflow-first interfaces for hiring managers / clients. They post roles, review AI-matched candidates, request introductions, and track their hiring pipeline. Premium, minimal, guided UX.

### Mothership (Internal)
Data lake + copilot + dashboard powering the operating system. Talent partners use it to ingest candidates, run AI matching, manage collections, hand off leads, and query the system via a natural language copilot. Admins use it for platform analytics, data quality oversight, and adapter management.

### Three Personas

| Persona | Product | Description |
|---------|---------|-------------|
| **Talent Partner** | Mothership | Power user. Ingests candidates, runs matching, manages collections, sends/receives handoffs, uses copilot |
| **Client / Hiring Manager** | Mind | External user. Posts roles, reviews matched candidates, requests intros, tracks pipeline |
| **Admin / Ops** | Mothership | Platform oversight. Analytics, data quality, adapter health, user management, copilot with full access |

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui | Matches job brief stack direction exactly |
| **Backend API** | FastAPI (Python) | Matches Data Engineer role stack; serves REST + WebSocket |
| **Database** | Supabase (PostgreSQL + pgvector + Realtime + Auth + RLS) | Named in job brief stack direction |
| **AI/LLM** | OpenAI API (GPT-4o for extraction/explanation, text-embedding-3-small for embeddings) | Production-realistic, swappable |
| **Orchestration** | agents-scaffolding (Agent A + Agent B, parallel autonomous execution) | Proven dual-agent framework |

### Monorepo Structure

```
recruittech/
├── backend/                    # Python — Mothership engine
│   ├── api/                    # FastAPI routes
│   │   ├── candidates.py       # Candidate CRUD + search
│   │   ├── roles.py            # Role CRUD + matching triggers
│   │   ├── matches.py          # Match results + explanations
│   │   ├── collections.py      # Collection management
│   │   ├── handoffs.py         # Handoff lifecycle
│   │   ├── quotes.py           # Quote generation
│   │   ├── copilot.py          # Natural language query endpoint
│   │   ├── signals.py          # Event stream / analytics
│   │   ├── admin.py            # Admin-only endpoints
│   │   └── auth.py             # Auth helpers
│   ├── adapters/               # Source integrations (mocked)
│   │   ├── base.py             # Abstract adapter interface
│   │   ├── bullhorn.py         # Bullhorn ATS adapter
│   │   ├── hubspot.py          # HubSpot CRM adapter
│   │   └── linkedin.py         # LinkedIn Recruiter adapter
│   ├── contracts/              # Canonical data contracts (Pydantic)
│   │   ├── candidate.py        # Candidate canonical model
│   │   ├── role.py             # Role canonical model
│   │   ├── match.py            # Match result model
│   │   ├── signal.py           # Signal event model
│   │   └── shared.py           # Shared enums, value objects
│   ├── pipelines/              # ETL/ELT
│   │   ├── ingest.py           # Raw data ingestion
│   │   ├── normalize.py        # Map adapter output → canonical
│   │   ├── deduplicate.py      # Identity resolution + dedup
│   │   └── enrich.py           # AI extraction + embedding generation
│   ├── matching/               # Hybrid AI matching
│   │   ├── structured.py       # Filter by structured fields
│   │   ├── semantic.py         # pgvector similarity search
│   │   ├── scorer.py           # Composite scoring
│   │   └── explainer.py        # LLM-generated match explanations
│   ├── copilot/                # Natural language query layer
│   │   ├── parser.py           # NL → structured query translation
│   │   ├── executor.py         # Query execution against data
│   │   └── formatter.py        # Response formatting with actions
│   ├── signals/                # Event tracking + recommendations
│   │   ├── tracker.py          # Event emission
│   │   ├── triggers.py         # Action triggers (notifications, recommendations)
│   │   └── analytics.py        # Aggregate analytics queries
│   ├── services/               # Business logic
│   │   ├── handoff.py          # Handoff lifecycle management
│   │   ├── quote.py            # Quote generation logic
│   │   └── collection.py       # Collection management
│   ├── seed/                   # Demo data generation
│   │   ├── candidates.py       # 50+ realistic UK-market candidates
│   │   ├── roles.py            # 15+ realistic roles across sectors
│   │   ├── organisations.py    # 10+ client companies
│   │   └── users.py            # Demo users for each persona
│   ├── config.py               # App configuration
│   ├── main.py                 # FastAPI app entry point
│   └── requirements.txt
├── frontend/                   # Next.js — Mind + Mothership UI
│   ├── app/
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Landing / login
│   │   ├── mind/               # Client / Hiring Manager views
│   │   │   ├── layout.tsx      # Mind layout (minimal chrome)
│   │   │   ├── dashboard/      # Client dashboard
│   │   │   ├── roles/          # Post + manage roles
│   │   │   ├── candidates/     # Browse matched candidates
│   │   │   ├── quotes/         # Quote requests + status
│   │   │   └── pipeline/       # Hiring pipeline kanban
│   │   └── mothership/         # Talent Partner + Admin views
│   │       ├── layout.tsx      # Mothership layout (sidebar + copilot)
│   │       ├── dashboard/      # Partner dashboard
│   │       ├── candidates/     # Candidate ingestion + management
│   │       ├── matching/       # Match results + exploration
│   │       ├── collections/    # Collection management
│   │       ├── handoffs/       # Handoff inbox/outbox
│   │       ├── copilot/        # Copilot conversation view
│   │       ├── admin/          # Admin-only views
│   │       │   ├── analytics/  # Platform analytics + funnels
│   │       │   ├── quality/    # Data quality + dedup review
│   │       │   ├── adapters/   # Adapter health + management
│   │       │   └── users/      # User management
│   │       └── demo/           # Guided demo walkthrough
│   ├── components/
│   │   ├── ui/                 # shadcn/ui primitives
│   │   ├── mind/               # Mind-specific components
│   │   ├── mothership/         # Mothership-specific components
│   │   └── shared/             # Cross-product components
│   ├── lib/
│   │   ├── api.ts              # API client (typed, from contracts)
│   │   ├── supabase.ts         # Supabase client + auth helpers
│   │   ├── types.ts            # TypeScript canonical types (mirrors Python contracts)
│   │   └── utils.ts            # Shared utilities
│   ├── package.json
│   └── tsconfig.json
├── contracts/                  # Shared interface boundary between agents
│   └── canonical.ts            # TypeScript canonical types (Agent B mirrors from backend/contracts/)
├── supabase/
│   ├── migrations/             # Database migrations
│   ├── seed.sql                # Seed data SQL
│   └── config.toml             # Supabase project config
├── plans/                      # Agent orchestration (from agents-scaffolding)
│   ├── ORCHESTRATOR.md
│   ├── BOOTSTRAP.md
│   ├── STATE.md
│   ├── HANDOFF.md
│   ├── ISSUES.md
│   ├── agent-a/               # Data Engineer tasks
│   └── agent-b/               # Product Engineer tasks
├── tasks/
│   ├── todo.md
│   └── lessons.md
├── CLAUDE.md                   # Agent instructions
├── docker-compose.yml          # Local dev (Supabase + backend)
└── README.md
```

---

## Canonical Data Contracts

Contracts are defined once and shared. They are the interface boundary between Agent A and Agent B.

### Candidate

```python
class Candidate(BaseModel):
    id: UUID
    # Identity (deduplicated)
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    location: str | None
    linkedin_url: str | None

    # Structured (LLM-extracted)
    skills: list[ExtractedSkill]           # name, years, confidence
    experience: list[ExperienceEntry]      # company, title, duration, industry
    seniority: SeniorityLevel             # junior, mid, senior, lead, principal
    salary_expectation: SalaryRange | None
    availability: AvailabilityStatus      # immediate, 1_month, 3_months, not_looking
    industries: list[str]

    # Raw
    cv_text: str | None
    profile_text: str | None

    # Source tracking
    sources: list[CandidateSource]         # adapter_name, external_id, ingested_at
    dedup_group: UUID | None               # links merged records
    dedup_confidence: float | None         # confidence of the merge

    # Embeddings (stored in pgvector)
    embedding: list[float] | None

    # Extraction metadata
    extraction_confidence: float           # overall confidence of structured extraction
    extraction_flags: list[str]            # fields that need human review

    # System
    created_at: datetime
    updated_at: datetime
    created_by: UUID                       # talent partner who added them
```

### Role

```python
class Role(BaseModel):
    id: UUID
    title: str
    description: str
    organisation_id: UUID

    # Structured (LLM-extracted from description)
    required_skills: list[RequiredSkill]   # name, min_years, importance
    preferred_skills: list[RequiredSkill]
    seniority: SeniorityLevel
    salary_band: SalaryRange | None
    location: str | None
    remote_policy: RemotePolicy           # onsite, hybrid, remote
    industry: str | None

    # Embeddings
    embedding: list[float] | None

    # Extraction metadata
    extraction_confidence: float

    # System
    status: RoleStatus                     # draft, active, paused, filled, closed
    created_at: datetime
    created_by: UUID                       # client user who posted
```

### Match

```python
class Match(BaseModel):
    id: UUID
    candidate_id: UUID
    role_id: UUID

    # Scoring (all components visible for traceability)
    overall_score: float                    # 0-1 composite
    structured_score: float                 # skill overlap component
    semantic_score: float                   # embedding similarity component
    skill_overlap: list[SkillMatch]         # per-skill: matched, partial, missing
    confidence: ConfidenceLevel             # strong, good, possible

    # Explanation
    explanation: str                        # plain-English, non-technical
    strengths: list[str]                    # bullet points
    gaps: list[str]                         # bullet points
    recommendation: str                     # one-line summary

    # Traceability
    scoring_breakdown: dict                 # full breakdown of how score was computed
    model_version: str                      # which model generated this

    # System
    created_at: datetime
    status: MatchStatus                     # generated, shortlisted, dismissed, intro_requested
```

### Signal

```python
class Signal(BaseModel):
    id: UUID
    event_type: SignalType                  # candidate_viewed, shortlisted, dismissed,
                                           # intro_requested, handoff_sent, handoff_accepted,
                                           # quote_generated, placement_made, copilot_query
    actor_id: UUID                          # user who triggered it
    actor_role: UserRole
    entity_type: str                        # candidate, role, match, collection, handoff
    entity_id: UUID
    metadata: dict                          # event-specific payload
    created_at: datetime
```

### Handoff

```python
class Handoff(BaseModel):
    id: UUID
    from_partner_id: UUID
    to_partner_id: UUID
    candidate_ids: list[UUID]
    context_notes: str                      # why these candidates are relevant
    target_role_id: UUID | None             # specific role, or general referral

    status: HandoffStatus                   # pending, accepted, declined, expired
    response_notes: str | None              # receiver's response
    attribution_id: UUID                    # tracks through to placement for commission

    created_at: datetime
    responded_at: datetime | None
```

### Quote

```python
class Quote(BaseModel):
    id: UUID
    client_id: UUID
    candidate_id: UUID
    role_id: UUID

    # Pricing
    is_pool_candidate: bool                 # already in shared talent network
    base_fee: Decimal                       # standard placement fee
    pool_discount: Decimal | None           # discount for pre-vetted candidates
    final_fee: Decimal
    fee_breakdown: dict                     # human-readable pricing explanation

    status: QuoteStatus                     # generated, sent, accepted, declined, expired
    created_at: datetime
    expires_at: datetime
```

### Collection

```python
class Collection(BaseModel):
    id: UUID
    name: str                               # e.g., "Senior Backend — London"
    description: str | None
    owner_id: UUID                          # talent partner
    visibility: Visibility                  # private, shared_specific, shared_all
    shared_with: list[UUID] | None          # specific partner IDs if shared_specific
    candidate_ids: list[UUID]
    tags: list[str]

    # Aggregate stats (computed)
    candidate_count: int
    avg_match_score: float | None           # against a given role, if set
    available_now_count: int

    created_at: datetime
    updated_at: datetime
```

---

## AI Pipeline

### Stage 1: Extraction

When a candidate enters the system (CV upload, profile paste, or adapter sync):

1. Raw text is sent to the LLM with a structured extraction prompt
2. LLM returns structured JSON: skills (with years of experience), experience timeline, seniority, industries, salary expectations, availability
3. Each extracted field tagged with a confidence score (0-1)
4. Fields below 0.7 confidence are flagged for human review (amber highlight in UI)
5. Talent partner can correct any field inline — corrections feed back as training signal
6. Embedding generated from the full profile text via text-embedding-3-small
7. Stored in pgvector for similarity search

**Traceability:** Every extraction stores the model version, prompt version, raw input, raw output, and per-field confidence. Visible in admin view.

### Stage 2: Matching

When a role is posted or a match is requested:

1. **Structured filter** — exclude candidates who don't meet hard requirements (location, availability, minimum experience years)
2. **Semantic search** — pgvector cosine similarity between role embedding and candidate embeddings, top 50
3. **Skill overlap scoring** — compare extracted skills against required/preferred skills, weighted by importance
4. **Composite score** — weighted combination: 40% skill overlap, 35% semantic similarity, 25% experience/seniority fit
5. **Rank and threshold** — top candidates bucketed into Strong (>0.75), Good (0.5-0.75), Possible (0.3-0.5)

**Traceability:** Every match stores the full scoring breakdown — which filters were applied, similarity scores, skill-by-skill comparison.

### Stage 3: Explanation

For the top matches (Strong + Good):

1. LLM receives: candidate structured profile, role structured requirements, skill overlap data, similarity score
2. Generates: plain-English explanation (2-3 sentences), bullet-point strengths, bullet-point gaps, one-line recommendation
3. Language is non-technical: "6 years of Python backend experience aligns well with the requirement" not "skill_overlap_score: 0.82"
4. Confidence indicator maps to human-friendly labels: Strong Match, Good Match, Worth Considering

**Guardrails:** Explanations are regenerable. If a talent partner corrects a match (marks a "Strong" candidate as not relevant), the signal is logged for future quality analysis. The system never auto-rejects — it always surfaces with explanations and lets humans decide.

### Copilot Query Layer

Natural language interface for talent partners and admins:

1. User types a question: "Who are my best Python candidates available in London?"
2. **Parser** — LLM translates natural language to a structured query (filters + sort + limit) against the canonical data model
3. **Executor** — runs the structured query against Supabase
4. **Formatter** — returns results with the structured query shown (transparency), one-click actions (shortlist, refer, add to collection), and follow-up suggestions

**Transparency:** Every copilot response shows: the query it interpreted, the filters it applied, result count. The user can see exactly what the system did — no black box.

**Multi-turn:** Copilot maintains conversation context within a session. "Now show me only the ones with fintech experience" refines the previous query.

---

## Signal Layer

Every meaningful user action emits a signal event:

| Event | Actor | Payload |
|-------|-------|---------|
| `candidate_ingested` | talent_partner | source adapter, extraction confidence |
| `candidate_viewed` | any | time spent, which fields expanded |
| `candidate_shortlisted` | talent_partner / client | for which role |
| `candidate_dismissed` | talent_partner / client | reason (optional) |
| `match_generated` | system | score, confidence level |
| `intro_requested` | client | quote amount, pool vs exclusive |
| `handoff_sent` | talent_partner | to whom, how many candidates |
| `handoff_accepted` | talent_partner | response time |
| `handoff_declined` | talent_partner | reason |
| `quote_generated` | system | amount, pool discount applied |
| `placement_made` | admin | final fee, time to placement |
| `copilot_query` | talent_partner / admin | query text, result count |

**Signals power:**
- Activity feeds (talent partner dashboard, admin dashboard)
- Analytics (funnel analysis, conversion rates, trending skills)
- Recommendations ("5 candidates match roles similar to your recent hires")
- Notification triggers (new matches, handoff received, quote requested)
- Quality feedback loop (dismissed Strong Matches indicate calibration drift)

---

## Identity Resolution & Deduplication

When candidates arrive from multiple adapters:

1. **Exact match:** email or phone number matches an existing record → auto-merge with high confidence
2. **Fuzzy match:** name similarity (Levenshtein) + same employer + similar role title → flag as potential duplicate (0.6-0.9 confidence)
3. **Semantic match:** embedding similarity > 0.95 on CV text → flag as potential duplicate
4. **Auto-merge:** confidence > 0.9 → merge automatically, log the merge, show in admin review queue as "auto-merged"
5. **Manual review:** confidence 0.6-0.9 → queue for talent partner review with side-by-side comparison
6. **Merge logic:** when merging, keep the most complete/recent data for each field, preserve all source attributions, combine skills lists (deduplicated)

Admin can review all merges (auto and manual), override decisions, and split incorrectly merged records.

---

## Persona Flows

### Talent Partner (Mothership)

**Dashboard:**
- Active roles with live match counts and quality indicators
- Pipeline health: candidates in system, pending dedup reviews, extraction queue status
- Handoff inbox (incoming) with accept/decline actions and outgoing referral status
- Activity feed powered by signal layer — "what needs attention" not just "what happened"
- Quick actions: add candidate, run matches, view collections

**Copilot Sidebar:**
- Always-visible sidebar panel (collapsible)
- Natural language query input with autocomplete suggestions
- Results render inline with one-click actions
- Shows the structured query it ran (transparency)
- Multi-turn: refine previous queries conversationally
- Suggested queries based on current view context

**Candidate Ingestion:**
- Upload CV (PDF/DOCX drag-and-drop), paste text, or "sync" from adapter (Bullhorn, HubSpot, LinkedIn)
- Real-time extraction animation: structured profile builds as LLM processes — skills, experience, seniority appearing progressively
- Low-confidence fields highlighted amber — partner corrects inline
- Automatic dedup check: if potential duplicate found, side-by-side comparison modal with merge/keep options
- Source attribution visible: "Imported from Bullhorn" badge

**Smart Matching:**
- Select a role → ranked candidate cards appear
- Each card: plain-English explanation, skill chips (green=matched, amber=partial, grey=missing), confidence badge (Strong/Good/Possible)
- Expand card: full traceability — scoring breakdown, all matched/missing skills, semantic similarity context
- One-click: shortlist, dismiss (with optional reason), add to collection, refer to partner
- Filter bar: location, availability, seniority, specific skills

**Collections:**
- Create themed collections with tags ("Senior Backend — London", "ML Engineers — Remote OK")
- Toggle visibility: private / shared with specific partners / shared with all
- Collection cards show aggregate stats: candidate count, availability breakdown, avg match quality
- Browse other partners' shared collections in sidebar
- Pull candidates from shared collections into own workflow

**Handoffs:**
- Inbox/outbox tab view
- Send: select candidates, pick partner, add context notes, optionally link to a specific role
- Receive: see candidates with sender's context, accept/decline with notes
- Attribution trail: visible chain from ingestion → handoff → placement
- Status tracking: pending, accepted, declined, expired

### Client / Hiring Manager (Mind)

**Dashboard:**
- Active roles with status indicators (sourcing / candidates ready / interviews / offer stage)
- Action cards with clear CTAs: "3 new candidates matched for Senior Backend — Review now"
- Quote requests in progress with status
- Simple metric tiles: candidates in pipeline, avg time-to-shortlist, placements this quarter
- Recommended candidates section: "Based on your recent hires, we have 5 strong candidates"

**Post a Role (guided step-by-step workflow):**
- Step 1: Role title + department
- Step 2: Description (free text, rich editor)
- Step 3: As they type, system extracts requirements in real-time → shown as editable tags: "We found: Python, 5+ years, fintech experience, London preferred"
- Step 4: Salary band + location + remote policy
- Step 5: Review all extracted requirements, confirm or edit
- Step 6: Publish → matches start generating immediately
- This IS "AI with guardrails, transparency, and user control" — the AI suggests, the human confirms

**Review Matched Candidates:**
- Clean card layout, anonymized by default (first name + last initial, no company names)
- Each card: match explanation in plain English, key skill chips, availability, confidence badge
- "Pre-vetted" badge on shared pool candidates (signals cheaper placement)
- No raw scores or percentages — non-technical language throughout
- Actions: shortlist (heart icon), dismiss (with optional reason), request intro
- Filter bar: skills, seniority, availability, location

**Request Introduction + Quote:**
- Click "Request Intro" on shortlisted candidate
- System generates quote with clear breakdown:
  - "Standard placement fee: £X"
  - "This candidate is in our pre-vetted talent network — reduced fee: £Y"
  - "Your saving: £Z"
- One-click accept → talent partner notified
- Quote valid for 14 days, status tracked

**Hiring Pipeline:**
- Visual kanban: Matched → Shortlisted → Intro Requested → Interviewing → Offer → Placed
- Drag cards between stages
- Notes at each stage
- Status changes emit signals → talent partners see updates in Mothership activity feed

**Proactive Recommendations:**
- Based on past roles and current talent pool
- "We have 5 strong candidates for roles similar to your last 3 hires"
- One-click to view recommended candidates
- Powered by signal layer (tracks what types of candidates this client shortlists/places)

### Admin / Ops (Mothership)

**Dashboard (copilot-powered):**
- Same copilot as talent partner but with platform-wide access
- Admin queries: "Which adapters had sync failures?", "Candidate-to-placement conversion rate for Q1?", "Show low-confidence auto-merges from this week"
- Top-level metric cards: total candidates, active roles, matches generated, placements, revenue in pipeline
- Health indicators for each adapter: last sync, records processed, error rate
- Alert panel: items needing attention (failed syncs, dedup review queue, low-confidence extractions)

**Platform Analytics (signal layer visualized):**
- Funnel visualization: Ingested → Deduplicated → Enriched → Matched → Shortlisted → Intro Requested → Placed
- Drop-off analysis at each stage
- Trending skills chart: most in-demand skills across all active roles
- Partner performance: handoff response times, placement conversion rates, candidates added
- Client engagement: browse frequency, shortlist rates, quote acceptance rates
- Match quality feedback: % of Strong Matches that convert to placements vs dismissals
- Time-series charts: activity over time, pipeline velocity

**Data Quality & Dedup Review:**
- Queue of pending dedup reviews (sorted by confidence)
- Side-by-side candidate comparison: fields from each source, agreements/conflicts highlighted
- One-click merge or keep separate
- Stats: auto-merge accuracy, review queue depth, sources with most duplicates
- Bulk actions for high-confidence merges

**Adapter Management:**
- Status cards for each integration (Bullhorn, HubSpot, LinkedIn)
- Per-adapter: last sync time, records ingested, errors, data quality score
- Schema mapping visualization: how adapter fields map to canonical contracts
- "Re-sync" trigger button
- Error log with details

**User & Access Management:**
- Add/deactivate talent partners and clients
- Role assignment
- Per-user activity summary (powered by signals)
- Invitation flow for new users

**AI Pipeline Monitoring:**
- Extraction queue: pending, processing, completed, failed
- Per-extraction detail: raw input → extracted output → confidence scores
- Match generation stats: avg processing time, confidence distribution
- LLM usage: tokens consumed, cost estimates, model version tracking

---

## UI/UX Design Direction

### Overall Aesthetic
- **Not:** cluttered ATS, enterprise software, data science prototype
- **Yes:** Linear, Notion, Stripe Dashboard, Vercel — clean, fast, modern
- Tailwind CSS + shadcn/ui for consistent, polished components
- Dark mode support (default light)
- Responsive but desktop-first (this is a work tool)

### Mind (Client-Facing)
- Minimal chrome, maximum whitespace
- Guided workflows with clear single actions per screen
- Premium feel: think Stripe Checkout, Deel, Remote.com
- No jargon — a hiring manager who's never used an ATS should understand in 30 seconds
- Soft color palette, professional typography

### Mothership (Internal)
- Information-dense but organized — think Linear sidebar + Notion content area
- Copilot sidebar always accessible
- Dashboard cards with clear status indicators
- Quick actions everywhere — minimize clicks to complete common tasks
- Data tables with sorting, filtering, inline actions
- Admin views: Grafana-inspired data density with Vercel-inspired cleanliness

### Shared Patterns
- Skeleton loading states (not spinners)
- Toast notifications for async operations
- Keyboard shortcuts for power users (talent partners)
- Empty states with helpful onboarding hints
- Consistent card patterns for candidates, roles, matches
- Confidence indicators: Strong (green), Good (amber), Possible (grey) — never raw numbers

### Demo Mode
A guided walkthrough overlay that can be activated to present the product:
- Step-by-step tour of each persona's key flows
- Pre-loaded demo data showing realistic UK market candidates and roles
- Highlights the AI matching, copilot, handoff, and quote features
- Designed for a 10-minute demo presentation to the interviewers

---

## Seed Data

Realistic UK recruitment market data:

- **50+ candidates** across: software engineering, data engineering, product management, ML/AI, DevOps. Mix of London, Manchester, remote. Realistic CVs with varied experience levels.
- **15+ roles** across: fintech, healthtech, SaaS, e-commerce. Varied seniority. Realistic job descriptions.
- **10+ client organisations** with UK company names and realistic profiles
- **5 talent partner users** with existing collections, handoffs, and history
- **3 client users** with active roles and pipeline history
- **Pre-generated matches** with explanations ready to display
- **Signal history** populating analytics dashboards from day one

Data should feel real enough that a recruitment professional would recognize the patterns.

---

## Auth & Access Control

- Supabase Auth with email/password (demo accounts pre-seeded)
- Three roles enforced at database level via Supabase RLS:
  - `talent_partner` — sees own candidates + shared collections + received handoffs
  - `client` — sees own roles + matched candidates (anonymized until intro) + own quotes
  - `admin` — sees everything
- JWT tokens, role in claims
- Frontend route guards per persona
- Demo login page with one-click access to each persona

---

## Real-Time Features (Supabase Realtime)

- **New match notifications** — when matches are generated for a role, the client and talent partner see them appear live
- **Handoff notifications** — receiving partner sees new handoff appear in inbox
- **Quote status updates** — client sees when their quote is reviewed
- **Pipeline updates** — talent partner sees when client moves a candidate to a new stage
- **Admin live feed** — signal events stream in real-time on the admin dashboard

---

## Agent Ownership Split

### Agent A — Data Engineer (Mothership Brain)

**Owns:**
- `backend/` — entire Python backend
- `contracts/canonical.py` — Python canonical types (source of truth)
- `supabase/migrations/` — database schema and migrations
- `supabase/seed.sql` — seed data
- `docker-compose.yml` — local dev infrastructure

**Responsibilities:**
- Canonical data model design and Pydantic contracts
- Supabase schema (tables, pgvector, RLS policies, functions)
- All FastAPI endpoints
- Adapter interfaces and mocked implementations (Bullhorn, HubSpot, LinkedIn)
- ETL pipeline: ingest → normalize → deduplicate → enrich
- AI matching pipeline: extraction, structured matching, semantic search, scoring, explanation
- Copilot query layer: NL parsing, execution, formatting
- Signal event tracking and analytics queries
- Business logic: handoffs, quotes, collections
- Seed data generation
- Backend tests

### Agent B — Product Engineer (Mind + Mothership UI)

**Owns:**
- `frontend/` — entire Next.js application
- `contracts/canonical.ts` — TypeScript canonical types (mirrors Python contracts)

**Responsibilities:**
- TypeScript type definitions (mirroring Agent A's Pydantic contracts)
- API client layer (typed fetch against FastAPI endpoints)
- Supabase client integration (auth, realtime subscriptions)
- All three persona layouts and views (Mind client, Mothership partner, Mothership admin)
- Copilot UI component (sidebar, conversation, inline results)
- Candidate card components with match explanations, skill chips, confidence badges
- Guided role-posting workflow for Mind
- Handoff inbox/outbox UI
- Quote generation and display UI
- Pipeline kanban view
- Admin analytics dashboards and charts
- Data quality review UI (dedup side-by-side)
- Adapter health status cards
- Demo mode walkthrough overlay
- Loading states, empty states, error states
- Responsive layout, dark mode
- Frontend tests

### Shared Contract Boundary

The **canonical type definitions** are the interface:
- Agent A writes `backend/contracts/*.py` (Pydantic models) — this is the single source of truth for all data shapes
- Agent B writes `contracts/canonical.ts` (TypeScript types) — mirrors the Python contracts exactly for frontend consumption
- Agent A's API endpoints accept and return these contract shapes
- Agent B's frontend consumes these shapes via the typed API client

Agent B can build UI against the contract types before Agent A's endpoints are live, using mocked API responses that conform to the contracts.

### Critical Cross-Agent Dependencies

| Agent B Task | Depends on Agent A | What's Needed |
|---|---|---|
| API client implementation | Canonical contracts + first endpoints | Contract shapes + running API |
| Realtime subscriptions | Supabase schema + RLS | Tables exist with realtime enabled |
| Match display UI | Match generation endpoint | Working match + explanation pipeline |
| Copilot UI | Copilot query endpoint | Working NL → query → results pipeline |
| Analytics dashboards | Signal + analytics endpoints | Working signal tracking + aggregate queries |

| Agent A Task | Depends on Agent B | What's Needed |
|---|---|---|
| (none critical) | — | Agent A has no hard dependencies on Agent B |

**Agent A is the critical path.** Agent B can build against contracts and mocked data from the start, but needs Agent A's endpoints to go live for integration. Agent A should prioritize: contracts → schema → core endpoints → matching pipeline → copilot.

---

## Build Sequence (8 Days, Parallel Agents)

### Day 1 — Foundation (PAIR)
- **Agent A:** Git init, monorepo structure, Supabase setup, canonical Python contracts, database schema + migrations, seed data, FastAPI skeleton with health check
- **Agent B:** Next.js init, Tailwind + shadcn/ui setup, TypeScript contracts (from Agent A's Python contracts), app router structure, layout shells for Mind + Mothership, auth flow with Supabase, demo login page
- **Coordination:** Agent A commits contracts first. Agent B mirrors to TypeScript.

### Day 2 — Core Data Pipeline
- **Agent A:** Adapter interfaces + Bullhorn/HubSpot/LinkedIn mocks, ingest + normalize pipeline, dedup pipeline, AI extraction pipeline (LLM + embedding generation), candidate CRUD endpoints, role CRUD endpoints
- **Agent B:** API client layer (typed), candidate list/detail views (Mothership), CV upload component with extraction animation, role posting guided workflow (Mind), shared candidate card component

### Day 3 — Matching Engine + Core UI
- **Agent A:** Structured matching, semantic matching (pgvector), composite scorer, LLM explanation generator, match endpoints, collection CRUD endpoints, signal event tracking foundation
- **Agent B:** Match results view with explanation cards and skill chips, collection management UI, Mind dashboard, Mothership talent partner dashboard, candidate browse view (Mind) with anonymization

### Day 4 — Handoffs + Quotes + Copilot
- **Agent A:** Handoff lifecycle endpoints, quote generation logic + endpoints, copilot NL parser + executor + formatter, copilot endpoint (streaming)
- **Agent B:** Handoff inbox/outbox UI, quote request + display flow (Mind), copilot sidebar component with streaming responses, pipeline kanban view (Mind)

### Day 5 — Admin + Analytics
- **Agent A:** Signal analytics aggregate queries, admin endpoints (platform stats, funnel data, partner performance), adapter health endpoints, AI pipeline monitoring endpoints, dedup review endpoints
- **Agent B:** Admin analytics dashboard with charts (recharts or similar), data quality review UI (side-by-side dedup), adapter health cards, AI pipeline monitoring view, user management UI

### Day 6 — Real-Time + Recommendations
- **Agent A:** Supabase Realtime triggers for matches/handoffs/quotes/pipeline changes, recommendation engine (based on signal history), proactive candidate suggestions for clients, trending skills aggregation
- **Agent B:** Realtime subscriptions wired to all views (live match notifications, handoff alerts, pipeline updates), recommendation display components, proactive suggestion cards on Mind dashboard, notification toast system

### Day 7 — Polish + Demo Mode
- **Agent A:** Seed data refinement (ensure realistic UK market data), edge case handling, API error responses, performance optimization (query tuning, caching), backend tests
- **Agent B:** Demo mode walkthrough overlay, loading/empty/error states everywhere, keyboard shortcuts, dark mode, responsive refinements, animation polish, frontend tests, accessibility pass

### Day 8 — Integration + Final Verification
- **Agent A:** Full integration testing, API documentation (auto-generated from FastAPI), fix any issues from Agent B's ISSUES.md, final seed data pass, deployment config
- **Agent B:** End-to-end flow testing across all personas, visual QA pass, demo rehearsal flow, README with setup instructions, final polish pass
- **Both:** Cross-validation, STATE.md fully completed, tagged release

---

## Success Criteria

The demo should achieve these reactions from non-technical recruitment partners:

1. **"It understands our world"** — realistic UK market data, recruitment terminology used correctly, workflows that mirror how recruitment actually works
2. **"The AI is actually useful"** — matching explanations that make sense, copilot that answers real questions, extraction that saves time
3. **"I can see how this would work"** — the handoff flow, the pool pricing, the multi-source ingestion all tell a coherent product story
4. **"This looks like a real product"** — polished UI, no rough edges, loading states, responsive, demo mode for guided presentation
5. **"This person could build our product"** — the architecture mirrors Mind + Mothership, the data contracts show data product thinking, the AI pipeline shows LLM competence with guardrails

---

## Out of Scope

- Real API integrations (adapters are mocked with realistic data)
- Payment processing
- Email/SMS delivery (notifications are in-app only)
- Mobile-optimized views (desktop-first, responsive is nice-to-have)
- Production deployment (local dev + demo is sufficient)
- User registration flow (pre-seeded demo accounts)
- File storage for CVs (text extraction only, no persistent file storage)
- Rate limiting, production security hardening
- Automated testing beyond smoke tests and key flow coverage
