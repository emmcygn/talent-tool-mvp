import json

from openai import AsyncOpenAI

from config import settings


PARSER_SYSTEM_PROMPT = """You are a query parser for a UK recruitment platform. You translate natural language questions into structured database queries.

The platform has these tables and fields:
- candidates: id, first_name, last_name, email, location, skills (json array of {name, years, confidence}), experience (json array of {company, title, duration_months, industry}), seniority (junior/mid/senior/lead/principal), salary_expectation (json {min_amount, max_amount, currency}), availability (immediate/1_month/3_months/not_looking), industries (text array), extraction_confidence, created_at, created_by
- roles: id, title, description, organisation_id, required_skills, preferred_skills, seniority, salary_band, location, remote_policy, industry, status (draft/active/paused/filled/closed), created_at, created_by
- matches: id, candidate_id, role_id, overall_score, structured_score, semantic_score, confidence (strong/good/possible), explanation, status (generated/shortlisted/dismissed/intro_requested), created_at
- collections: id, name, owner_id, visibility, candidate_count, avg_match_score, tags, created_at
- handoffs: id, from_partner_id, to_partner_id, status (pending/accepted/declined/expired), candidate_ids, context_notes, created_at
- quotes: id, client_id, candidate_id, role_id, base_fee, final_fee, is_pool_candidate, status (generated/sent/accepted/declined/expired), created_at
- signals: id, event_type, actor_id, entity_type, entity_id, metadata, created_at

Given a natural language query, return a structured query as JSON with:
{
    "query_type": "candidate_search" | "role_search" | "match_search" | "analytics" | "collection_search" | "handoff_search" | "quote_search" | "general",
    "table": "the primary table to query",
    "filters": [{"field": "...", "operator": "eq|neq|gt|lt|gte|lte|like|in|contains", "value": "..."}],
    "text_search": "optional full-text search term for skill/name matching",
    "order_by": {"field": "...", "direction": "asc|desc"},
    "limit": 20,
    "interpretation": "One sentence explaining how you interpreted the query",
    "suggested_followups": ["suggested follow-up question 1", "suggested follow-up question 2"]
}

Rules:
- Always include an interpretation explaining your understanding
- For skill searches, use the "contains" operator on the skills JSON field
- Location matching should be case-insensitive and partial (e.g., "London" matches "East London")
- "available" or "available now" means availability IN (immediate, 1_month)
- "senior" candidates means seniority = "senior" (not lead or principal unless specified)
- Default limit is 20 unless the user specifies otherwise
- "best" or "top" implies ordering by match score or extraction confidence
- Suggest 2-3 follow-up questions that would refine or extend the current query
- If the query is ambiguous, make a reasonable assumption and note it in the interpretation

Handle context from previous queries. If the user says "now filter those by..." or "only the ones with...", apply the refinement to the previous query structure."""

PARSER_CONTEXT_TEMPLATE = """Previous queries in this session:
{context}

Current query: {query}

If the current query references previous results (e.g., "those", "them", "filter by", "only the ones"), refine the previous query. Otherwise, treat as a new query."""


class CopilotParser:
    """Translates natural language to structured queries using an LLM."""

    def __init__(self):
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def parse(
        self,
        query: str,
        session_context: list[dict] | None = None,
    ) -> dict:
        """
        Parse a natural language query into a structured query.

        Args:
            query: The user's natural language question
            session_context: Previous queries/results in this session for multi-turn

        Returns:
            Structured query dict with table, filters, ordering, interpretation
        """
        messages = [{"role": "system", "content": PARSER_SYSTEM_PROMPT}]

        if session_context:
            context_str = "\n".join(
                f"Q: {c['query']}\nInterpreted as: {c.get('interpretation', 'N/A')}\nResults: {c.get('result_count', 'N/A')} results"
                for c in session_context[-5:]  # last 5 turns
            )
            user_msg = PARSER_CONTEXT_TEMPLATE.format(
                context=context_str, query=query
            )
        else:
            user_msg = query

        messages.append({"role": "user", "content": user_msg})

        try:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=500,
            )

            content = response.choices[0].message.content
            parsed = json.loads(content)

            # Ensure required fields exist
            return {
                "query_type": parsed.get("query_type", "general"),
                "table": parsed.get("table", "candidates"),
                "filters": parsed.get("filters", []),
                "text_search": parsed.get("text_search"),
                "order_by": parsed.get("order_by"),
                "limit": min(parsed.get("limit", 20), 100),
                "interpretation": parsed.get("interpretation", ""),
                "suggested_followups": parsed.get("suggested_followups", []),
            }

        except Exception as e:
            return {
                "query_type": "general",
                "table": "candidates",
                "filters": [],
                "text_search": query,
                "order_by": None,
                "limit": 20,
                "interpretation": f"Falling back to text search: {query}",
                "suggested_followups": [],
                "error": str(e),
            }
