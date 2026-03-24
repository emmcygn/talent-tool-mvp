# Handoff Log

Append-only. Both agents write here when completing a task that the other agent depends on.

**Format:**
```
## [Agent] Task [XX] → [Target Agent] | [Timestamp]
- **Delivered:** [what was produced]
- **Files:** [paths]
- **Import paths:** [how to use it]
- **Notes:** [anything the other agent needs to know]
```

---

## Agent A Task 01 → Agent B | 2026-03-24
- **Delivered:** All canonical Pydantic data contracts for the recruitment platform
- **Files:**
  - `backend/contracts/shared.py` — Enums (SeniorityLevel, AvailabilityStatus, RemotePolicy, RoleStatus, MatchStatus, ConfidenceLevel, HandoffStatus, QuoteStatus, Visibility, UserRole, SignalType) + value objects (ExtractedSkill, RequiredSkill, ExperienceEntry, SalaryRange, SkillMatch, CandidateSource)
  - `backend/contracts/candidate.py` — CandidateCreate, Candidate, CandidateAnonymized
  - `backend/contracts/role.py` — RoleCreate, Role
  - `backend/contracts/match.py` — Match
  - `backend/contracts/signal.py` — SignalCreate, Signal
  - `backend/contracts/handoff.py` — HandoffCreate, Handoff
  - `backend/contracts/quote.py` — QuoteRequest, Quote
  - `backend/contracts/collection.py` — CollectionCreate, Collection
  - `backend/contracts/__init__.py` — Re-exports all models
- **Import paths:** `from contracts.candidate import Candidate` (when running from `backend/`)
- **Notes:** Mirror these to `contracts/canonical.ts`. Pay special attention to `CandidateAnonymized` (client-facing view). All UUIDs are `uuid.UUID`, all datetimes are `datetime.datetime`. Pydantic v2 models.

## Agent A Task 02 → Agent B | 2026-03-24
- **Delivered:** Full PostgreSQL schema with pgvector, RLS, Realtime; Docker Compose for local dev
- **Files:**
  - `supabase/migrations/001_initial_schema.sql` — All tables, enums, indexes, RLS policies, Realtime config, updated_at triggers
  - `supabase/config.toml` — Supabase local dev configuration
  - `docker-compose.yml` — Backend + Supabase DB services
- **Notes:** Supabase Realtime enabled on `matches`, `handoffs`, `quotes`, `signals` — subscribe for live updates. RLS uses `auth.jwt() -> 'user_metadata' ->> 'role'` to determine access. JSONB used for structured arrays (skills, experience, etc.). HNSW indexes on candidate/role embeddings for vector similarity search.

## Agent B Task 01 → Agent A | 2026-03-24
- **Delivered:** Next.js 16 scaffold with TypeScript contracts, shadcn/ui, typed API client
- **Files:**
  - `contracts/canonical.ts` — All TypeScript types mirroring Python contracts
  - `frontend/lib/api.ts` — Typed API client skeleton
  - `frontend/lib/supabase.ts` — Supabase browser client
  - `frontend/lib/utils.ts` — cn() helper + formatting utilities
  - `frontend/lib/types.ts` — Re-export from canonical
- **Import paths:** `import type { Candidate } from "@/contracts/canonical"` or `from "@/lib/types"`
- **Notes:** Using Next.js 16 (not 14 as plan assumed). shadcn/ui toast is deprecated, using sonner instead. If you change Python contracts, note in HANDOFF.md so I can update the TS mirror.

## Agent B Task 02 → Agent A | 2026-03-24
- **Delivered:** Layout shells, demo login page, auth flow, proxy (middleware)
- **Files:**
  - `frontend/app/providers.tsx` — AuthContext with Supabase session management
  - `frontend/lib/auth.ts` — Demo user credentials and sign-in helpers
  - `frontend/app/login/page.tsx` — One-click persona login (3 roles)
  - `frontend/app/mind/layout.tsx` — Client top-nav layout
  - `frontend/app/mothership/layout.tsx` — Talent partner sidebar + copilot panel
  - `frontend/proxy.ts` — Auth guard with role-based routing
- **Notes:** Demo users defined in lib/auth.ts — seed data must use these exact credentials: alex.morgan@mothership.demo/demo-talent-2026 (talent_partner), jamie.chen@acmecorp.demo/demo-client-2026 (client), sam.patel@mothership.demo/demo-admin-2026 (admin). Next.js 16 renamed middleware.ts to proxy.ts.

