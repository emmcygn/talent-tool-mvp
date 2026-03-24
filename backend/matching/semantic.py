from uuid import UUID


class SemanticSearch:
    """pgvector cosine similarity search for candidate-role matching."""

    def __init__(self, supabase):
        self.supabase = supabase

    async def find_similar_candidates(
        self,
        role_embedding: list[float],
        candidate_pool: list[UUID] | None = None,
        top_k: int = 50,
    ) -> list[dict]:
        """Find top_k candidates most similar to the role embedding.

        Uses pgvector's cosine distance operator via Supabase RPC.
        Returns list of {candidate_id, similarity_score} sorted by similarity desc.
        """
        params = {
            "query_embedding": role_embedding,
            "match_count": top_k,
        }

        if candidate_pool:
            params["candidate_ids"] = [str(cid) for cid in candidate_pool]

        result = self.supabase.rpc("match_candidates", params).execute()

        return [
            {
                "candidate_id": UUID(row["id"]),
                "similarity_score": 1.0 - row["distance"],
            }
            for row in (result.data or [])
        ]
