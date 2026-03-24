from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from api.auth import CurrentUser, get_current_user, require_role
from api.deps import get_supabase_admin
from contracts.shared import UserRole
from signals.analytics import AnalyticsService
from signals.tracker import SignalTracker

router = APIRouter()


@router.get("/recent")
async def get_recent_signals(
    limit: int = Query(default=50, le=200),
    event_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    since: Optional[datetime] = None,
    user: CurrentUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()
    tracker = SignalTracker(supabase)
    actor_id = None if user.role == UserRole.admin else user.id
    return await tracker.get_recent(
        limit=limit,
        event_type=event_type,
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=entity_id,
        since=since,
    )


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_signals(
    entity_type: str,
    entity_id: UUID,
    limit: int = Query(default=100, le=500),
    user: CurrentUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()
    tracker = SignalTracker(supabase)
    return await tracker.get_signals_for_entity(entity_type, entity_id, limit)


@router.get("/analytics/funnel")
async def get_funnel(
    days: int = Query(default=30, le=365),
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    supabase = get_supabase_admin()
    return await AnalyticsService(supabase).get_funnel_data(days=days)


@router.get("/analytics/trending-skills")
async def get_trending_skills(
    days: int = Query(default=30, le=365),
    top_k: int = Query(default=20, le=50),
    user: CurrentUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()
    return await AnalyticsService(supabase).get_trending_skills(days=days, top_k=top_k)


@router.get("/analytics/partner-performance")
async def get_partner_performance(
    days: int = Query(default=30, le=365),
    user: CurrentUser = Depends(require_role(UserRole.admin)),
):
    supabase = get_supabase_admin()
    return await AnalyticsService(supabase).get_partner_performance(days=days)


@router.get("/analytics/client-engagement")
async def get_client_engagement(
    days: int = Query(default=30, le=365),
    user: CurrentUser = Depends(require_role(UserRole.admin)),
):
    supabase = get_supabase_admin()
    return await AnalyticsService(supabase).get_client_engagement(days=days)


@router.get("/analytics/time-series")
async def get_time_series(
    event_type: Optional[str] = None,
    days: int = Query(default=30, le=365),
    granularity: str = Query(default="day", pattern="^(day|week)$"),
    user: CurrentUser = Depends(
        require_role(UserRole.talent_partner, UserRole.admin)
    ),
):
    supabase = get_supabase_admin()
    return await AnalyticsService(supabase).get_time_series(
        event_type=event_type, days=days, granularity=granularity
    )
