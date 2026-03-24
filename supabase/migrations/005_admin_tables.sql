-- Deduplication review queue
CREATE TABLE IF NOT EXISTS dedup_queue (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_a_id uuid NOT NULL REFERENCES candidates(id),
    candidate_b_id uuid NOT NULL REFERENCES candidates(id),
    match_type text NOT NULL,  -- 'exact_email', 'fuzzy_name', 'semantic'
    confidence float NOT NULL,
    status text NOT NULL DEFAULT 'pending',  -- pending, approved, rejected
    resolved_by uuid REFERENCES users(id),
    resolved_at timestamptz,
    resolution_notes text,
    created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dedup_queue_status ON dedup_queue(status);
CREATE INDEX IF NOT EXISTS idx_dedup_queue_confidence ON dedup_queue(confidence DESC);

-- Users table is created in 001_initial_schema.sql with first_name, last_name, role (user_role enum).
-- No duplicate definition needed here.

-- RLS for admin-only tables
ALTER TABLE dedup_queue ENABLE ROW LEVEL SECURITY;
CREATE POLICY "dedup_queue_admin_only" ON dedup_queue
    FOR ALL USING (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role = 'admin')
    );
