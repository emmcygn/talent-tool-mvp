import logging

from supabase import create_client, Client

from config import settings

logger = logging.getLogger("recruittech.deps")

# Supabase client singletons
_supabase_client: Client | None = None
_supabase_admin_client: Client | None = None


def get_supabase() -> Client:
    """Get Supabase client with anon key (respects RLS)."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_key,
        )
    return _supabase_client


def get_supabase_admin() -> Client:
    """Get Supabase client with service key (bypasses RLS).

    Use for system operations: ingestion, matching, signal tracking.
    """
    global _supabase_admin_client
    if _supabase_admin_client is None:
        _supabase_admin_client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )
    return _supabase_admin_client
