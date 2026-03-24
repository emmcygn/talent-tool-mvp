-- pgvector cosine similarity search function
CREATE OR REPLACE FUNCTION match_candidates(
    query_embedding vector(1536),
    match_count int DEFAULT 50,
    candidate_ids uuid[] DEFAULT NULL
)
RETURNS TABLE(id uuid, distance float)
LANGUAGE plpgsql
AS $$
BEGIN
    IF candidate_ids IS NOT NULL THEN
        RETURN QUERY
        SELECT c.id, (c.embedding <=> query_embedding)::float AS distance
        FROM candidates c
        WHERE c.embedding IS NOT NULL
          AND c.id = ANY(candidate_ids)
        ORDER BY c.embedding <=> query_embedding
        LIMIT match_count;
    ELSE
        RETURN QUERY
        SELECT c.id, (c.embedding <=> query_embedding)::float AS distance
        FROM candidates c
        WHERE c.embedding IS NOT NULL
        ORDER BY c.embedding <=> query_embedding
        LIMIT match_count;
    END IF;
END;
$$;
