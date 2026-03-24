# Agent A — Task 02: Supabase Schema + Migrations

## Mission
Create the full PostgreSQL database schema with pgvector extension, all tables mapping to canonical contracts, Row Level Security policies for three roles, and Supabase project configuration.

## Context
Day 1 task, immediately follows Task 01 (contracts). The schema is the physical data layer that backs every canonical contract. It must support pgvector for embedding similarity search, RLS for multi-tenant access control, and efficient indexes for common query patterns. Supabase provides PostgreSQL + Auth + Realtime + RLS out of the box.

## Prerequisites
- Task 01 complete (all canonical Pydantic contracts exist in `backend/contracts/`)
- Supabase CLI installed (`npx supabase init` or Docker-based local dev)
- Docker available for local Supabase

## Checklist
- [ ] Create `supabase/config.toml` with project configuration
- [ ] Create `supabase/migrations/001_initial_schema.sql` with full schema
- [ ] Enable `pgvector` extension
- [ ] Create `users` table with role enum
- [ ] Create `organisations` table
- [ ] Create `candidates` table with JSONB fields for structured data and pgvector column
- [ ] Create `roles` table with JSONB fields and pgvector column
- [ ] Create `matches` table with scoring fields
- [ ] Create `signals` table for event tracking
- [ ] Create `handoffs` table with status lifecycle
- [ ] Create `quotes` table with pricing fields
- [ ] Create `collections` table with visibility
- [ ] Create `collection_candidates` junction table
- [ ] Add indexes for common queries (email, org, status, created_at)
- [ ] Add HNSW index on embedding columns for pgvector
- [ ] Create RLS policies for `talent_partner`, `client`, `admin` roles
- [ ] Enable RLS on all tables
- [ ] Enable Realtime on key tables (matches, handoffs, quotes, signals)
- [ ] Create `docker-compose.yml` for local Supabase + backend
- [ ] Verify migration runs against local Supabase
- [ ] Commit

## Implementation Details

### Supabase Config (`supabase/config.toml`)

```toml
[project]
id = "recruittech-local"
name = "RecruitTech PoC"

[api]
enabled = true
port = 54321
schemas = ["public"]

[db]
port = 54322
major_version = 15

[auth]
enabled = true
site_url = "http://localhost:3000"
additional_redirect_urls = ["http://localhost:3000"]
jwt_expiry = 3600

[auth.email]
enable_signup = true
enable_confirmations = false
```

### Docker Compose (`docker-compose.yml`)

```yaml
version: "3.8"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=http://supabase-kong:8000
      - SUPABASE_KEY=${SUPABASE_ANON_KEY}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://postgres:postgres@supabase-db:5432/postgres
    depends_on:
      - supabase-db
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  supabase-db:
    image: supabase/postgres:15.6.1.143
    ports:
      - "54322:5432"
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: postgres
    volumes:
      - supabase-db-data:/var/lib/postgresql/data
      - ./supabase/migrations:/docker-entrypoint-initdb.d

volumes:
  supabase-db-data:
```

### Migration (`supabase/migrations/001_initial_schema.sql`)

