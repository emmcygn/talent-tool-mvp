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
