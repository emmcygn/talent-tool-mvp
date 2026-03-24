# Agent A — Task 14: Copilot Query Layer

## Mission
Build the natural language copilot that lets talent partners and admins query the platform using plain English. Translates natural language to structured queries via LLM, executes against Supabase, formats results with transparency (shows the query it ran), suggests actions, and supports multi-turn conversation context within a session.

## Context
This is Day 4. The copilot is the centrepiece feature of the Mothership — it transforms the platform from a traditional CRUD tool into an intelligent operating system. Partners type questions like "Who are my best Python candidates available in London?" and get structured, actionable results. The copilot shows what it did (transparency), suggests next steps, and remembers context within a session for follow-up refinements.

## Prerequisites
- Task 08 complete (candidate + role CRUD — data to query against)
- Task 09 complete (matching engine — can reference match results)
- Task 03 complete (FastAPI skeleton with auth, streaming support)
- Task 12 complete (signal tracking — copilot queries emit signals)

## Checklist
- [ ] Create `backend/copilot/__init__.py`
- [ ] Create `backend/copilot/parser.py` — NL → structured query via LLM
- [ ] Create `backend/copilot/executor.py` — query execution against Supabase
- [ ] Create `backend/copilot/formatter.py` — response formatting with actions and suggestions
- [ ] Create `backend/api/copilot.py` — SSE streaming endpoint with session context
- [ ] Register router in `backend/main.py`
- [ ] Create `backend/tests/test_copilot.py` — unit tests
- [ ] Run tests, verify pass
- [ ] Commit: "Agent A Task 14: Copilot query layer"

## Implementation Details

### Query Parser (`backend/copilot/parser.py`)

```python
import json
from openai import AsyncOpenAI
from backend.config import settings


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
```

### Query Executor (`backend/copilot/executor.py`)

```python
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
                # For JSON array contains — use textSearch or filter in Python
                # PostgREST containment: field->>key
                query = query.contains(field, value)

        # Apply text search for skill/name matching (fallback)
        if text_search and table == "candidates":
            # Search in first_name, last_name, or skills
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
```

### Response Formatter (`backend/copilot/formatter.py`)

```python
class CopilotFormatter:
    """Formats copilot query results into user-friendly responses."""

    def format_response(
        self,
        query: str,
        parsed_query: dict,
        execution_result: dict,
    ) -> dict:
        """
        Format the copilot response with:
        - Natural language summary
        - The query that was run (transparency)
        - Results
        - Suggested actions
        - Follow-up suggestions
        """
        results = execution_result.get("results", [])
        total = execution_result.get("total_count", 0)
        query_type = parsed_query.get("query_type", "general")
        table = parsed_query.get("table", "unknown")

        # Generate summary
        summary = self._generate_summary(query_type, table, total, results)

        # Generate suggested actions based on result type
        actions = self._generate_actions(query_type, results)

        return {
            "summary": summary,
            "interpretation": parsed_query.get("interpretation", ""),
            "query_executed": execution_result.get("query_executed", {}),
            "results": results,
            "total_count": total,
            "actions": actions,
            "followup_suggestions": parsed_query.get("suggested_followups", []),
        }

    def _generate_summary(
        self, query_type: str, table: str, total: int, results: list
    ) -> str:
        """Generate a natural language summary of the results."""
        if total == 0:
            return f"No results found. Try broadening your search criteria."

        entity = table.rstrip("s")  # candidates → candidate
        if total == 1:
            return f"Found 1 {entity}."
        elif total <= 5:
            return f"Found {total} {table}."
        else:
            return f"Found {total} {table}. Showing the top {min(len(results), total)}."

    def _generate_actions(self, query_type: str, results: list) -> list[dict]:
        """Generate contextual actions based on the query type and results."""
        actions = []

        if not results:
            return actions

        if query_type == "candidate_search":
            actions.extend([
                {
                    "label": "Add to collection",
                    "action": "add_to_collection",
                    "description": "Add these candidates to a new or existing collection",
                },
                {
                    "label": "Run matching",
                    "action": "run_matching",
                    "description": "Run these candidates against a specific role",
                },
                {
                    "label": "Create handoff",
                    "action": "create_handoff",
                    "description": "Refer these candidates to another partner",
                },
            ])

        elif query_type == "match_search":
            actions.extend([
                {
                    "label": "Shortlist top matches",
                    "action": "shortlist_matches",
                    "description": "Shortlist the strong matches from these results",
                },
                {
                    "label": "Export results",
                    "action": "export_results",
                    "description": "Export match results as a summary",
                },
            ])

        elif query_type == "role_search":
            actions.extend([
                {
                    "label": "Generate matches",
                    "action": "generate_matches",
                    "description": "Run the matching engine against these roles",
                },
            ])

        elif query_type == "analytics":
            actions.extend([
                {
                    "label": "View dashboard",
                    "action": "view_dashboard",
                    "description": "Open the full analytics dashboard for deeper analysis",
                },
            ])

        return actions
```

