from supabase import Client


class CopilotExecutor:
    """Executes structured queries against Supabase."""

    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def execute(self, structured_query: dict) -> dict:
        """
        Execute a structured query and return results with metadata.

        Returns:
            {
                "results": [...],
                "total_count": int,
                "query_executed": dict  # the structured query for transparency
            }
        """
        table = structured_query.get("table", "candidates")
        filters = structured_query.get("filters", [])
        text_search = structured_query.get("text_search")
        order_by = structured_query.get("order_by")
        limit = structured_query.get("limit", 20)

        # Select appropriate fields based on table
        select_fields = self._get_select_fields(table)
        query = self.supabase.table(table).select(select_fields, count="exact")

        # Apply filters
        for f in filters:
            field = f.get("field", "")
            operator = f.get("operator", "eq")
            value = f.get("value")

            if operator == "eq":
                query = query.eq(field, value)
            elif operator == "neq":
                query = query.neq(field, value)
            elif operator == "gt":
                query = query.gt(field, value)
            elif operator == "lt":
                query = query.lt(field, value)
            elif operator == "gte":
                query = query.gte(field, value)
            elif operator == "lte":
                query = query.lte(field, value)
            elif operator == "like":
                query = query.like(field, f"%{value}%")
            elif operator == "ilike":
                query = query.ilike(field, f"%{value}%")
            elif operator == "in":
                if isinstance(value, list):
                    query = query.in_(field, value)
            elif operator == "contains":
                # For JSON array contains — use PostgREST containment
                query = query.contains(field, value)

        # Apply text search for skill/name matching (fallback)
        if text_search and table == "candidates":
            # Search in first_name, last_name, or location
            query = query.or_(
                f"first_name.ilike.%{text_search}%,"
                f"last_name.ilike.%{text_search}%,"
                f"location.ilike.%{text_search}%"
            )

        # Apply ordering
        if order_by:
            desc = order_by.get("direction", "desc") == "desc"
            query = query.order(order_by["field"], desc=desc)
        else:
            query = query.order("created_at", desc=True)

        # Apply limit
        query = query.limit(limit)

        try:
            result = query.execute()
            return {
                "results": result.data or [],
                "total_count": result.count or len(result.data or []),
                "query_executed": {
                    "table": table,
                    "filters": filters,
                    "text_search": text_search,
                    "order_by": order_by,
                    "limit": limit,
                },
            }
        except Exception as e:
            return {
                "results": [],
                "total_count": 0,
                "query_executed": structured_query,
                "error": str(e),
            }

    def _get_select_fields(self, table: str) -> str:
        """Return appropriate SELECT fields per table, excluding large blobs."""
        field_map = {
            "candidates": "id, first_name, last_name, location, skills, seniority, availability, industries, extraction_confidence, created_at",
            "roles": "id, title, description, organisation_id, required_skills, seniority, location, remote_policy, industry, status, created_at",
            "matches": "id, candidate_id, role_id, overall_score, confidence, explanation, strengths, gaps, recommendation, status, created_at",
            "collections": "id, name, description, owner_id, visibility, candidate_count, avg_match_score, available_now_count, tags, created_at",
            "handoffs": "id, from_partner_id, to_partner_id, status, candidate_ids, context_notes, created_at, responded_at",
            "quotes": "id, client_id, candidate_id, role_id, base_fee, final_fee, is_pool_candidate, status, fee_breakdown, created_at, expires_at",
            "signals": "id, event_type, actor_id, entity_type, entity_id, metadata, created_at",
        }
        return field_map.get(table, "*")
