from collections import Counter
from datetime import datetime, timedelta

from contracts.shared import SignalType


class AnalyticsService:
    """Aggregate analytics queries powered by the signal layer."""

    def __init__(self, supabase):
        self.supabase = supabase

    async def get_funnel_data(self, days: int = 30) -> dict:
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        stages = {
            "ingested": SignalType.candidate_ingested.value,
            "matched": SignalType.match_generated.value,
            "shortlisted": SignalType.candidate_shortlisted.value,
            "intro_requested": SignalType.intro_requested.value,
            "placed": SignalType.placement_made.value,
        }

        funnel = {}
        for stage_name, event_type in stages.items():
            result = (
                self.supabase.table("signals")
                .select("id", count="exact")
                .eq("event_type", event_type)
                .gte("created_at", since)
                .execute()
            )
            funnel[stage_name] = result.count or 0

        stage_order = ["ingested", "matched", "shortlisted", "intro_requested", "placed"]
        dropoff = {}
        for i in range(1, len(stage_order)):
            prev = funnel[stage_order[i - 1]]
            curr = funnel[stage_order[i]]
            rate = round(curr / prev * 100, 1) if prev > 0 else 0.0
            dropoff[f"{stage_order[i-1]}_to_{stage_order[i]}"] = rate

        return {"period_days": days, "stages": funnel, "conversion_rates": dropoff}

    async def get_trending_skills(self, days: int = 30, top_k: int = 20) -> list[dict]:
        result = (
            self.supabase.table("roles")
            .select("required_skills, preferred_skills")
            .eq("status", "active")
            .execute()
        )

        skill_counts = Counter()
        for role in result.data or []:
            for skill in role.get("required_skills") or []:
                if isinstance(skill, dict):
                    skill_counts[skill.get("name", "")] += 2
            for skill in role.get("preferred_skills") or []:
                if isinstance(skill, dict):
                    skill_counts[skill.get("name", "")] += 1

        return [
            {"skill": name, "demand_score": count}
            for name, count in skill_counts.most_common(top_k)
            if name
        ]

    async def get_partner_performance(self, days: int = 30) -> list[dict]:
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        result = (
            self.supabase.table("signals")
            .select("*")
            .eq("actor_role", "talent_partner")
            .gte("created_at", since)
            .execute()
        )

        partner_stats: dict[str, dict] = {}
        for s in result.data or []:
            pid = s["actor_id"]
            if pid not in partner_stats:
                partner_stats[pid] = {
                    "partner_id": pid,
                    "candidates_added": 0,
                    "handoffs_sent": 0,
                    "handoffs_accepted": 0,
                    "placements": 0,
                }
            event = s["event_type"]
            if event == SignalType.candidate_ingested.value:
                partner_stats[pid]["candidates_added"] += 1
            elif event == SignalType.handoff_sent.value:
                partner_stats[pid]["handoffs_sent"] += 1
            elif event == SignalType.handoff_accepted.value:
                partner_stats[pid]["handoffs_accepted"] += 1
            elif event == SignalType.placement_made.value:
                partner_stats[pid]["placements"] += 1

        return list(partner_stats.values())

    async def get_client_engagement(self, days: int = 30) -> list[dict]:
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        result = (
            self.supabase.table("signals")
            .select("*")
            .eq("actor_role", "client")
            .gte("created_at", since)
            .execute()
        )

        client_stats: dict[str, dict] = {}
        for s in result.data or []:
            cid = s["actor_id"]
            if cid not in client_stats:
                client_stats[cid] = {
                    "client_id": cid,
                    "candidates_viewed": 0,
                    "candidates_shortlisted": 0,
                    "candidates_dismissed": 0,
                    "intros_requested": 0,
                }
            event = s["event_type"]
            if event == SignalType.candidate_viewed.value:
                client_stats[cid]["candidates_viewed"] += 1
            elif event == SignalType.candidate_shortlisted.value:
                client_stats[cid]["candidates_shortlisted"] += 1
            elif event == SignalType.candidate_dismissed.value:
                client_stats[cid]["candidates_dismissed"] += 1
            elif event == SignalType.intro_requested.value:
                client_stats[cid]["intros_requested"] += 1

        for stats in client_stats.values():
            total = stats["candidates_shortlisted"] + stats["candidates_dismissed"]
            stats["shortlist_rate"] = (
                round(stats["candidates_shortlisted"] / total * 100, 1)
                if total > 0
                else 0.0
            )

        return list(client_stats.values())

    async def get_time_series(
        self, event_type: str | None = None, days: int = 30, granularity: str = "day"
    ) -> list[dict]:
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        query = (
            self.supabase.table("signals")
            .select("created_at, event_type")
            .gte("created_at", since)
            .order("created_at", desc=False)
        )
        if event_type:
            query = query.eq("event_type", event_type)

        result = query.execute()

        buckets: dict[str, int] = {}
        for s in result.data or []:
            dt = datetime.fromisoformat(s["created_at"].replace("Z", "+00:00"))
            if granularity == "week":
                week_start = dt - timedelta(days=dt.weekday())
                key = week_start.strftime("%Y-%m-%d")
            else:
                key = dt.strftime("%Y-%m-%d")
            buckets[key] = buckets.get(key, 0) + 1

        start_date = datetime.utcnow() - timedelta(days=days)
        series = []
        current = start_date
        while current <= datetime.utcnow():
            key = current.strftime("%Y-%m-%d")
            series.append({"date": key, "count": buckets.get(key, 0)})
            current += timedelta(days=7 if granularity == "week" else 1)

        return series
