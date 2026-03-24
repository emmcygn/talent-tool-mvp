from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from contracts.candidate import Candidate, CandidateAnonymized, CandidateCreate
from contracts.collection import Collection, CollectionCreate
from contracts.handoff import Handoff, HandoffCreate
from contracts.match import Match
from contracts.quote import Quote, QuoteRequest
from contracts.role import Role, RoleCreate
from contracts.shared import (
    ConfidenceLevel,
    HandoffStatus,
    MatchStatus,
    QuoteStatus,
    RemotePolicy,
    SignalType,
    UserRole,
    Visibility,
)
from contracts.signal import Signal, SignalCreate


def test_candidate_create():
    c = CandidateCreate(first_name="John", last_name="Doe")
    assert c.first_name == "John"


def test_candidate_full():
    c = Candidate(
        id=uuid4(),
        first_name="John",
        last_name="Doe",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        created_by=uuid4(),
    )
    assert c.skills == []
    assert c.extraction_flags == []


def test_candidate_anonymized():
    c = CandidateAnonymized(id=uuid4(), first_name="John", last_initial="D")
    assert c.is_pool_candidate is False


def test_role_create():
    r = RoleCreate(
        title="Senior Backend", description="Python role", organisation_id=uuid4()
    )
    assert r.remote_policy == RemotePolicy.hybrid


def test_role_full():
    r = Role(
        id=uuid4(),
        title="Senior Backend",
        description="Python role",
        organisation_id=uuid4(),
        created_at=datetime.now(),
        created_by=uuid4(),
    )
    assert r.status.value == "draft"


def test_match():
    m = Match(
        id=uuid4(),
        candidate_id=uuid4(),
        role_id=uuid4(),
        overall_score=0.85,
        structured_score=0.9,
        semantic_score=0.8,
        confidence=ConfidenceLevel.strong,
        explanation="Strong match",
        recommendation="Recommend",
        created_at=datetime.now(),
    )
    assert m.status == MatchStatus.generated


def test_signal_create():
    s = SignalCreate(
        event_type=SignalType.candidate_viewed,
        actor_id=uuid4(),
        actor_role=UserRole.talent_partner,
        entity_type="candidate",
        entity_id=uuid4(),
    )
    assert s.metadata == {}


def test_signal_full():
    s = Signal(
        id=uuid4(),
        event_type=SignalType.candidate_viewed,
        actor_id=uuid4(),
        actor_role=UserRole.talent_partner,
        entity_type="candidate",
        entity_id=uuid4(),
        created_at=datetime.now(),
    )
    assert s.event_type == SignalType.candidate_viewed


def test_handoff_create():
    h = HandoffCreate(
        to_partner_id=uuid4(),
        candidate_ids=[uuid4()],
        context_notes="Great Python candidates",
    )
    assert h.target_role_id is None


def test_handoff_full():
    h = Handoff(
        id=uuid4(),
        from_partner_id=uuid4(),
        to_partner_id=uuid4(),
        candidate_ids=[uuid4()],
        context_notes="Great Python candidates",
        attribution_id=uuid4(),
        created_at=datetime.now(),
    )
    assert h.status == HandoffStatus.pending


def test_quote_request():
    q = QuoteRequest(candidate_id=uuid4(), role_id=uuid4())
    assert q.candidate_id is not None


def test_quote():
    q = Quote(
        id=uuid4(),
        client_id=uuid4(),
        candidate_id=uuid4(),
        role_id=uuid4(),
        is_pool_candidate=True,
        base_fee=Decimal("25000"),
        pool_discount=Decimal("5000"),
        final_fee=Decimal("20000"),
        created_at=datetime.now(),
        expires_at=datetime.now(),
    )
    assert q.status == QuoteStatus.generated


def test_collection_create():
    c = CollectionCreate(name="Senior Backend — London")
    assert c.visibility == Visibility.private


def test_collection_full():
    c = Collection(
        id=uuid4(),
        name="Senior Backend — London",
        owner_id=uuid4(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert c.candidate_count == 0


def test_models_serialize_to_json():
    """Verify all models can round-trip through JSON."""
    now = datetime.now()
    uid = uuid4()

    models = [
        CandidateCreate(first_name="A", last_name="B"),
        Candidate(
            id=uid, first_name="A", last_name="B",
            created_at=now, updated_at=now, created_by=uid,
        ),
        CandidateAnonymized(id=uid, first_name="A", last_initial="B"),
        RoleCreate(title="T", description="D", organisation_id=uid),
        Role(
            id=uid, title="T", description="D", organisation_id=uid,
            created_at=now, created_by=uid,
        ),
        Match(
            id=uid, candidate_id=uid, role_id=uid,
            overall_score=0.8, structured_score=0.7, semantic_score=0.9,
            confidence=ConfidenceLevel.good, explanation="x",
            recommendation="y", created_at=now,
        ),
        SignalCreate(
            event_type=SignalType.candidate_viewed, actor_id=uid,
            actor_role=UserRole.client, entity_type="candidate", entity_id=uid,
        ),
        Signal(
            id=uid, event_type=SignalType.candidate_viewed, actor_id=uid,
            actor_role=UserRole.client, entity_type="candidate", entity_id=uid,
            created_at=now,
        ),
        HandoffCreate(
            to_partner_id=uid, candidate_ids=[uid], context_notes="notes",
        ),
        Handoff(
            id=uid, from_partner_id=uid, to_partner_id=uid,
            candidate_ids=[uid], context_notes="notes",
            attribution_id=uid, created_at=now,
        ),
        QuoteRequest(candidate_id=uid, role_id=uid),
        Quote(
            id=uid, client_id=uid, candidate_id=uid, role_id=uid,
            is_pool_candidate=False, base_fee=Decimal("10000"),
            final_fee=Decimal("10000"), created_at=now, expires_at=now,
        ),
        CollectionCreate(name="Test"),
        Collection(
            id=uid, name="Test", owner_id=uid,
            created_at=now, updated_at=now,
        ),
    ]

    for model in models:
        json_str = model.model_dump_json()
        assert json_str  # non-empty
        # Round-trip: JSON → dict → model
        restored = type(model).model_validate_json(json_str)
        assert restored == model
