# Cross-Agent Issues

Append-only. Both agents write here when they find bugs, blockers, or need changes in the other agent's code.

**Severity levels:**
- `BLOCKER` — Cannot proceed until resolved. Other agent must fix ASAP.
- `BUG` — Something is broken but can be worked around.
- `WARN` — Potential issue, not blocking.
- `REQUEST` — Feature or change request.

**Format:**
```
## Issue #N — [SEVERITY] [Title]
- **Filed by:** Agent [A|B] | [Timestamp]
- **Assigned to:** Agent [A|B]
- **Status:** open | resolved
- **Description:** [what's wrong]
- **Files:** [affected files]
- **Expected:** [what should happen]
- **Actual:** [what happens instead]
- **Resolution:** [how it was fixed, if resolved]
```

---

## Issue #1 — [BUG] Match TypeScript contract missing `experience_score`
- **Filed by:** Agent A | 2026-03-24
- **Assigned to:** Agent B
- **Status:** open
- **Description:** Python `Match` model now has `experience_score: float = 0.0` (added to resolve CLAUDE.md known issue). The TypeScript mirror at `contracts/canonical.ts` line 151 does not include this field. Backend responses will include it but the TS type won't recognize it.
- **Files:** `contracts/canonical.ts` (Match interface, around line 151)
- **Expected:** `experience_score: number;` field present in the TS Match interface
- **Actual:** Field is missing
- **Resolution:** Add `experience_score: number;` after `semantic_score: number;` in the Match interface.

---

## Issue #2 — [BUG] Demo user credentials don't match between frontend and backend seed data
- **Filed by:** Agent A | 2026-03-24
- **Assigned to:** Agent B
- **Status:** open
- **Description:** Frontend `lib/auth.ts` uses demo credentials `alex.morgan@mothership.demo` / `demo-talent-2026`, `jamie.chen@acmecorp.demo` / `demo-client-2026`, `sam.patel@mothership.demo` / `demo-admin-2026`. But backend seed data at `backend/seed/users.py` defines users as `sarah.chen@recruittech.demo` / `demo-partner-1`, `alex.thompson@monzo.demo` / `demo-client-1`, `admin@recruittech.demo` / `demo-admin-1`. Demo login will always fail because the emails and passwords don't match.
- **Files:** `frontend/lib/auth.ts`, `backend/seed/users.py`
- **Expected:** Same demo credentials in both frontend auth config and backend seed data
- **Actual:** Completely different emails and passwords
- **Resolution:** Either Agent B updates `lib/auth.ts` to match Agent A's seed users, or Agent A updates `seed/users.py` to match Agent B's credentials. Recommend Agent B aligns to Agent A since seed data is the database source of truth.

---

## Issue #3 — [WARN] Mock data matches missing `experience_score`
- **Filed by:** Agent A | 2026-03-24
- **Assigned to:** Agent B
- **Status:** open
- **Description:** All 5 mock matches in `frontend/lib/mock-data.ts` lack the `experience_score` field. Backend always returns this field (defaults to `0.0`). Mock data should include it for consistency.
- **Files:** `frontend/lib/mock-data.ts` (MOCK_MATCHES, lines 331-486)
- **Expected:** Each mock match includes `experience_score: number`
- **Actual:** Field is absent; will be `undefined` when consuming code expects `number`
- **Resolution:** Add `experience_score: 0.95` (or appropriate value) to each mock match after `semantic_score`.

---

## Issue #4 — [WARN] Frontend admin API paths don't match backend routes
- **Filed by:** Agent A | 2026-03-24
- **Assigned to:** Agent B
- **Status:** open
- **Description:** Frontend `api.ts` calls `GET /api/admin/funnel` but backend has this at `GET /api/signals/analytics/funnel`. Frontend calls `GET /api/admin/adapters` but backend has `GET /api/admin/adapters/health`. These will 404.
- **Files:** `frontend/lib/api.ts` (lines 174-176)
- **Expected:** Frontend calls correct backend paths
- **Actual:** Path mismatch causes 404
- **Resolution:** Update frontend api.ts: `funnelData` → `/api/signals/analytics/funnel`, `adapterHealth` → `/api/admin/adapters/health`.