### Copilot Streaming Endpoint (`backend/api/copilot.py`)

```python
import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from uuid import UUID
from pydantic import BaseModel
from backend.api.auth import get_current_user
from backend.copilot.parser import CopilotParser
from backend.copilot.executor import CopilotExecutor
from backend.copilot.formatter import CopilotFormatter
from backend.signals.tracker import SignalTracker
from backend.contracts.shared import SignalType, UserRole
from supabase import Client

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

# In-memory session context (per-user, last N turns)
# In production this would be Redis or database-backed
_session_contexts: dict[str, list[dict]] = {}
MAX_SESSION_TURNS = 10


class CopilotQuery(BaseModel):
    query: str
    session_id: str | None = None  # for multi-turn context


@router.post("/query")
async def copilot_query(
    data: CopilotQuery,
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """
    Process a copilot natural language query.
    Returns the full response (non-streaming version for simple clients).
    """
    parser = CopilotParser()
    executor = CopilotExecutor(supabase)
    formatter = CopilotFormatter()

    # Get session context
    session_key = data.session_id or user["id"]
    context = _session_contexts.get(session_key, [])

    # Parse
    parsed = await parser.parse(data.query, session_context=context)

    # Execute
    result = await executor.execute(parsed)

    # Format
    response = formatter.format_response(data.query, parsed, result)

    # Store in session context
    context_entry = {
        "query": data.query,
        "interpretation": parsed.get("interpretation", ""),
        "result_count": result.get("total_count", 0),
        "query_type": parsed.get("query_type", ""),
        "filters": parsed.get("filters", []),
    }
    if session_key not in _session_contexts:
        _session_contexts[session_key] = []
    _session_contexts[session_key].append(context_entry)
    # Trim to max turns
    _session_contexts[session_key] = _session_contexts[session_key][-MAX_SESSION_TURNS:]

    # Emit signal
    tracker = SignalTracker(supabase)
    await tracker.emit(
        event_type=SignalType.copilot_query,
        actor_id=user["id"],
        actor_role=user["role"],
        entity_type="copilot",
        entity_id=user["id"],  # no specific entity
        metadata={
            "query": data.query,
            "interpretation": parsed.get("interpretation", ""),
            "result_count": result.get("total_count", 0),
            "query_type": parsed.get("query_type", ""),
        },
    )

    return response


@router.post("/query/stream")
async def copilot_query_stream(
    data: CopilotQuery,
    user=Depends(get_current_user),
    supabase: Client = Depends(),
):
    """
    Process a copilot query with Server-Sent Events (SSE) streaming.
    Sends progressive updates: parsing → executing → results → actions.
    """
    async def event_stream():
        parser = CopilotParser()
        executor = CopilotExecutor(supabase)
        formatter = CopilotFormatter()

        session_key = data.session_id or user["id"]
        context = _session_contexts.get(session_key, [])

        # Phase 1: Parsing
        yield f"data: {json.dumps({'phase': 'parsing', 'message': 'Understanding your question...'})}\n\n"

        parsed = await parser.parse(data.query, session_context=context)

        yield f"data: {json.dumps({'phase': 'parsed', 'interpretation': parsed.get('interpretation', ''), 'query_type': parsed.get('query_type', '')})}\n\n"

        # Phase 2: Executing
        yield f"data: {json.dumps({'phase': 'executing', 'message': 'Searching the platform...'})}\n\n"

        result = await executor.execute(parsed)

        yield f"data: {json.dumps({'phase': 'executed', 'total_count': result.get('total_count', 0)})}\n\n"

        # Phase 3: Formatting
        response = formatter.format_response(data.query, parsed, result)

        # Stream results in chunks (for large result sets)
        results = response.get("results", [])
        chunk_size = 5
        for i in range(0, len(results), chunk_size):
            chunk = results[i:i + chunk_size]
            yield f"data: {json.dumps({'phase': 'results', 'chunk_index': i // chunk_size, 'results': chunk})}\n\n"

        # Phase 4: Complete with actions and suggestions
        yield f"data: {json.dumps({'phase': 'complete', 'summary': response.get('summary', ''), 'actions': response.get('actions', []), 'followup_suggestions': response.get('followup_suggestions', []), 'query_executed': response.get('query_executed', {})})}\n\n"

        # Update session context
        context_entry = {
            "query": data.query,
            "interpretation": parsed.get("interpretation", ""),
            "result_count": result.get("total_count", 0),
            "query_type": parsed.get("query_type", ""),
            "filters": parsed.get("filters", []),
        }
        if session_key not in _session_contexts:
            _session_contexts[session_key] = []
        _session_contexts[session_key].append(context_entry)
        _session_contexts[session_key] = _session_contexts[session_key][-MAX_SESSION_TURNS:]

        # Emit signal
        tracker = SignalTracker(supabase)
        await tracker.emit(
            event_type=SignalType.copilot_query,
            actor_id=user["id"],
            actor_role=user["role"],
            entity_type="copilot",
            entity_id=user["id"],
            metadata={
                "query": data.query,
                "interpretation": parsed.get("interpretation", ""),
                "result_count": result.get("total_count", 0),
                "query_type": parsed.get("query_type", ""),
            },
        )

        yield f"data: {json.dumps({'phase': 'done'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    user=Depends(get_current_user),
):
    """Clear copilot session context (start fresh conversation)."""
    session_key = session_id or user["id"]
    if session_key in _session_contexts:
        del _session_contexts[session_key]
    return {"status": "cleared"}
```