```sql
-- =============================================================
-- RecruitTech PoC — Initial Schema
-- Supports: pgvector, RLS, Realtime
-- =============================================================

-- Extensions
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

-- Users (extends Supabase auth.users)
CREATE TABLE users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role user_role NOT NULL DEFAULT 'talent_partner',
    organisation_id UUID,  -- FK added after organisations table
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Organisations (client companies)
CREATE TABLE organisations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    industry TEXT,
    website TEXT,
    location TEXT,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add FK from users to organisations
ALTER TABLE users
    ADD CONSTRAINT fk_users_organisation
    FOREIGN KEY (organisation_id) REFERENCES organisations(id);

-- Candidates
CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    location TEXT,
    linkedin_url TEXT,

    -- Structured (LLM-extracted), stored as JSONB
    skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    experience JSONB NOT NULL DEFAULT '[]'::jsonb,
    seniority seniority_level,
    salary_expectation JSONB,
    availability availability_status,
    industries JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- Raw text
    cv_text TEXT,
    profile_text TEXT,

    -- Source tracking (JSONB array of {adapter_name, external_id, ingested_at})
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    dedup_group UUID,
    dedup_confidence FLOAT,

    -- Embedding (1536 dimensions for text-embedding-3-small)
    embedding vector(1536),

    -- Extraction metadata
    extraction_confidence FLOAT,
    extraction_flags JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- System
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL REFERENCES users(id)
);

-- Roles
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    organisation_id UUID NOT NULL REFERENCES organisations(id),

    -- Structured (LLM-extracted)
    required_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    preferred_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    seniority seniority_level,
    salary_band JSONB,
    location TEXT,
    remote_policy remote_policy NOT NULL DEFAULT 'hybrid',
    industry TEXT,

    -- Embedding
    embedding vector(1536),

    -- Extraction metadata
    extraction_confidence FLOAT,

    -- System
    status role_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID NOT NULL REFERENCES users(id)
);

-- Matches
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,

    -- Scoring
    overall_score FLOAT NOT NULL,
    structured_score FLOAT NOT NULL,
    semantic_score FLOAT NOT NULL,
    skill_overlap JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence confidence_level NOT NULL,

    -- Explanation
    explanation TEXT NOT NULL DEFAULT '',
    strengths JSONB NOT NULL DEFAULT '[]'::jsonb,
    gaps JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommendation TEXT NOT NULL DEFAULT '',

    -- Traceability
    scoring_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_version TEXT NOT NULL DEFAULT '',

    -- System
    status match_status NOT NULL DEFAULT 'generated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE(candidate_id, role_id)
);

-- Signals (event tracking)
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

-- Handoffs
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

-- Quotes
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

-- Collections
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id),
    visibility collection_visibility NOT NULL DEFAULT 'private',
    shared_with JSONB,   -- array of user UUIDs if shared_specific
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Collection-Candidates junction
CREATE TABLE collection_candidates (
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (collection_id, candidate_id)
);

-- =============================================================
-- INDEXES
-- =============================================================

-- Users
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_organisation ON users(organisation_id);

-- Candidates
CREATE INDEX idx_candidates_email ON candidates(email);
CREATE INDEX idx_candidates_created_by ON candidates(created_by);
CREATE INDEX idx_candidates_seniority ON candidates(seniority);
CREATE INDEX idx_candidates_availability ON candidates(availability);
CREATE INDEX idx_candidates_dedup_group ON candidates(dedup_group);
CREATE INDEX idx_candidates_created_at ON candidates(created_at DESC);

-- pgvector HNSW index for fast approximate nearest neighbor search
CREATE INDEX idx_candidates_embedding ON candidates
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Roles
CREATE INDEX idx_roles_organisation ON roles(organisation_id);
CREATE INDEX idx_roles_status ON roles(status);
CREATE INDEX idx_roles_created_by ON roles(created_by);
CREATE INDEX idx_roles_created_at ON roles(created_at DESC);

-- pgvector HNSW index for roles
CREATE INDEX idx_roles_embedding ON roles
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Matches
CREATE INDEX idx_matches_candidate ON matches(candidate_id);
CREATE INDEX idx_matches_role ON matches(role_id);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_score ON matches(overall_score DESC);
CREATE INDEX idx_matches_confidence ON matches(confidence);

-- Signals
CREATE INDEX idx_signals_event_type ON signals(event_type);
CREATE INDEX idx_signals_actor ON signals(actor_id);
CREATE INDEX idx_signals_entity ON signals(entity_type, entity_id);
CREATE INDEX idx_signals_created_at ON signals(created_at DESC);

-- Handoffs
CREATE INDEX idx_handoffs_from ON handoffs(from_partner_id);
CREATE INDEX idx_handoffs_to ON handoffs(to_partner_id);
CREATE INDEX idx_handoffs_status ON handoffs(status);

-- Quotes
CREATE INDEX idx_quotes_client ON quotes(client_id);
CREATE INDEX idx_quotes_candidate ON quotes(candidate_id);
CREATE INDEX idx_quotes_role ON quotes(role_id);
CREATE INDEX idx_quotes_status ON quotes(status);

-- Collections
CREATE INDEX idx_collections_owner ON collections(owner_id);
CREATE INDEX idx_collections_visibility ON collections(visibility);

-- =============================================================
-- ROW LEVEL SECURITY
-- =============================================================

-- Helper function: get current user's role from JWT
CREATE OR REPLACE FUNCTION auth.user_role()
RETURNS user_role AS $$
    SELECT (auth.jwt() -> 'user_metadata' ->> 'role')::user_role;
$$ LANGUAGE sql STABLE;

-- Helper function: get current user's ID
CREATE OR REPLACE FUNCTION auth.uid_text()
RETURNS TEXT AS $$
    SELECT auth.uid()::text;
$$ LANGUAGE sql STABLE;

-- ---- USERS ----
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY users_admin_all ON users
    FOR ALL TO authenticated
    USING (auth.user_role() = 'admin');

CREATE POLICY users_self_read ON users
    FOR SELECT TO authenticated
    USING (id = auth.uid());

CREATE POLICY users_talent_partner_read ON users
    FOR SELECT TO authenticated
    USING (auth.user_role() = 'talent_partner');

-- ---- ORGANISATIONS ----
ALTER TABLE organisations ENABLE ROW LEVEL SECURITY;

CREATE POLICY orgs_admin_all ON organisations
    FOR ALL TO authenticated
    USING (auth.user_role() = 'admin');

CREATE POLICY orgs_read ON organisations
    FOR SELECT TO authenticated
    USING (true);  -- all authenticated users can read orgs

-- ---- CANDIDATES ----
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;

CREATE POLICY candidates_admin_all ON candidates
    FOR ALL TO authenticated
    USING (auth.user_role() = 'admin');

CREATE POLICY candidates_tp_read ON candidates
    FOR SELECT TO authenticated
    USING (auth.user_role() = 'talent_partner');

CREATE POLICY candidates_tp_insert ON candidates
    FOR INSERT TO authenticated
    WITH CHECK (auth.user_role() = 'talent_partner' AND created_by = auth.uid());

CREATE POLICY candidates_tp_update ON candidates
    FOR UPDATE TO authenticated
    USING (auth.user_role() = 'talent_partner' AND created_by = auth.uid());

CREATE POLICY candidates_client_read ON candidates
    FOR SELECT TO authenticated
    USING (
        auth.user_role() = 'client'
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
    USING (auth.user_role() = 'admin');

CREATE POLICY roles_tp_read ON roles
    FOR SELECT TO authenticated
    USING (auth.user_role() = 'talent_partner');

CREATE POLICY roles_client_own ON roles
    FOR ALL TO authenticated
    USING (auth.user_role() = 'client' AND created_by = auth.uid())
    WITH CHECK (auth.user_role() = 'client' AND created_by = auth.uid());

-- ---- MATCHES ----
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;

CREATE POLICY matches_admin_all ON matches
    FOR ALL TO authenticated
    USING (auth.user_role() = 'admin');

CREATE POLICY matches_tp_read ON matches
    FOR SELECT TO authenticated
    USING (auth.user_role() = 'talent_partner');

CREATE POLICY matches_client_own_roles ON matches
    FOR SELECT TO authenticated
    USING (
        auth.user_role() = 'client'
        AND role_id IN (SELECT id FROM roles WHERE created_by = auth.uid())
    );

-- ---- SIGNALS ----
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;

CREATE POLICY signals_admin_all ON signals
    FOR ALL TO authenticated
    USING (auth.user_role() = 'admin');

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
    USING (auth.user_role() = 'admin');

CREATE POLICY handoffs_tp_own ON handoffs
    FOR SELECT TO authenticated
    USING (
        auth.user_role() = 'talent_partner'
        AND (from_partner_id = auth.uid() OR to_partner_id = auth.uid())
    );

CREATE POLICY handoffs_tp_insert ON handoffs
    FOR INSERT TO authenticated
    WITH CHECK (
        auth.user_role() = 'talent_partner'
        AND from_partner_id = auth.uid()
    );

CREATE POLICY handoffs_tp_update ON handoffs
    FOR UPDATE TO authenticated
    USING (
        auth.user_role() = 'talent_partner'
        AND to_partner_id = auth.uid()
    );

-- ---- QUOTES ----
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;

CREATE POLICY quotes_admin_all ON quotes
    FOR ALL TO authenticated
    USING (auth.user_role() = 'admin');

CREATE POLICY quotes_client_own ON quotes
    FOR SELECT TO authenticated
    USING (auth.user_role() = 'client' AND client_id = auth.uid());

CREATE POLICY quotes_tp_read ON quotes
    FOR SELECT TO authenticated
    USING (auth.user_role() = 'talent_partner');

-- ---- COLLECTIONS ----
ALTER TABLE collections ENABLE ROW LEVEL SECURITY;

CREATE POLICY collections_admin_all ON collections
    FOR ALL TO authenticated
    USING (auth.user_role() = 'admin');

CREATE POLICY collections_tp_own ON collections
    FOR ALL TO authenticated
    USING (auth.user_role() = 'talent_partner' AND owner_id = auth.uid())
    WITH CHECK (auth.user_role() = 'talent_partner' AND owner_id = auth.uid());

CREATE POLICY collections_tp_shared ON collections
    FOR SELECT TO authenticated
    USING (
        auth.user_role() = 'talent_partner'
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
    USING (auth.user_role() = 'admin');

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
-- Enable Realtime on tables that need live updates
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
```

