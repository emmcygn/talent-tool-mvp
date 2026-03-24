-- =============================================================
-- RecruitTech PoC — Cloud-Safe Schema
-- For Supabase Cloud SQL Editor
-- =============================================================

-- Extensions (these are pre-enabled on Supabase Cloud, but safe to call)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- =============================================================
-- ENUMS
-- =============================================================

CREATE TYPE user_role AS ENUM ('talent_partner', 'client', 'admin');
CREATE TYPE seniority_level AS ENUM ('junior', 'mid', 'senior', 'lead', 'principal');
CREATE TYPE availability_status AS ENUM ('immediate', '1_month', '3_months', 'not_looking');
CREATE TYPE remote_policy AS ENUM ('onsite', 'hybrid', 'remote');
CREATE TYPE role_status AS ENUM ('draft', 'active', 'paused', 'filled', 'closed');
CREATE TYPE match_status AS ENUM ('generated', 'shortlisted', 'dismissed', 'intro_requested');
CREATE TYPE confidence_level AS ENUM ('strong', 'good', 'possible');
CREATE TYPE handoff_status AS ENUM ('pending', 'accepted', 'declined', 'expired');
CREATE TYPE quote_status AS ENUM ('generated', 'sent', 'accepted', 'declined', 'expired');
CREATE TYPE collection_visibility AS ENUM ('private', 'shared_specific', 'shared_all');
CREATE TYPE signal_type AS ENUM (
    'candidate_ingested', 'candidate_viewed', 'candidate_shortlisted',
    'candidate_dismissed', 'match_generated', 'intro_requested',
    'handoff_sent', 'handoff_accepted', 'handoff_declined',
    'quote_generated', 'placement_made', 'copilot_query'
);

-- =============================================================
-- TABLES
-- =============================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT NOT NULL UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    role user_role NOT NULL DEFAULT 'talent_partner',
    organisation_id UUID,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE organisations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    industry TEXT,
    website TEXT,
    location TEXT,
    description TEXT,
    size TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE users
    ADD CONSTRAINT fk_users_organisation
    FOREIGN KEY (organisation_id) REFERENCES organisations(id);

CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    location TEXT,
    linkedin_url TEXT,
    skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    experience JSONB NOT NULL DEFAULT '[]'::jsonb,
    seniority seniority_level,
    salary_expectation JSONB,
    availability availability_status,
    industries JSONB NOT NULL DEFAULT '[]'::jsonb,
    cv_text TEXT,
    profile_text TEXT,
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    dedup_group UUID,
    dedup_confidence FLOAT,
    embedding vector(1536),
    extraction_confidence FLOAT,
    extraction_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL REFERENCES users(id)
);

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    organisation_id UUID NOT NULL REFERENCES organisations(id),
    required_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    preferred_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    seniority seniority_level,
    salary_band JSONB,
    location TEXT,
    remote_policy remote_policy NOT NULL DEFAULT 'hybrid',
    industry TEXT,
    embedding vector(1536),
    extraction_confidence FLOAT,
    status role_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL REFERENCES users(id)
);

CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    overall_score FLOAT NOT NULL,
    structured_score FLOAT NOT NULL,
    semantic_score FLOAT NOT NULL,
    experience_score FLOAT NOT NULL DEFAULT 0.0,
    skill_overlap JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence confidence_level NOT NULL,
    explanation TEXT NOT NULL DEFAULT '',
    strengths JSONB NOT NULL DEFAULT '[]'::jsonb,
    gaps JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommendation TEXT NOT NULL DEFAULT '',
    scoring_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_version TEXT NOT NULL DEFAULT '',
    status match_status NOT NULL DEFAULT 'generated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(candidate_id, role_id)
);

CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type signal_type NOT NULL,
    actor_id UUID NOT NULL REFERENCES users(id),
    actor_role user_role NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE handoffs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_partner_id UUID NOT NULL REFERENCES users(id),
    to_partner_id UUID NOT NULL REFERENCES users(id),
    candidate_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    context_notes TEXT NOT NULL,
    target_role_id UUID REFERENCES roles(id),
    status handoff_status NOT NULL DEFAULT 'pending',
    response_notes TEXT,
    attribution_id UUID NOT NULL DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    responded_at TIMESTAMPTZ
);

CREATE TABLE quotes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES users(id),
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    role_id UUID NOT NULL REFERENCES roles(id),
    is_pool_candidate BOOLEAN NOT NULL DEFAULT false,
    base_fee DECIMAL(12,2) NOT NULL,
    pool_discount DECIMAL(12,2),
    final_fee DECIMAL(12,2) NOT NULL,
    fee_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
    status quote_status NOT NULL DEFAULT 'generated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id),
    visibility collection_visibility NOT NULL DEFAULT 'private',
    shared_with JSONB,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    candidate_count INTEGER NOT NULL DEFAULT 0,
    avg_match_score FLOAT,
    available_now_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE collection_candidates (
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (collection_id, candidate_id)
);