### Tests (`backend/tests/test_copilot.py`)

```python
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from backend.copilot.parser import CopilotParser, PARSER_SYSTEM_PROMPT
from backend.copilot.executor import CopilotExecutor
from backend.copilot.formatter import CopilotFormatter


def test_parser_system_prompt_contains_table_schema():
    assert "candidates" in PARSER_SYSTEM_PROMPT
    assert "roles" in PARSER_SYSTEM_PROMPT
    assert "matches" in PARSER_SYSTEM_PROMPT
    assert "handoffs" in PARSER_SYSTEM_PROMPT
    assert "quotes" in PARSER_SYSTEM_PROMPT
    assert "signals" in PARSER_SYSTEM_PROMPT


def test_parser_system_prompt_contains_operators():
    for op in ["eq", "gt", "lt", "like", "in", "contains"]:
        assert op in PARSER_SYSTEM_PROMPT


def test_formatter_empty_results():
    formatter = CopilotFormatter()
    result = formatter.format_response(
        query="Find Python developers",
        parsed_query={"query_type": "candidate_search", "interpretation": "Searching for candidates with Python skills"},
        execution_result={"results": [], "total_count": 0, "query_executed": {}},
    )
    assert "No results" in result["summary"]
    assert result["total_count"] == 0
    assert result["actions"] == []


def test_formatter_candidate_results():
    formatter = CopilotFormatter()
    result = formatter.format_response(
        query="Find Python developers in London",
        parsed_query={
            "query_type": "candidate_search",
            "interpretation": "Searching for Python developers located in London",
            "suggested_followups": ["Filter by seniority", "Show only available now"],
        },
        execution_result={
            "results": [{"id": "1", "first_name": "Alice"}],
            "total_count": 1,
            "query_executed": {"table": "candidates"},
        },
    )
    assert result["total_count"] == 1
    assert len(result["actions"]) > 0
    assert any(a["action"] == "add_to_collection" for a in result["actions"])
    assert len(result["followup_suggestions"]) == 2


def test_formatter_match_results_have_shortlist_action():
    formatter = CopilotFormatter()
    result = formatter.format_response(
        query="Show matches for Senior Backend role",
        parsed_query={"query_type": "match_search", "suggested_followups": []},
        execution_result={
            "results": [{"id": "1", "overall_score": 0.85}],
            "total_count": 1,
            "query_executed": {},
        },
    )
    assert any(a["action"] == "shortlist_matches" for a in result["actions"])


def test_executor_select_fields():
    executor = CopilotExecutor(MagicMock())
    # Candidates should not include embedding or cv_text (large fields)
    fields = executor._get_select_fields("candidates")
    assert "embedding" not in fields
    assert "cv_text" not in fields
    assert "first_name" in fields
    assert "skills" in fields

    # Unknown table returns *
    assert executor._get_select_fields("unknown_table") == "*"


@pytest.mark.asyncio
async def test_parser_fallback_on_error():
    parser = CopilotParser()
    # Mock OpenAI to raise an error
    with patch.object(parser, "openai") as mock_openai:
        mock_openai.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        result = await parser.parse("Find Python developers")
        assert result["query_type"] == "general"
        assert result["text_search"] == "Find Python developers"
        assert "error" in result


def test_formatter_summary_pluralization():
    formatter = CopilotFormatter()

    # Single result
    result_1 = formatter.format_response(
        query="test", parsed_query={"query_type": "candidate_search", "suggested_followups": []},
        execution_result={"results": [{}], "total_count": 1, "query_executed": {}},
    )
    assert "1 candidate" in result_1["summary"]

    # Multiple results
    result_n = formatter.format_response(
        query="test", parsed_query={"query_type": "candidate_search", "suggested_followups": []},
        execution_result={"results": [{}, {}, {}], "total_count": 3, "query_executed": {}},
    )
    assert "3 candidates" in result_n["summary"]
```