## Outputs
- `supabase/config.toml`
- `supabase/migrations/001_initial_schema.sql`
- `docker-compose.yml`

## Acceptance Criteria
1. Migration SQL executes without errors against a fresh PostgreSQL 15 instance with pgvector
2. All tables exist with correct columns and types matching canonical contracts
3. `\d candidates` shows `embedding` column of type `vector(1536)`
4. HNSW indexes exist on `candidates.embedding` and `roles.embedding`
5. RLS is enabled on all tables — `SELECT relrowsecurity FROM pg_class WHERE relname = 'candidates'` returns `true`
6. Admin role can read/write all tables; talent_partner sees only own + shared data; client sees only matched candidates for own roles
7. Realtime publication includes matches, handoffs, quotes, signals
8. `updated_at` triggers fire correctly on UPDATE

## Handoff Notes
- **To Task 03:** Schema is ready. FastAPI auth helpers should extract `user_role` from Supabase JWT `user_metadata.role` — this matches the `auth.user_role()` SQL function.
- **To Agent B:** Supabase Realtime is enabled on `matches`, `handoffs`, `quotes`, `signals`. Subscribe to these for live updates.
- **Decision:** JSONB used for `skills`, `experience`, `sources`, `extraction_flags`, `skill_overlap`, `strengths`, `gaps`, `scoring_breakdown`, `fee_breakdown`, `candidate_ids` (on handoffs), `shared_with`, `tags`. This avoids excessive normalization for a PoC while keeping query flexibility.
- **Decision:** `collection_candidates` is a proper junction table (not JSONB array) to support efficient queries and proper FK constraints.
