# Autonomous Agent Orchestration Protocol

This document defines how two Claude Code terminals operate as Agent A and Agent B, working through a series of tasks autonomously.

---

## Terminal Setup

### Terminal 1 — Agent A

Start the session with:
```
You are Agent A (Data Engineer — Mothership Brain). Read plans/ORCHESTRATOR.md for your execution protocol, then check plans/STATE.md for your current task and begin work.
```

### Terminal 2 — Agent B

Start the session with:
```
You are Agent B (Product Engineer — Mind + Mothership UI). Read plans/ORCHESTRATOR.md for your execution protocol, then check plans/STATE.md for your current task and begin work.
```

---

## Execution Loop (per agent)

Every agent follows this loop continuously until all tasks are complete:

```
┌─────────────────────────────────────────────────┐
│  0. READ plans/ISSUES.md                        │
│     → Fix any open issues assigned to you       │
│     → This comes BEFORE starting new work       │
│                                                 │
│  1. READ plans/STATE.md                         │
│     → Find my next not_started task             │
│     → Check if dependencies are met             │
│                                                 │
│  2. IF dependency not met:                      │
│     → Work on non-blocking parts of the task    │
│     → OR skip to next non-blocked task          │
│     → Write blocker in STATE.md                 │
│                                                 │
│  3. READ plans/agent-{a,b}/task-XX.md           │
│     → This is the self-contained work order     │
│                                                 │
│  4. CHECK Prerequisites section                 │
│     → Verify listed files/modules exist         │
│     → If missing, check HANDOFF.md              │
│                                                 │
│  5. EXECUTE Checklist                           │
│     → Work through items sequentially           │
│     → Use Implementation Details for specs      │
│     → Commit after each logical unit            │
│                                                 │
│  5b. CROSS-VALIDATE                             │
│     → Import/smoke-test modules you depend      │
│       on from the other agent                   │
│     → If something is broken, file an issue     │
│       in plans/ISSUES.md                        │
│                                                 │
│  6. VERIFY Acceptance Criteria                  │
│     → Run the exact commands listed             │
│     → If failing in YOUR code, fix it           │
│     → If failing in OTHER agent's code,         │
│       file ISSUES.md with BLOCKER severity      │
│                                                 │
│  7. VALIDATION GATE                             │
│     → Agent A: cd backend && python -m pytest   │
│     → Agent B: cd frontend && npm run build     │
│     → MUST pass before marking complete         │
│                                                 │
│  8. POST-TASK PROTOCOL                          │
│     → Update STATE.md: status → completed       │
│     → Write HANDOFF.md entry if other agent     │
│       depends on this task's output             │
│     → Commit: "Agent {A|B} Task XX: {title}"    │
│                                                 │
│  9. LOOP → back to step 0                       │
└─────────────────────────────────────────────────┘
```

---

## Git Protocol

Both agents work on the **same branch** (`main`). To avoid conflicts:

1. **Pull before starting each task:** `git pull --rebase` (if remote set up)
2. **Commit after each task** with format: `Agent {A|B} Task {XX}: {title}`
3. **Never force push.**
4. **Agents own different files** — conflicts should be rare. Shared files:
   - `plans/STATE.md` — both write (different sections)
   - `plans/HANDOFF.md` — both write (append-only)
   - `plans/ISSUES.md` — both write (append-only)
   - `tasks/lessons.md` — both write (append-only)

5. **If merge conflict on shared files:** take both changes (append-only by design)

### File Ownership

| Files | Owner | Rule |
|-------|-------|------|
| `backend/**` | Agent A | Agent A creates and modifies all backend code |
| `supabase/**` | Agent A | Agent A owns database schema and migrations |
| `backend/contracts/**` | Agent A | Source of truth for data contracts. Changes require HANDOFF.md entry. |
| `contracts/canonical.ts` | Agent B | Agent B mirrors Python contracts to TypeScript |
| `frontend/**` | Agent B | Agent B creates and modifies all frontend code |
| `docker-compose.yml` | Agent A | Agent A owns infrastructure config |
| `.env.example` | Agent A | Agent A creates, both reference |

---

## Pairing Tasks

### Bootstrap (Task 01 — both agents)
- **Agent A** creates: monorepo structure, Python backend scaffold, canonical Pydantic contracts, requirements.txt, config
- **Agent B** creates: Next.js scaffold, TypeScript canonical types (mirrored from Python), Tailwind + shadcn/ui setup, API client skeleton, Supabase client
- **Coordination:** Agent A commits first (contracts are the interface). Agent B then commits, importing contract types.
- **Both verify:** Agent A: `pytest` passes. Agent B: `npm run build` passes.

---

## Dependency Resolution

When a task has a dependency (noted in STATE.md):

1. Check STATE.md — is the dependency task marked `completed`?
2. Check HANDOFF.md — is there a handoff entry with file paths?
3. If YES to both → proceed
4. If NO → skip to next non-blocked task, or work on parts that don't require the dependency

### Critical Cross-Agent Dependencies

| Agent B Task | Depends on Agent A | What's needed |
|---|---|---|
| B-01 | A-01 (contracts) | `backend/contracts/*.py` — types to mirror |
| B-04 | A-01 (contracts) | Contract shapes for mock data |
| B-14 | A-15 (admin endpoints) | Admin API endpoints for analytics/quality data |

| Agent A Task | Depends on Agent B | What's needed |
|---|---|---|
| (none critical) | — | Agent A has no hard dependencies on Agent B |

**Agent A is the critical path.** Agent B can build against contracts and mock data from the start.

---

## Validation Gate & Retry Protocol

### Validation Commands

```bash
# Agent A
cd backend && python -m pytest -v

# Agent B
cd frontend && npm run build && npm run lint
```

### Retry Protocol

1. **Attempt 1:** Read error, fix root cause, re-run
2. **Attempt 2:** Re-think approach — implementation may be wrong
3. **Attempt 3:** Check if failure is in other agent's code:
   - YES → file BLOCKER in ISSUES.md, skip to non-blocked work
   - NO → write problem in STATE.md, move on
4. **Never:** Brute-force retry same approach. If it failed twice, approach is wrong.
5. **Never:** Mark task complete if validation hasn't passed.

---

## Session Recovery

If a terminal crashes or context is lost:

1. Start a new Claude Code session with identity prompt
2. Run `plans/BOOTSTRAP.md` recovery checklist
3. Read `plans/ISSUES.md` → fix open issues assigned to you
4. Read `plans/STATE.md` → find last completed task → resume from next
5. Read `plans/HANDOFF.md` → catch up on other agent's deliveries
6. Read `tasks/lessons.md` → load corrections

---

## Success Condition

Both agents have completed all 16 tasks each. STATE.md shows all 32 rows as `completed`. The following all succeed:

```bash
cd backend && python -m pytest -v
cd frontend && npm run build && npm run lint
# Frontend serves at localhost:3000
# Backend serves at localhost:8000
# Demo login works for all 3 personas
# AI matching returns results with explanations
# Copilot responds to natural language queries
```
