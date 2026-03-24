# Agent A — Task 01: Bootstrap — Project Structure + Canonical Contracts

## Mission
Set up the Python backend project structure and define all canonical Pydantic data contracts that serve as the interface boundary between Agent A and Agent B.

## Context
This is Day 1, the first task. Nothing exists yet. This is a PAIR task — Agent B is simultaneously setting up the Next.js frontend and will mirror these contracts to TypeScript. Agent A must commit contracts first so Agent B has a source of truth to mirror.

## Prerequisites
- Python 3.12+ installed
- Git repository initialized
- `pip` available

## Checklist
- [ ] Create monorepo directory structure (`backend/`, `supabase/`, `contracts/`, `plans/`, `tasks/`)
- [ ] Create `backend/requirements.txt` with all dependencies
- [ ] Create `backend/config.py` with settings class
- [ ] Create `backend/contracts/shared.py` with all shared enums and value objects
- [ ] Create `backend/contracts/candidate.py` with Candidate model
- [ ] Create `backend/contracts/role.py` with Role model
- [ ] Create `backend/contracts/match.py` with Match model
- [ ] Create `backend/contracts/signal.py` with Signal model
- [ ] Create `backend/contracts/handoff.py` with Handoff model
- [ ] Create `backend/contracts/quote.py` with Quote model
- [ ] Create `backend/contracts/collection.py` with Collection model
- [ ] Create `backend/contracts/__init__.py` re-exporting all models
- [ ] Create `backend/tests/test_contracts.py` — validate all models instantiate correctly
- [ ] Run tests, verify pass
- [ ] Commit: "Agent A Task 01: Bootstrap — project structure + canonical contracts"

## Implementation Details

### Requirements (`backend/requirements.txt`)

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
pydantic-settings==2.7.1
supabase==2.11.0
openai==1.58.1
httpx==0.28.1
python-jose[cryptography]==3.3.0
python-multipart==0.0.18
pgvector==0.3.6
psycopg2-binary==2.9.10
sqlalchemy==2.0.36
Levenshtein==0.26.1
pytest==8.3.4
pytest-asyncio==0.24.0
```

### Config (`backend/config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str = "http://localhost:54321"
    supabase_key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # local dev default
    supabase_service_key: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    database_url: str = "postgresql://postgres:postgres@localhost:54322/postgres"
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"

settings = Settings()
```

### Shared Enums (`backend/contracts/shared.py`)

```python
from enum import Enum
from pydantic import BaseModel
from decimal import Decimal

class SeniorityLevel(str, Enum):
    junior = "junior"
    mid = "mid"
    senior = "senior"
    lead = "lead"
    principal = "principal"

class AvailabilityStatus(str, Enum):
    immediate = "immediate"
    one_month = "1_month"
    three_months = "3_months"
    not_looking = "not_looking"

class RemotePolicy(str, Enum):
    onsite = "onsite"
    hybrid = "hybrid"
    remote = "remote"

