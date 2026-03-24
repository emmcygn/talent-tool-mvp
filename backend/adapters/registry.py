import logging

from .base import AdapterStatus, BaseAdapter

logger = logging.getLogger("recruittech.adapters")


class AdapterRegistry:
    """Registry for managing adapter instances.

    Provides discovery, lookup, and health checking for all
    registered adapters.
    """

    def __init__(self):
        self._adapters: dict[str, BaseAdapter] = {}

    def register(self, adapter: BaseAdapter) -> None:
        """Register an adapter instance."""
        if adapter.name in self._adapters:
            logger.warning(f"Adapter '{adapter.name}' already registered, replacing")
        self._adapters[adapter.name] = adapter
        logger.info(f"Registered adapter: {adapter.name} ({adapter.display_name})")

    def get(self, name: str) -> BaseAdapter:
        """Get adapter by name. Raises KeyError if not found."""
        if name not in self._adapters:
            raise KeyError(
                f"Adapter '{name}' not registered. Available: {list(self._adapters.keys())}"
            )
        return self._adapters[name]

    def list_all(self) -> list[BaseAdapter]:
        """Return all registered adapters."""
        return list(self._adapters.values())

    def list_names(self) -> list[str]:
        """Return names of all registered adapters."""
        return list(self._adapters.keys())

    async def get_all_statuses(self) -> list[AdapterStatus]:
        """Get health status of all registered adapters."""
        statuses = []
        for adapter in self._adapters.values():
            try:
                status = await adapter.get_status()
                statuses.append(status)
            except Exception as e:
                statuses.append(
                    AdapterStatus(
                        adapter_name=adapter.name,
                        connected=False,
                        error=str(e),
                    )
                )
        return statuses


# Global registry instance — initialized at app startup
adapter_registry = AdapterRegistry()


def init_adapters() -> AdapterRegistry:
    """Initialize and register all mock adapters.

    Called during FastAPI lifespan startup.
    """
    from .bullhorn import BullhornAdapter
    from .hubspot import HubSpotAdapter
    from .linkedin import LinkedInAdapter

    adapter_registry.register(BullhornAdapter())
    adapter_registry.register(HubSpotAdapter())
    adapter_registry.register(LinkedInAdapter())

    logger.info(f"Initialized {len(adapter_registry.list_names())} adapters")
    return adapter_registry
