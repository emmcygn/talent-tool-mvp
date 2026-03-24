# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**RecruitTech PoC** — A recruitment platform mirroring the Mind + Mothership architecture: AI-powered candidate matching, copilot dashboards, and multi-persona workflows for UK recruitment partners.

- **Source layout:** `backend/` (Python 3.12 / FastAPI) + `frontend/` (Next.js 14 / TypeScript)
- **Build system:** pip (backend), npm (frontend)
- **Key deliverables:** Mind (external hiring manager UI), Mothership (internal talent partner + admin dashboards with copilot)

## Build & Dev Commands

```bash
# Backend
cd backend && pip install -r requirements.txt
cd backend && python -m pytest -v                    # run tests
cd backend && uvicorn main:app --reload --port 8000  # dev server

# Frontend
cd frontend && npm install
cd frontend && npm run build                         # build
cd frontend && npm run lint                          # lint
cd frontend && npm run dev                           # dev server (port 3000)

# Validation gate (must pass before completing any task)
cd backend && python -m pytest -v
cd frontend && npm run build && npm run lint
```

## Architecture

```
recruittech/
├── backend/              # Python FastAPI — Mothership engine
│   ├── api/              # REST endpoints
│   ├── adapters/         # CRM/ATS integrations (Bullhorn, HubSpot, LinkedIn — mocked)
│   ├── contracts/        # Canonical Pydantic data contracts (SOURCE OF TRUTH)
│   ├── pipelines/        # ETL: ingest → normalize → deduplicate → enrich
│   ├── matching/         # Hybrid AI: structured + semantic + explanation
│   ├── copilot/          # NL → query → results
│   ├── signals/          # Event tracking + analytics
│   ├── services/         # Business logic (handoffs, quotes, collections)
│   ├── seed/             # Demo data generation
│   └── tests/            # pytest tests
├── frontend/             # Next.js 14 — Mind + Mothership UI
│   ├── app/mind/         # Client / hiring manager views
│   ├── app/mothership/   # Talent partner + admin views
│   ├── components/       # UI components (shadcn/ui + custom)
│   └── lib/              # API client, Supabase client, utilities
├── contracts/
│   └── canonical.ts      # TypeScript mirror of Python contracts
├── supabase/             # Schema, migrations, RLS policies
└── plans/                # Agent orchestration
```

**Data flow:** Adapters → Ingest → Normalize → Deduplicate → Enrich (LLM extraction + embeddings) → Match (structured + semantic + composite score) → Explain (LLM) → Display (UI)

---

## Agent Execution Model

This repo is built by **two AI agents working in parallel** with self-contained task plans. All implementation is agent-first — Claude Code IS the engineering team.

**Full orchestration protocol:** `plans/ORCHESTRATOR.md`
**Pre-flight checklist:** `plans/BOOTSTRAP.md`
**Progress tracker:** `plans/STATE.md`
**Inter-agent comms:** `plans/HANDOFF.md`
**Cross-agent issues:** `plans/ISSUES.md`
**Shared lessons:** `tasks/lessons.md`

### Agent A — Data Engineer (Mothership Brain)
**Owns:** `backend/`, `supabase/`, `docker-compose.yml`
**Plans:** `plans/agent-a/task-01.md` through `task-16.md`

### Agent B — Product Engineer (Mind + Mothership UI)
**Owns:** `frontend/`, `contracts/canonical.ts`
**Plans:** `plans/agent-b/task-01.md` through `task-16.md`

### How to Execute a Task

1. Read `plans/ISSUES.md` → fix any open issues assigned to you FIRST
2. Read `plans/STATE.md` → find your next `not_started` task
3. Check dependencies — is the blocking task marked `completed`?
4. Read the task file (e.g., `plans/agent-a/task-07.md`) — it is fully self-contained
5. Check **Prerequisites** — verify the files/modules listed actually exist
6. Work through the **Checklist** sequentially, using **Implementation Details** for specifics
7. **Cross-validate:** After implementing, import and smoke-test any modules you depend on from the other agent.
8. Validate against **Acceptance Criteria**
9. Run validation gate (see Build & Dev Commands above) — fix failures before proceeding
10. Update `plans/STATE.md` — mark task as `completed` with timestamp
11. Write `plans/HANDOFF.md` entry if the other agent depends on this task's output
12. Commit: `Agent {A|B} Task {XX}: {title}`
13. Loop → back to step 1

### Agent Coordination Rules

- **The contracts in `backend/contracts/` are the interface boundary.** Agent A produces data in these shapes. Agent B consumes them via `contracts/canonical.ts`.
- **Agent A is the critical path** for core pipeline components. Agent B can build UI against mock data before Agent A's implementations land.
- **Never modify the other agent's owned files** without noting it in HANDOFF.md.
- **Session recovery:** Re-read STATE.md → find last completed task → resume from next.

---

## Workflow Orchestration

### 1. Plan First
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- Task plan files (`plans/agent-{a,b}/task-XX.md`) are the master plans

### 2. Verification Before Done
- Never mark a task complete without proving it works
- Run validation gate after every task
- Ask yourself: "Would this survive a code review from a senior engineer?"

### 3. Autonomous Bug Fixing
- When given a bug report: just fix it
- Point at logs, errors, failing tests — then resolve them

---

## Known Plan Issues (fix during implementation)

- **Python import convention:** Task files are inconsistent — some use `from backend.config import settings` (package-style), others use `from config import settings` (relative). **Settle on one convention in Task A-03** and follow it consistently. If running from project root with `cd backend && uvicorn main:app`, use relative imports (no `backend.` prefix). If running as a package, use the prefix. Whichever you choose, fix all subsequent imports to match.
- **`api/deps.py` module:** Multiple tasks reference `get_supabase_admin()` and `get_current_user()` as dependencies. Task A-03 creates `api/deps.py` — ensure it provides these.
- **Match scoring:** The `Match` contract has `structured_score` and `semantic_score` but no separate `experience_score`. The composite is 40/35/25 (skill/semantic/experience). Either add an `experience_score` field or compute it from overall score minus the weighted other two.

## Core Principles
- **Simplicity First**: Make every change as simple as possible
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary
- **Polish Matters**: Non-technical partners are the audience — every UI surface should feel finished