## Outputs
- `backend/copilot/__init__.py`
- `backend/copilot/parser.py`
- `backend/copilot/executor.py`
- `backend/copilot/formatter.py`
- `backend/api/copilot.py`
- `backend/tests/test_copilot.py`

## Acceptance Criteria
1. `POST /api/copilot/query` accepts natural language and returns structured results
2. `POST /api/copilot/query/stream` returns SSE with phases: parsing → parsed → executing → executed → results → complete → done
3. Parser translates common recruitment queries correctly (skill search, location filter, availability filter, match exploration)
4. Multi-turn context works: "Show Python devs in London" followed by "only the ones available now" refines the query
5. Every response includes `interpretation` (transparency) and `query_executed` (what was actually run)
6. Suggested follow-up questions are contextually relevant
7. Actions are appropriate to the query type (candidate → shortlist/add to collection, match → shortlist)
8. Copilot queries emit `copilot_query` signals for analytics
9. Session context is capped at 10 turns
10. Fallback works when LLM parsing fails (falls back to text search)
11. All tests pass: `python -m pytest tests/test_copilot.py -v`

## Handoff Notes
- **To Task 16:** Seed data should include example copilot sessions in the signal history to show copilot usage analytics.
- **To Agent B:** The streaming endpoint sends SSE events with a `phase` field. Phases in order: `parsing`, `parsed`, `executing`, `executed`, `results` (may be multiple chunks), `complete`, `done`. The `complete` event contains `summary`, `actions`, `followup_suggestions`, and `query_executed`. Wire the copilot sidebar to consume these phases progressively. The non-streaming `/query` endpoint returns the same data in one response for simpler integration. Session ID should be a UUID generated client-side and sent with each query for multi-turn context. Actions have `label`, `action`, and `description` fields — render as clickable buttons.
- **Decision:** Session context is in-memory (dict keyed by session ID). For the PoC this is sufficient. Production would use Redis or Supabase. Temperature 0.1 for parser (we want deterministic query translation). Large fields (embedding, cv_text) are excluded from copilot query results to keep responses fast.