## Agent A Task 13 → Agent B | 2026-03-24
- **Delivered:** Handoff lifecycle endpoints + quote generation with fee calculator
- **Files:**
  - `backend/services/handoff.py` — HandoffService: create, inbox, outbox, respond, attribution chain
  - `backend/services/quote.py` — QuoteService: generate_quote, fee calc by seniority, 20% pool discount
  - `backend/api/handoffs.py` — GET /api/handoffs/inbox, /outbox, POST /, PATCH /{id}/respond, GET /attribution/{id}
  - `backend/api/quotes.py` — POST /api/quotes/generate, GET /, GET /{id}, PATCH /{id}/status
- **Notes:**
  - Handoff inbox/outbox return separate lists. attribution_id links the full referral chain.
  - Quote `fee_breakdown` field: `{summary, seniority_level, base_fee, pool_discount?, savings_message?, final_fee, validity}`. Render as fee card.
  - Quote status flow: generated → sent → accepted/declined/expired (transitions enforced).
  - Fee schedule (GBP): junior=8K, mid=12K, senior=18K, lead=25K, principal=35K. Pool discount=20%.

## Agent A Task 14 → Agent B | 2026-03-24
- **Delivered:** NL copilot query layer with streaming SSE endpoint
- **Files:**
  - `backend/copilot/parser.py` — LLM-based NL→structured query parser
  - `backend/copilot/executor.py` — Supabase query executor
  - `backend/copilot/formatter.py` — Response formatter with actions and suggestions
  - `backend/api/copilot.py` — POST /api/copilot/query (full), POST /api/copilot/query/stream (SSE)
- **Notes:**
  - Non-streaming `/query` returns: `{summary, interpretation, query_executed, results, total_count, actions, followup_suggestions}`.
  - SSE phases: `parsing` → `parsed` → `executing` → `executed` → `results` (chunked, 5/chunk) → `complete` → `done`.
  - Session ID is client-generated UUID, sent with each query for multi-turn context (capped at 10 turns, in-memory).
  - `actions` have `label`, `action`, `description` — render as clickable buttons in copilot sidebar.

## Agent A Task 15 → Agent B | 2026-03-24
- **Delivered:** Admin endpoints for platform monitoring and user management
- **Files:**
  - `backend/api/admin.py` — All admin endpoints (stats, adapter health, pipeline status, dedup queue, user CRUD)
  - `supabase/migrations/005_admin_tables.sql` — dedup_queue + users tables
- **Notes:**
  - GET /api/admin/stats: `{totals, active, growth_7d}`.
  - GET /api/admin/pipeline/status: `{extraction_queue, confidence_distribution, embedding_coverage}`.
  - GET /api/admin/dedup/queue: enriched with both candidate summaries side-by-side.
  - All endpoints require admin role — show access-denied UI for non-admins.

## Agent A Task 16 → Agent B | 2026-03-24
- **Delivered:** Comprehensive UK-market seed data generation
- **Files:**
  - `backend/seed/organisations.py` — 12 UK tech companies
  - `backend/seed/users.py` — 9 demo users with stable UUIDs
  - `backend/seed/candidates.py` — 50+ candidates (8 hand-crafted + 42 generated)
  - `backend/seed/roles.py` — 15 roles across fintech/healthtech/SaaS/e-commerce
  - `backend/seed/generate.py` — Master orchestrator, generates supabase/seed.sql
  - `backend/tests/test_integration.py` — End-to-end API route tests
- **Notes:**
  - Demo user stable UUIDs: partners=`11111111-1111-1111-1111-{111..555}`, clients=`22222222-2222-2222-2222-{111..333}`, admin=`33333333-3333-3333-3333-111111111111`.
  - Run `cd backend && python -m seed.generate` to produce `supabase/seed.sql`.
  - Seed includes: 12+ handoffs, 18 quotes, 600+ signals (30 days), 8 dedup queue items, 6 collections.
  - Embeddings and matches are NOT pre-generated (require AI pipeline run after loading SQL).

## Agent B Task 04 → Agent A | 2026-03-24
- **Delivered:** Enhanced API client with auth + retry, full mock data layer
- **Files:**
  - `frontend/lib/api.ts` — Enhanced with auth token injection, ApiError class, retry logic
  - `frontend/lib/mock-data.ts` — 5 candidates, 3 roles, 5 matches, 3 collections
  - `frontend/lib/api-mock.ts` — Full mock implementation of ApiClient interface
  - `frontend/lib/api-client.ts` — Unified export switching real/mock via NEXT_PUBLIC_USE_MOCKS
- **Notes:** Frontend expects these new endpoint paths beyond Task 01: PATCH /api/candidates/:id, POST /api/candidates/upload, POST /api/candidates/extract, POST /api/roles/extract-requirements, PATCH /api/matches/:id/status, GET /api/matches/role/:id/anonymized, GET /api/users/me. Mock data uses deterministic UUIDs (00000000-0000-0000-0000-000000000010 etc.).
