import pytest

from adapters.base import AdapterCandidate, AdapterStatus
from adapters.bullhorn import BullhornAdapter
from adapters.hubspot import HubSpotAdapter
from adapters.linkedin import LinkedInAdapter
from adapters.registry import AdapterRegistry, init_adapters


@pytest.mark.asyncio
async def test_bullhorn_fetch_candidates():
    adapter = BullhornAdapter()
    candidates = await adapter.fetch_candidates()
    assert len(candidates) == 18
    assert all(isinstance(c, AdapterCandidate) for c in candidates)
    assert all(c.adapter_name == "bullhorn" for c in candidates)
    # Verify ATS-specific fields exist
    assert "employmentHistory" in candidates[0].raw_data
    assert "skillList" in candidates[0].raw_data


@pytest.mark.asyncio
async def test_hubspot_fetch_candidates():
    adapter = HubSpotAdapter()
    candidates = await adapter.fetch_candidates()
    assert len(candidates) == 16
    assert all(c.adapter_name == "hubspot" for c in candidates)
    # Verify CRM-specific fields exist
    assert "properties" in candidates[0].raw_data
    assert "engagement_score" in candidates[0].raw_data["properties"]


@pytest.mark.asyncio
async def test_linkedin_fetch_candidates():
    adapter = LinkedInAdapter()
    candidates = await adapter.fetch_candidates()
    assert len(candidates) == 15
    assert all(c.adapter_name == "linkedin" for c in candidates)
    # Verify profile-specific fields exist
    assert "skills" in candidates[0].raw_data
    assert "endorsements" in candidates[0].raw_data["skills"][0]


@pytest.mark.asyncio
async def test_bullhorn_has_roles():
    adapter = BullhornAdapter()
    roles = await adapter.fetch_roles()
    assert len(roles) > 0


@pytest.mark.asyncio
async def test_hubspot_no_roles():
    adapter = HubSpotAdapter()
    roles = await adapter.fetch_roles()
    assert roles == []


@pytest.mark.asyncio
async def test_linkedin_no_roles():
    adapter = LinkedInAdapter()
    roles = await adapter.fetch_roles()
    assert roles == []


@pytest.mark.asyncio
async def test_adapter_status():
    for AdapterClass in [BullhornAdapter, HubSpotAdapter, LinkedInAdapter]:
        adapter = AdapterClass()
        status = await adapter.get_status()
        assert isinstance(status, AdapterStatus)
        assert status.connected is True
        assert status.records_available > 0


def test_registry():
    registry = AdapterRegistry()
    registry.register(BullhornAdapter())
    registry.register(HubSpotAdapter())
    registry.register(LinkedInAdapter())
    assert len(registry.list_names()) == 3
    assert registry.get("bullhorn").name == "bullhorn"
    with pytest.raises(KeyError):
        registry.get("nonexistent")


def test_init_adapters():
    registry = init_adapters()
    assert "bullhorn" in registry.list_names()
    assert "hubspot" in registry.list_names()
    assert "linkedin" in registry.list_names()
