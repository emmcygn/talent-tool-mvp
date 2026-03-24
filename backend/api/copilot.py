import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.auth import CurrentUser, get_current_user
from api.deps import get_supabase_admin
from contracts.shared import SignalType
from copilot.executor import CopilotExecutor
from copilot.formatter import CopilotFormatter
from copilot.parser import CopilotParser
from signals.tracker import SignalTracker

router = APIRouter()

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
    user: CurrentUser = Depends(get_current_user),
):
    """
    Process a copilot natural language query.
    Returns the full response (non-streaming version for simple clients).
    """
    supabase = get_supabase_admin()
    parser = CopilotParser()
    executor = CopilotExecutor(supabase)
    formatter = CopilotFormatter()

    # Get session context
    session_key = data.session_id or str(user.id)
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
        actor_id=user.id,
        actor_role=user.role,
        entity_type="copilot",
        entity_id=user.id,
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
    user: CurrentUser = Depends(get_current_user),
):
    """
    Process a copilot query with Server-Sent Events (SSE) streaming.
    Sends progressive updates: parsing → parsed → executing → executed → results → complete → done.
    """
    supabase = get_supabase_admin()

    async def event_stream():
        parser = CopilotParser()
        executor = CopilotExecutor(supabase)
        formatter = CopilotFormatter()

        session_key = data.session_id or str(user.id)
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
        for i in range(0, max(len(results), 1), chunk_size):
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
            actor_id=user.id,
            actor_role=user.role,
            entity_type="copilot",
            entity_id=user.id,
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
    user: CurrentUser = Depends(get_current_user),
):
    """Clear copilot session context (start fresh conversation)."""
    session_key = session_id or str(user.id)
    if session_key in _session_contexts:
        del _session_contexts[session_key]
    return {"status": "cleared"}