-- =============================================================
-- INDEXES
-- =============================================================

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_organisation ON users(organisation_id);
CREATE INDEX idx_candidates_email ON candidates(email);
CREATE INDEX idx_candidates_created_by ON candidates(created_by);
CREATE INDEX idx_candidates_seniority ON candidates(seniority);
CREATE INDEX idx_candidates_availability ON candidates(availability);
CREATE INDEX idx_candidates_dedup_group ON candidates(dedup_group);
CREATE INDEX idx_candidates_created_at ON candidates(created_at DESC);
CREATE INDEX idx_candidates_embedding ON candidates
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_roles_organisation ON roles(organisation_id);
CREATE INDEX idx_roles_status ON roles(status);
CREATE INDEX idx_roles_created_by ON roles(created_by);
CREATE INDEX idx_roles_created_at ON roles(created_at DESC);
CREATE INDEX idx_roles_embedding ON roles
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_matches_candidate ON matches(candidate_id);
CREATE INDEX idx_matches_role ON matches(role_id);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_score ON matches(overall_score DESC);
CREATE INDEX idx_matches_confidence ON matches(confidence);
CREATE INDEX idx_signals_event_type ON signals(event_type);
CREATE INDEX idx_signals_actor ON signals(actor_id);
CREATE INDEX idx_signals_entity ON signals(entity_type, entity_id);
CREATE INDEX idx_signals_created_at ON signals(created_at DESC);
CREATE INDEX idx_handoffs_from ON handoffs(from_partner_id);
CREATE INDEX idx_handoffs_to ON handoffs(to_partner_id);
CREATE INDEX idx_handoffs_status ON handoffs(status);
CREATE INDEX idx_quotes_client ON quotes(client_id);
CREATE INDEX idx_quotes_candidate ON quotes(candidate_id);
CREATE INDEX idx_quotes_role ON quotes(role_id);
CREATE INDEX idx_quotes_status ON quotes(status);
CREATE INDEX idx_collections_owner ON collections(owner_id);
CREATE INDEX idx_collections_visibility ON collections(visibility);

-- =============================================================
-- ROW LEVEL SECURITY
-- =============================================================

