import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from copilot.executor import CopilotExecutor
from copilot.formatter import CopilotFormatter
from copilot.parser import PARSER_SYSTEM_PROMPT, CopilotParser


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
        parsed_query={
            "query_type": "candidate_search",
            "interpretation": "Searching for candidates with Python skills",
        },
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

    # Single result — table="candidates" → entity="candidate"
    result_1 = formatter.format_response(
        query="test",
        parsed_query={"query_type": "candidate_search", "table": "candidates", "suggested_followups": []},
        execution_result={"results": [{}], "total_count": 1, "query_executed": {}},
    )
    assert "1 candidate" in result_1["summary"]

    # Multiple results — table="candidates"
    result_n = formatter.format_response(
        query="test",
        parsed_query={"query_type": "candidate_search", "table": "candidates", "suggested_followups": []},
        execution_result={"results": [{}, {}, {}], "total_count": 3, "query_executed": {}},
    )
    assert "3 candidates" in result_n["summary"]


def test_formatter_role_search_has_generate_matches_action():
    formatter = CopilotFormatter()
    result = formatter.format_response(
        query="Show active roles",
        parsed_query={"query_type": "role_search", "suggested_followups": []},
        execution_result={
            "results": [{"id": "1", "title": "Senior Engineer"}],
            "total_count": 1,
            "query_executed": {},
        },
    )
    assert any(a["action"] == "generate_matches" for a in result["actions"])


def test_formatter_analytics_has_dashboard_action():
    formatter = CopilotFormatter()
    result = formatter.format_response(
        query="Show platform statistics",
        parsed_query={"query_type": "analytics", "suggested_followups": []},
        execution_result={
            "results": [{"event_type": "match_generated", "count": 42}],
            "total_count": 1,
            "query_executed": {},
        },
    )
    assert any(a["action"] == "view_dashboard" for a in result["actions"])
