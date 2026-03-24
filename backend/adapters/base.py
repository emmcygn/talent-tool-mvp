from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AdapterStatus(BaseModel):
    """Health status returned by adapters."""

    adapter_name: str
    connected: bool
    last_sync: datetime | None = None
    records_available: int = 0
    error: str | None = None


class AdapterCandidate(BaseModel):
    """Raw candidate record as returned by an adapter.

    Each adapter returns its own field set. Not all fields are present
    in every adapter — that's the point. Normalization handles mapping.
    """

    external_id: str
    raw_data: dict[str, Any]
    adapter_name: str
    fetched_at: datetime


class AdapterRole(BaseModel):
    """Raw role record as returned by an adapter."""

    external_id: str
    raw_data: dict[str, Any]
    adapter_name: str
    fetched_at: datetime


class BaseAdapter(ABC):
    """Abstract base class for all recruitment data adapters.

    Each adapter connects to an external system (Bullhorn, HubSpot,
    LinkedIn) and returns raw records in that system's native format.
    The normalization pipeline (Task 05) maps these to canonical format.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique adapter identifier, e.g. 'bullhorn', 'hubspot', 'linkedin'."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable adapter name for UI display."""
        ...

    @property
    @abstractmethod
    def adapter_type(self) -> str:
        """Type category: 'ats', 'crm', 'social'."""
        ...

    @abstractmethod
    async def fetch_candidates(
        self,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[AdapterCandidate]:
        """Fetch candidate records from the external system."""
        ...

    @abstractmethod
    async def fetch_roles(
        self,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[AdapterRole]:
        """Fetch role/job records from the external system.

        Not all adapters have roles. Return empty list if not applicable.
        """
        ...

    @abstractmethod
    async def get_status(self) -> AdapterStatus:
        """Return current adapter health status."""
        ...