-- Helper functions in PUBLIC schema (not auth — Cloud doesn't allow auth schema writes)
CREATE OR REPLACE FUNCTION public.get_user_role()
RETURNS user_role AS $$
    SELECT (auth.jwt() -> 'user_metadata' ->> 'role')::user_role;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.get_uid_text()
RETURNS TEXT AS $$
    SELECT auth.uid()::text;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- ---- USERS ----
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY users_admin_all ON users
    FOR ALL TO authenticated
    USING (public.get_user_role() = 'admin');

CREATE POLICY users_self_read ON users
    FOR SELECT TO authenticated
    USING (id = auth.uid());

CREATE POLICY users_talent_partner_read ON users
    FOR SELECT TO authenticated
    USING (public.get_user_role() = 'talent_partner');

-- ---- ORGANISATIONS ----
ALTER TABLE organisations ENABLE ROW LEVEL SECURITY;

CREATE POLICY orgs_admin_all ON organisations
    FOR ALL TO authenticated
    USING (public.get_user_role() = 'admin');

CREATE POLICY orgs_read ON organisations
    FOR SELECT TO authenticated
    USING (true);

-- ---- CANDIDATES ----
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;

CREATE POLICY candidates_admin_all ON candidates
    FOR ALL TO authenticated
    USING (public.get_user_role() = 'admin');

CREATE POLICY candidates_tp_read ON candidates
    FOR SELECT TO authenticated
    USING (public.get_user_role() = 'talent_partner');

CREATE POLICY candidates_tp_insert ON candidates
    FOR INSERT TO authenticated
    WITH CHECK (public.get_user_role() = 'talent_partner' AND created_by = auth.uid());

CREATE POLICY candidates_tp_update ON candidates
    FOR UPDATE TO authenticated
    USING (public.get_user_role() = 'talent_partner' AND created_by = auth.uid());

CREATE POLICY candidates_client_read ON candidates
    FOR SELECT TO authenticated
    USING (
        public.get_user_role() = 'client'
        AND id IN (
            SELECT candidate_id FROM matches m
            JOIN roles r ON m.role_id = r.id
            WHERE r.created_by = auth.uid()
        )
    );

-- ---- ROLES ----
ALTER TABLE roles ENABLE ROW LEVEL SECURITY;

CREATE POLICY roles_admin_all ON roles
    FOR ALL TO authenticated
    USING (public.get_user_role() = 'admin');

CREATE POLICY roles_tp_read ON roles
    FOR SELECT TO authenticated
    USING (public.get_user_role() = 'talent_partner');

CREATE POLICY roles_client_own ON roles
    FOR ALL TO authenticated
    USING (public.get_user_role() = 'client' AND created_by = auth.uid())
    WITH CHECK (public.get_user_role() = 'client' AND created_by = auth.uid());

-- ---- MATCHES ----
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;

CREATE POLICY matches_admin_all ON matches
    FOR ALL TO authenticated
    USING (public.get_user_role() = 'admin');

CREATE POLICY matches_tp_read ON matches
    FOR SELECT TO authenticated
    USING (public.get_user_role() = 'talent_partner');

CREATE POLICY matches_client_own_roles ON matches
    FOR SELECT TO authenticated
    USING (
        public.get_user_role() = 'client'
        AND role_id IN (SELECT id FROM roles WHERE created_by = auth.uid())
    );

-- ---- SIGNALS ----
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;

CREATE POLICY signals_admin_all ON signals
    FOR ALL TO authenticated
    USING (public.get_user_role() = 'admin');

CREATE POLICY signals_own_read ON signals
    FOR SELECT TO authenticated
    USING (actor_id = auth.uid());

CREATE POLICY signals_insert ON signals
    FOR INSERT TO authenticated
    WITH CHECK (actor_id = auth.uid());

-- ---- HANDOFFS ----
ALTER TABLE handoffs ENABLE ROW LEVEL SECURITY;

CREATE POLICY handoffs_admin_all ON handoffs
    FOR ALL TO authenticated
    USING (public.get_user_role() = 'admin');

CREATE POLICY handoffs_tp_own ON handoffs
    FOR SELECT TO authenticated
    USING (
        public.get_user_role() = 'talent_partner'
        AND (from_partner_id = auth.uid() OR to_partner_id = auth.uid())
    );

CREATE POLICY handoffs_tp_insert ON handoffs
    FOR INSERT TO authenticated
    WITH CHECK (
        public.get_user_role() = 'talent_partner'
        AND from_partner_id = auth.uid()
    );

CREATE POLICY handoffs_tp_update ON handoffs
    FOR UPDATE TO authenticated
    USING (
        public.get_user_role() = 'talent_partner'
        AND to_partner_id = auth.uid()
    );

-- ---- QUOTES ----
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;

CREATE POLICY quotes_admin_all ON quotes
    FOR ALL TO authenticated
    USING (public.get_user_role() = 'admin');

CREATE POLICY quotes_client_own ON quotes
    FOR SELECT TO authenticated
    USING (public.get_user_role() = 'client' AND client_id = auth.uid());

CREATE POLICY quotes_tp_read ON quotes
    FOR SELECT TO authenticated
    USING (public.get_user_role() = 'talent_partner');

-- ---- COLLECTIONS ----
ALTER TABLE collections ENABLE ROW LEVEL SECURITY;

CREATE POLICY collections_admin_all ON collections
    FOR ALL TO authenticated
    USING (public.get_user_role() = 'admin');

CREATE POLICY collections_tp_own ON collections
    FOR ALL TO authenticated
    USING (public.get_user_role() = 'talent_partner' AND owner_id = auth.uid())
    WITH CHECK (public.get_user_role() = 'talent_partner' AND owner_id = auth.uid());

CREATE POLICY collections_tp_shared ON collections
    FOR SELECT TO authenticated
    USING (
        public.get_user_role() = 'talent_partner'
        AND (
            visibility = 'shared_all'
            OR (
                visibility = 'shared_specific'
                AND shared_with ? auth.uid()::text
            )
        )
    );

-- ---- COLLECTION_CANDIDATES ----
ALTER TABLE collection_candidates ENABLE ROW LEVEL SECURITY;

CREATE POLICY cc_admin_all ON collection_candidates
    FOR ALL TO authenticated
    USING (public.get_user_role() = 'admin');

CREATE POLICY cc_tp_own ON collection_candidates
    FOR ALL TO authenticated
    USING (
        collection_id IN (
            SELECT id FROM collections WHERE owner_id = auth.uid()
        )
    )
    WITH CHECK (
        collection_id IN (
            SELECT id FROM collections WHERE owner_id = auth.uid()
        )
    );

CREATE POLICY cc_tp_shared_read ON collection_candidates
    FOR SELECT TO authenticated
    USING (
        collection_id IN (
            SELECT id FROM collections
            WHERE visibility = 'shared_all'
            OR (visibility = 'shared_specific' AND shared_with ? auth.uid()::text)
        )
    );

-- =============================================================
-- REALTIME
-- =============================================================
ALTER PUBLICATION supabase_realtime ADD TABLE matches;
ALTER PUBLICATION supabase_realtime ADD TABLE handoffs;
ALTER PUBLICATION supabase_realtime ADD TABLE quotes;
ALTER PUBLICATION supabase_realtime ADD TABLE signals;

-- =============================================================
-- UPDATED_AT TRIGGER
-- =============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER tr_candidates_updated_at
    BEFORE UPDATE ON candidates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER tr_organisations_updated_at
    BEFORE UPDATE ON organisations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER tr_collections_updated_at
    BEFORE UPDATE ON collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
