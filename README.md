> Engineers: see [Technical README](TECHNICAL-README.md) for setup, architecture, and API docs.

# talent-tool-mvp

A proof-of-concept recruitment platform built to demonstrate the **Mind + Mothership** architecture -- two interconnected products that together form an AI-powered operating system for modern recruitment agencies.

**Live Demo:**
- Frontend: [talent-tool-mvp.vercel.app](https://talent-tool-mvp.vercel.app)
- Backend API: [talent-tool-mvp-production.up.railway.app](https://talent-tool-mvp-production.up.railway.app)

---

## What is this?

talent-tool-mvp is a working prototype of a dual-product recruitment platform. It mirrors the architecture described in the Wave Talent founding engineer brief: an external-facing product for hiring managers (**Mind**) and an internal operating system for talent partners and admins (**Mothership**), unified by a shared AI-powered data layer.

---

## The Problem

Recruitment agencies today operate with fragmented tools:

| Pain Point | Impact |
|---|---|
| Candidate data scattered across ATS, CRM, LinkedIn, spreadsheets | Talent partners waste hours searching and cross-referencing |
| Manual candidate-to-role matching based on gut feel | Inconsistent quality, missed matches, slow turnaround |
| No structured handoff process between talent partners | Lost context, duplicated effort, attribution disputes |
| Clients have no visibility into the sourcing process | Frustration, constant status requests, slow decision-making |
| No feedback loop from placements back to sourcing | Matching quality never improves |

---

## The Solution

Two products, one shared intelligence layer:

| Product | Users | Purpose |
|---|---|---|
| **Mind** | Hiring managers / clients | Post roles, browse AI-matched candidates, request introductions with transparent pricing |
| **Mothership** | Talent partners + admins | Ingest candidates from any source, run AI matching, manage collections, hand off leads, query the system with natural language |

Both products share a unified data layer with AI-powered candidate extraction, hybrid matching, and a signal-tracking system that makes the platform smarter over time.

---

## Product Architecture

```mermaid
graph TB
    subgraph Mind ["Mind (External)"]
        M1[Role Posting]
        M2[Candidate Browse]
        M3[Quote & Intro Requests]
        M4[Hiring Pipeline]
    end

    subgraph Mothership ["Mothership (Internal)"]
        MS1[Candidate Ingestion]
        MS2[AI Matching Engine]
        MS3[Copilot NL Queries]
        MS4[Collections & Handoffs]
        MS5[Admin Analytics]
    end

    subgraph DataLayer ["Shared Data & AI Layer"]
        D1[(Supabase PostgreSQL + pgvector)]
        D2[OpenAI GPT-4o]
        D3[Signal Event Stream]
        D4[Embedding Store]
    end

    Mind --> DataLayer
    Mothership --> DataLayer
    D3 -->|Activity feeds, analytics| Mothership
    D3 -->|Notifications, recommendations| Mind
    D2 -->|Skill extraction, match explanations, copilot| Mothership
    D2 -->|Role requirement extraction| Mind
```

---

## Three Personas

### Talent Partner (Mothership)

The power user. Talent partners ingest candidates from multiple sources, review AI extractions, run matching against open roles, curate collections, and hand off leads to other partners.

```mermaid
journey
    title Talent Partner Journey
    section Ingest
        Upload CV or sync from ATS: 5: Talent Partner
        Review AI-extracted profile: 4: Talent Partner
        Correct low-confidence fields: 3: Talent Partner
        Auto-dedup check runs: 5: System
    section Match
        Select open role: 5: Talent Partner
        View ranked candidates with explanations: 5: Talent Partner
        Shortlist strong matches: 5: Talent Partner
        Dismiss with reason: 4: Talent Partner
    section Collaborate
        Create themed collection: 5: Talent Partner
        Share with specific partners: 4: Talent Partner
        Hand off candidates to partner: 5: Talent Partner
        Track attribution through to placement: 4: System
    section Query
        Ask copilot a question: 5: Talent Partner
        Review structured query and results: 5: Talent Partner
        Refine with follow-up: 4: Talent Partner
```

### Client / Hiring Manager (Mind)

The external user. Clients post roles through a guided workflow, browse AI-matched candidates (anonymized until intro), request introductions with transparent pricing, and track their hiring pipeline.

```mermaid
journey
    title Hiring Manager Journey
    section Post Role
        Enter role title and description: 5: Hiring Manager
        Review AI-extracted requirements: 4: Hiring Manager
        Confirm skills, seniority, location: 5: Hiring Manager
        Publish role: 5: Hiring Manager
    section Review Candidates
        Browse ranked matches with explanations: 5: Hiring Manager
        View skill chips and confidence badges: 4: Hiring Manager
        Shortlist promising candidates: 5: Hiring Manager
    section Request Intro
        Click Request Intro on shortlisted candidate: 5: Hiring Manager
        Review quote with pool discount breakdown: 4: Hiring Manager
        Accept quote: 5: Hiring Manager
    section Track Pipeline
        Move candidates through kanban stages: 5: Hiring Manager
        View progress across all roles: 4: Hiring Manager
```

### Admin / Ops (Mothership)

Platform oversight. Admins monitor data quality, review auto-merges, track adapter health, analyze funnel metrics, and use the copilot with full platform-wide access.

```mermaid
journey
    title Admin Journey
    section Monitor
        View platform-wide analytics dashboard: 5: Admin
        Check adapter sync health: 4: Admin
        Review AI pipeline status: 4: Admin
    section Quality
        Review auto-merged candidate records: 5: Admin
        Approve or split incorrect merges: 4: Admin
        Flag low-confidence extractions: 3: Admin
    section Analyze
        View placement funnel drop-off: 5: Admin
        Track trending skills across roles: 4: Admin
        Monitor partner performance metrics: 4: Admin
    section Copilot
        Ask platform-wide queries: 5: Admin
        Generate custom reports: 4: Admin
```

---

## AI-Powered Features

### Skill Extraction from CVs

When a candidate is ingested (via CV upload, text paste, or adapter sync), the AI extracts structured data in real time:

| Extracted Field | Example | Confidence Scoring |
|---|---|---|
| Skills with years | Python (6 years), React (3 years) | Per-field confidence 0-1 |
| Experience timeline | Senior Engineer at Monzo, 2021-2024 | Verified against CV text |
| Seniority level | Senior | Inferred from title + years |
| Salary expectation | 85k-100k GBP | When stated or inferable |
| Availability | Immediate / 1 month / 3 months | From notice period context |
| Industries | Fintech, SaaS | From company + role context |

Fields below 0.7 confidence are highlighted for human review -- the AI suggests, the human confirms.

### Hybrid Matching Pipeline

```mermaid
graph LR
    A[Role Posted] --> B[Structured Filter]
    B -->|Location, availability, min experience| C[Semantic Search]
    C -->|pgvector cosine similarity, top 50| D[Skill Overlap Scoring]
    D -->|Per-skill match: matched, partial, missing| E[Composite Score]
    E -->|40% skills + 35% semantic + 25% experience| F[Rank & Bucket]
    F --> G["Strong (>0.75)"]
    F --> H["Good (0.50-0.75)"]
    F --> I["Possible (0.30-0.50)"]
    G --> J[LLM Explanation]
    H --> J
    J -->|Plain English summary, strengths, gaps| K[Display to User]
```

Every match includes:
- A plain-English explanation ("6 years of Python backend experience aligns well with the requirement")
- Bullet-point strengths and gaps
- A one-line recommendation
- Full scoring breakdown available for transparency

### Copilot Natural Language Queries

Talent partners and admins can query the system in plain English:

```mermaid
graph LR
    A["'Who are my best Python candidates in London?'"] --> B[NL Parser]
    B -->|LLM translates to structured query| C[Query Executor]
    C -->|Runs against Supabase| D[Result Formatter]
    D -->|Results + actions + follow-ups| E[Display with Transparency]
    E -->|Shows: query interpreted, filters applied, result count| F[One-Click Actions]
```

The copilot shows exactly what query it ran -- no black box. Results include one-click actions (shortlist, add to collection, refer to partner) and follow-up suggestions.

---

## Key Workflows

### Candidate Ingestion to Placement

The complete lifecycle of a candidate through the platform:

```mermaid
graph TB
    subgraph Sources ["Data Sources"]
        S1[CV Upload]
        S2[Bullhorn ATS]
        S3[HubSpot CRM]
        S4[LinkedIn Recruiter]
    end

    subgraph Pipeline ["AI Pipeline"]
        P1[Ingest Raw Data]
        P2[Normalize to Canonical Format]
        P3[Deduplicate & Identity Resolution]
        P4[AI Extraction: Skills, Experience, Seniority]
        P5[Generate Embeddings]
    end

    subgraph Matching ["Matching"]
        M1[Role Published by Client]
        M2[Hybrid Match: Structured + Semantic]
        M3[LLM Generates Explanations]
        M4[Candidates Ranked & Bucketed]
    end

    subgraph Placement ["Placement Flow"]
        PL1[Client Reviews Matches]
        PL2[Client Shortlists]
        PL3[Client Requests Intro + Quote]
        PL4[Talent Partner Notified]
        PL5[Interview Process]
        PL6[Placement Made]
    end

    Sources --> P1 --> P2 --> P3 --> P4 --> P5
    M1 --> M2
    P5 --> M2 --> M3 --> M4
    M4 --> PL1 --> PL2 --> PL3 --> PL4 --> PL5 --> PL6
```

### Handoff Between Talent Partners

```mermaid
sequenceDiagram
    participant PA as Partner A
    participant System as Platform
    participant PB as Partner B

    PA->>System: Select candidates for handoff
    PA->>System: Choose receiving partner + add context notes
    PA->>System: Optionally link to a specific role
    System->>PB: Real-time notification: new handoff received
    PB->>System: Review candidates with Partner A's context
    alt Accepted
        PB->>System: Accept handoff with notes
        System->>PA: Notification: handoff accepted
        Note over System: Attribution chain preserved through to placement
    else Declined
        PB->>System: Decline with reason
        System->>PA: Notification: handoff declined with reason
    end
```

### Quote and Introduction Request

```mermaid
sequenceDiagram
    participant Client as Hiring Manager
    participant System as Platform
    participant TP as Talent Partner

    Client->>System: Click "Request Intro" on shortlisted candidate
    System->>System: Generate quote with pricing breakdown
    alt Pool Candidate
        System->>Client: Standard fee with pool discount applied
        Note over Client: "Pre-vetted talent network -- reduced fee"
    else Exclusive Candidate
        System->>Client: Standard placement fee
    end
    Client->>System: Accept quote
    System->>TP: Notification: intro requested + quote accepted
    TP->>System: Facilitate introduction
```

---

## Feature Comparison: Mind vs Mothership

| Capability | Mind (Clients) | Mothership (Internal) |
|---|---|---|
| View candidates | Anonymized until intro request | Full profiles with source tracking |
| Post roles | Guided step-by-step workflow | Direct entry or bulk import |
| AI matching | View matched candidates with explanations | Run matching, configure weights, review scoring |
| Copilot | Not available | Full NL query interface |
| Collections | Not available | Create, share, manage themed groups |
| Handoffs | Not available | Send/receive between partners |
| Pricing | View quotes with fee breakdown | Configure pricing tiers |
| Analytics | Own pipeline metrics | Platform-wide funnel, trends, performance |
| Pipeline | Kanban board for own roles | Cross-role, cross-client visibility |
| Dedup review | Not available | Side-by-side merge/split decisions |

---

## Demo Access

The platform ships with pre-seeded demo accounts for each persona. On the login page, use the one-click persona selector to sign in as:

| Persona | Email | What You Will See |
|---|---|---|
| Talent Partner | `partner@demo.recruittech.io` | Mothership dashboard with active roles, candidate pipeline, copilot sidebar, collections, handoff inbox |
| Hiring Manager | `client@demo.recruittech.io` | Mind dashboard with posted roles, AI-matched candidates, quote requests, hiring pipeline |
| Admin | `admin@demo.recruittech.io` | Full Mothership with analytics dashboards, data quality review, adapter monitoring, platform-wide copilot |

Demo data includes 50+ realistic UK-market candidates, 15+ roles across fintech/healthtech/SaaS, pre-generated matches with explanations, and signal history populating the analytics dashboards.

---

## Built With

| Layer | Technology | Role in the Platform |
|---|---|---|
| **Frontend** | Next.js 16 (App Router), TypeScript, Tailwind CSS, shadcn/ui | Mind + Mothership UI with dark luxe theme |
| **Backend** | FastAPI (Python 3.12) | REST API powering all data operations, AI pipelines, and business logic |
| **Database** | Supabase (PostgreSQL + pgvector + Auth + Realtime + RLS) | Unified data layer with vector search, row-level security, and real-time subscriptions |
| **AI** | OpenAI GPT-4o + text-embedding-3-small | Skill extraction, match explanations, copilot query parsing, semantic embeddings |
| **Engineering** | Dual AI agents via agents-scaffolding framework | Agent A (Data Engineer) and Agent B (Product Engineer) working in parallel |

### How It Was Built

This platform was constructed by two autonomous AI agents working in parallel over 8 days:

- **Agent A (Data Engineer)** built the entire backend: data contracts, database schema, ETL pipelines, AI matching engine, copilot query layer, signal tracking, and all API endpoints.
- **Agent B (Product Engineer)** built the entire frontend: all three persona views, copilot UI, candidate cards, guided workflows, admin dashboards, and the dark luxe visual theme.

The agents coordinated through a shared contract boundary (canonical Pydantic/TypeScript types) and an orchestration framework (`plans/` directory) that managed task sequencing, dependency resolution, handoffs, and issue tracking -- all without human intervention during execution.

---

## Repository

[github.com/emmcygn/talent-tool-mvp](https://github.com/emmcygn/talent-tool-mvp)
