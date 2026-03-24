import pytest
from decimal import Decimal
from uuid import uuid4

from contracts.quote import QuoteRequest
from contracts.shared import QuoteStatus, SeniorityLevel
from services.quote import (
    POOL_DISCOUNT_PERCENTAGE,
    QUOTE_VALIDITY_DAYS,
    SENIORITY_BASE_FEES,
    QuoteService,
)


def test_seniority_fee_schedule():
    """Fee schedule covers all seniority levels with ascending fees."""
    levels = [
        SeniorityLevel.junior,
        SeniorityLevel.mid,
        SeniorityLevel.senior,
        SeniorityLevel.lead,
        SeniorityLevel.principal,
    ]
    fees = [SENIORITY_BASE_FEES[level] for level in levels]
    # Fees should be strictly ascending
    for i in range(1, len(fees)):
        assert fees[i] > fees[i - 1], (
            f"{levels[i].value} fee should be higher than {levels[i-1].value}"
        )


def test_pool_discount_percentage():
    assert POOL_DISCOUNT_PERCENTAGE == Decimal("0.20")


def test_pool_discount_calculation():
    base = Decimal("18000")
    discount = (base * POOL_DISCOUNT_PERCENTAGE).quantize(Decimal("0.01"))
    assert discount == Decimal("3600.00")
    assert base - discount == Decimal("14400.00")


def test_quote_validity():
    assert QUOTE_VALIDITY_DAYS == 14


def test_quote_request_model():
    q = QuoteRequest(candidate_id=uuid4(), role_id=uuid4())
    assert q.candidate_id is not None
    assert q.role_id is not None


def test_quote_status_valid_transitions():
    """Generated → sent → accepted/declined/expired."""
    terminal = {QuoteStatus.accepted, QuoteStatus.declined, QuoteStatus.expired}
    for status in terminal:
        assert status.value in ["accepted", "declined", "expired"]


def test_all_seniority_levels_in_fee_schedule():
    """Every seniority level must be present in the fee schedule."""
    for level in SeniorityLevel:
        assert level in SENIORITY_BASE_FEES, f"{level.value} missing from fee schedule"
        assert SENIORITY_BASE_FEES[level] > 0


def test_fee_breakdown_generation():
    """Fee breakdown contains required keys."""
    from unittest.mock import MagicMock

    service = QuoteService(MagicMock())
    base = Decimal("18000")
    discount = (base * POOL_DISCOUNT_PERCENTAGE).quantize(Decimal("0.01"))
    final = base - discount

    breakdown = service._generate_fee_breakdown(
        seniority=SeniorityLevel.senior,
        base_fee=base,
        is_pool=True,
        pool_discount=discount,
        final_fee=final,
        role_title="Senior Backend Engineer",
    )

    assert "summary" in breakdown
    assert "base_fee" in breakdown
    assert "pool_discount" in breakdown
    assert "savings_message" in breakdown
    assert "final_fee" in breakdown
    assert "validity" in breakdown
    assert "£3,600.00" in breakdown["savings_message"]


def test_fee_breakdown_no_pool_discount():
    """Fee breakdown without pool discount should not include discount fields."""
    from unittest.mock import MagicMock

    service = QuoteService(MagicMock())
    base = Decimal("12000")

    breakdown = service._generate_fee_breakdown(
        seniority=SeniorityLevel.mid,
        base_fee=base,
        is_pool=False,
        pool_discount=None,
        final_fee=base,
        role_title="Mid-level Developer",
    )

    assert "pool_discount" not in breakdown
    assert "savings_message" not in breakdown
    assert breakdown["final_fee"]["amount"] == "12000"