class RoleStatus(str, Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    filled = "filled"
    closed = "closed"

class MatchStatus(str, Enum):
    generated = "generated"
    shortlisted = "shortlisted"
    dismissed = "dismissed"
    intro_requested = "intro_requested"

class ConfidenceLevel(str, Enum):
    strong = "strong"
    good = "good"
    possible = "possible"

class HandoffStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    expired = "expired"

class QuoteStatus(str, Enum):
    generated = "generated"
    sent = "sent"
    accepted = "accepted"
    declined = "declined"
    expired = "expired"

class Visibility(str, Enum):
    private = "private"
    shared_specific = "shared_specific"
    shared_all = "shared_all"

class UserRole(str, Enum):
    talent_partner = "talent_partner"
    client = "client"
    admin = "admin"

class SignalType(str, Enum):
    candidate_ingested = "candidate_ingested"
    candidate_viewed = "candidate_viewed"
    candidate_shortlisted = "candidate_shortlisted"
    candidate_dismissed = "candidate_dismissed"
    match_generated = "match_generated"
    intro_requested = "intro_requested"
    handoff_sent = "handoff_sent"
    handoff_accepted = "handoff_accepted"
    handoff_declined = "handoff_declined"
    quote_generated = "quote_generated"
    placement_made = "placement_made"
    copilot_query = "copilot_query"

class ExtractedSkill(BaseModel):
    name: str
    years: float | None = None
    confidence: float = 1.0

class RequiredSkill(BaseModel):
    name: str
    min_years: float | None = None
    importance: str = "required"  # required | preferred

class ExperienceEntry(BaseModel):
    company: str
    title: str
    duration_months: int | None = None
    industry: str | None = None

class SalaryRange(BaseModel):
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    currency: str = "GBP"

class SkillMatch(BaseModel):
    skill_name: str
    status: str  # matched | partial | missing
    candidate_years: float | None = None
    required_years: float | None = None

class CandidateSource(BaseModel):
    adapter_name: str
    external_id: str
    ingested_at: str  # ISO datetime string
```

### Candidate Contract (`backend/contracts/candidate.py`)

```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from .shared import (
    ExtractedSkill, ExperienceEntry, SeniorityLevel,
    SalaryRange, AvailabilityStatus, CandidateSource
)

class CandidateCreate(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    cv_text: str | None = None
    profile_text: str | None = None

class Candidate(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    skills: list[ExtractedSkill] = []
    experience: list[ExperienceEntry] = []
    seniority: SeniorityLevel | None = None
    salary_expectation: SalaryRange | None = None
    availability: AvailabilityStatus | None = None
    industries: list[str] = []
    cv_text: str | None = None
    profile_text: str | None = None
    sources: list[CandidateSource] = []
    dedup_group: UUID | None = None
    dedup_confidence: float | None = None
    embedding: list[float] | None = None
    extraction_confidence: float | None = None
    extraction_flags: list[str] = []
    created_at: datetime
    updated_at: datetime
    created_by: UUID

class CandidateAnonymized(BaseModel):
    """Client-facing view — no full name, no company names."""
    id: UUID
    first_name: str
    last_initial: str
    location: str | None = None
    skills: list[ExtractedSkill] = []
    seniority: SeniorityLevel | None = None
    availability: AvailabilityStatus | None = None
    industries: list[str] = []
    experience_years: int | None = None
    is_pool_candidate: bool = False
```

### Role Contract (`backend/contracts/role.py`)

```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from .shared import (
    RequiredSkill, SeniorityLevel, SalaryRange,
    RemotePolicy, RoleStatus
)

class RoleCreate(BaseModel):
    title: str
    description: str
    organisation_id: UUID
    salary_band: SalaryRange | None = None
    location: str | None = None
    remote_policy: RemotePolicy = RemotePolicy.hybrid

class Role(BaseModel):
    id: UUID
    title: str
    description: str
    organisation_id: UUID
    required_skills: list[RequiredSkill] = []
    preferred_skills: list[RequiredSkill] = []
    seniority: SeniorityLevel | None = None
    salary_band: SalaryRange | None = None
    location: str | None = None
    remote_policy: RemotePolicy = RemotePolicy.hybrid
    industry: str | None = None
    embedding: list[float] | None = None
    extraction_confidence: float | None = None
    status: RoleStatus = RoleStatus.draft
    created_at: datetime
    created_by: UUID
```

### Match Contract (`backend/contracts/match.py`)

```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from .shared import SkillMatch, ConfidenceLevel, MatchStatus

class Match(BaseModel):
    id: UUID
    candidate_id: UUID
    role_id: UUID
    overall_score: float
    structured_score: float
    semantic_score: float
    skill_overlap: list[SkillMatch] = []
    confidence: ConfidenceLevel
    explanation: str
    strengths: list[str] = []
    gaps: list[str] = []
    recommendation: str
    scoring_breakdown: dict = {}
    model_version: str = ""
    created_at: datetime
    status: MatchStatus = MatchStatus.generated
```

### Signal Contract (`backend/contracts/signal.py`)

```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from .shared import SignalType, UserRole

class SignalCreate(BaseModel):
    event_type: SignalType
    actor_id: UUID
    actor_role: UserRole
    entity_type: str
    entity_id: UUID
    metadata: dict = {}

class Signal(BaseModel):
    id: UUID
    event_type: SignalType
    actor_id: UUID
    actor_role: UserRole
    entity_type: str
    entity_id: UUID
    metadata: dict = {}
    created_at: datetime
```

### Handoff Contract (`backend/contracts/handoff.py`)

```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from .shared import HandoffStatus

class HandoffCreate(BaseModel):
    to_partner_id: UUID
    candidate_ids: list[UUID]
    context_notes: str
    target_role_id: UUID | None = None

class Handoff(BaseModel):
    id: UUID
    from_partner_id: UUID
    to_partner_id: UUID
    candidate_ids: list[UUID]
    context_notes: str
    target_role_id: UUID | None = None
    status: HandoffStatus = HandoffStatus.pending
    response_notes: str | None = None
    attribution_id: UUID
    created_at: datetime
    responded_at: datetime | None = None
```

### Quote Contract (`backend/contracts/quote.py`)

```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from .shared import QuoteStatus

class QuoteRequest(BaseModel):
    candidate_id: UUID
    role_id: UUID

class Quote(BaseModel):
    id: UUID
    client_id: UUID
    candidate_id: UUID
    role_id: UUID
    is_pool_candidate: bool
    base_fee: Decimal
    pool_discount: Decimal | None = None
    final_fee: Decimal
    fee_breakdown: dict = {}
    status: QuoteStatus = QuoteStatus.generated
    created_at: datetime
    expires_at: datetime
```

### Collection Contract (`backend/contracts/collection.py`)

```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from .shared import Visibility

class CollectionCreate(BaseModel):
    name: str
    description: str | None = None
    visibility: Visibility = Visibility.private
    shared_with: list[UUID] | None = None
    tags: list[str] = []

class Collection(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    owner_id: UUID
    visibility: Visibility = Visibility.private
    shared_with: list[UUID] | None = None
    candidate_ids: list[UUID] = []
    tags: list[str] = []
    candidate_count: int = 0
    avg_match_score: float | None = None
    available_now_count: int = 0
    created_at: datetime
    updated_at: datetime
```

### Tests (`backend/tests/test_contracts.py`)

```python
from uuid import uuid4
from datetime import datetime
from decimal import Decimal
from backend.contracts.candidate import Candidate, CandidateCreate, CandidateAnonymized
from backend.contracts.role import Role, RoleCreate
from backend.contracts.match import Match
from backend.contracts.signal import Signal, SignalCreate
from backend.contracts.handoff import Handoff, HandoffCreate
from backend.contracts.quote import Quote, QuoteRequest
from backend.contracts.collection import Collection, CollectionCreate
from backend.contracts.shared import *

def test_candidate_create():
    c = CandidateCreate(first_name="John", last_name="Doe")
    assert c.first_name == "John"

def test_candidate_full():
    c = Candidate(
        id=uuid4(), first_name="John", last_name="Doe",
        created_at=datetime.now(), updated_at=datetime.now(),
        created_by=uuid4()
    )
    assert c.skills == []
    assert c.extraction_flags == []

def test_candidate_anonymized():
    c = CandidateAnonymized(
        id=uuid4(), first_name="John", last_initial="D"
    )
    assert c.is_pool_candidate is False

def test_role_create():
    r = RoleCreate(title="Senior Backend", description="Python role", organisation_id=uuid4())
    assert r.remote_policy == RemotePolicy.hybrid

def test_match():
    m = Match(
        id=uuid4(), candidate_id=uuid4(), role_id=uuid4(),
        overall_score=0.85, structured_score=0.9, semantic_score=0.8,
        confidence=ConfidenceLevel.strong, explanation="Strong match",
        recommendation="Recommend", created_at=datetime.now()
    )
    assert m.status == MatchStatus.generated

def test_signal_create():
    s = SignalCreate(
        event_type=SignalType.candidate_viewed, actor_id=uuid4(),
        actor_role=UserRole.talent_partner, entity_type="candidate",
        entity_id=uuid4()
    )
    assert s.metadata == {}

def test_handoff_create():
    h = HandoffCreate(
        to_partner_id=uuid4(), candidate_ids=[uuid4()],
        context_notes="Great Python candidates"
    )
    assert h.target_role_id is None

def test_quote():
    q = Quote(
        id=uuid4(), client_id=uuid4(), candidate_id=uuid4(),
        role_id=uuid4(), is_pool_candidate=True,
        base_fee=Decimal("25000"), pool_discount=Decimal("5000"),
        final_fee=Decimal("20000"), created_at=datetime.now(),
        expires_at=datetime.now()
    )
    assert q.status == QuoteStatus.generated

def test_collection_create():
    c = CollectionCreate(name="Senior Backend — London")
    assert c.visibility == Visibility.private
```

## Outputs
- `backend/requirements.txt`
- `backend/config.py`
- `backend/contracts/` (all contract files)
- `backend/tests/test_contracts.py`
- `backend/__init__.py`, `backend/contracts/__init__.py`, `backend/tests/__init__.py`

## Acceptance Criteria
1. `cd backend && pip install -r requirements.txt` succeeds
2. `cd backend && python -m pytest tests/test_contracts.py -v` — all tests pass
3. All contract models can be serialized to JSON and back

## Handoff Notes
- **To Agent B:** All canonical types are in `backend/contracts/`. Mirror these exactly to `contracts/canonical.ts`. Key files: `shared.py` (enums + value objects), `candidate.py`, `role.py`, `match.py`, `signal.py`, `handoff.py`, `quote.py`, `collection.py`. Pay attention to `CandidateAnonymized` — this is the client-facing view.
- **To Task 02:** Contracts are ready. Schema should map these models to PostgreSQL tables.
- **Decision:** Using Pydantic v2 with `model_` prefix methods. All UUIDs as `uuid.UUID`, all datetimes as `datetime.datetime`.
