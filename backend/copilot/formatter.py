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
            return "No results found. Try broadening your search criteria."

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
