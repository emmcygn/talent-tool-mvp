# Agent B — Task 01: Bootstrap — Next.js + TypeScript Contracts

## Mission
Set up the Next.js frontend project with Tailwind CSS, shadcn/ui, and mirror all Python canonical contracts to TypeScript types.

## Context
Day 1, PAIR task. Agent A is simultaneously creating the Python backend and canonical contracts. Agent A commits first — read `backend/contracts/` to mirror types exactly. If Agent A hasn't committed yet, start with the Next.js scaffold and come back to types.

## Prerequisites
- Node.js 20+ installed
- npm available
- Agent A has committed Task 01 (contracts in `backend/contracts/`)

## Checklist
- [ ] Initialize Next.js project in `frontend/` with App Router, TypeScript, Tailwind CSS
- [ ] Install and configure shadcn/ui
- [ ] Install additional dependencies: `@supabase/supabase-js`, `@supabase/ssr`, `recharts`, `lucide-react`, `date-fns`
- [ ] Create `contracts/canonical.ts` — mirror all Python contracts to TypeScript
- [ ] Create `frontend/lib/types.ts` — re-export from canonical
- [ ] Create `frontend/lib/utils.ts` — cn() helper and formatting utilities
- [ ] Create `frontend/lib/supabase.ts` — Supabase client setup
- [ ] Create `frontend/lib/api.ts` — typed API client skeleton
- [ ] Verify: `cd frontend && npm run build` passes
- [ ] Commit: "Agent B Task 01: Bootstrap — Next.js + TypeScript contracts"

## Implementation Details

### Next.js Init

```bash
cd recruittech
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*" --use-npm
```

### Additional Dependencies

```bash
cd frontend
npm install @supabase/supabase-js @supabase/ssr recharts lucide-react date-fns clsx tailwind-merge class-variance-authority
npx shadcn@latest init -d
npx shadcn@latest add button card input label textarea select badge dialog dropdown-menu tabs toast separator skeleton avatar sheet command popover
```

### TypeScript Canonical Types (`contracts/canonical.ts`)

Mirror every Python contract exactly. Use string literal unions for enums (more ergonomic in TS than enum keyword).

```typescript
// ============================================================
// Shared Enums & Value Objects
// ============================================================

export type SeniorityLevel = "junior" | "mid" | "senior" | "lead" | "principal";
export type AvailabilityStatus = "immediate" | "1_month" | "3_months" | "not_looking";
export type RemotePolicy = "onsite" | "hybrid" | "remote";
export type RoleStatus = "draft" | "active" | "paused" | "filled" | "closed";
export type MatchStatus = "generated" | "shortlisted" | "dismissed" | "intro_requested";
export type ConfidenceLevel = "strong" | "good" | "possible";
export type HandoffStatus = "pending" | "accepted" | "declined" | "expired";
export type QuoteStatus = "generated" | "sent" | "accepted" | "declined" | "expired";
export type Visibility = "private" | "shared_specific" | "shared_all";
export type UserRole = "talent_partner" | "client" | "admin";

export type SignalType =
  | "candidate_ingested" | "candidate_viewed" | "candidate_shortlisted"
  | "candidate_dismissed" | "match_generated" | "intro_requested"
  | "handoff_sent" | "handoff_accepted" | "handoff_declined"
  | "quote_generated" | "placement_made" | "copilot_query";

export interface ExtractedSkill {
  name: string;
  years: number | null;
  confidence: number;
}

export interface RequiredSkill {
  name: string;
  min_years: number | null;
  importance: "required" | "preferred";
}

export interface ExperienceEntry {
  company: string;
  title: string;
  duration_months: number | null;
  industry: string | null;
}

export interface SalaryRange {
  min_amount: number | null;
  max_amount: number | null;
  currency: string;
}

export interface SkillMatch {
  skill_name: string;
  status: "matched" | "partial" | "missing";
  candidate_years: number | null;
  required_years: number | null;
}

export interface CandidateSource {
  adapter_name: string;
  external_id: string;
  ingested_at: string;
}

// ============================================================
// Candidate
// ============================================================

export interface CandidateCreate {
  first_name: string;
  last_name: string;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  linkedin_url?: string | null;
  cv_text?: string | null;
  profile_text?: string | null;
}

export interface Candidate {
  id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  location: string | null;
  linkedin_url: string | null;
  skills: ExtractedSkill[];
  experience: ExperienceEntry[];
  seniority: SeniorityLevel | null;
  salary_expectation: SalaryRange | null;
  availability: AvailabilityStatus | null;
  industries: string[];
  cv_text: string | null;
  profile_text: string | null;
  sources: CandidateSource[];
  dedup_group: string | null;
  dedup_confidence: number | null;
  extraction_confidence: number | null;
  extraction_flags: string[];
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface CandidateAnonymized {
  id: string;
  first_name: string;
  last_initial: string;
  location: string | null;
  skills: ExtractedSkill[];
  seniority: SeniorityLevel | null;
  availability: AvailabilityStatus | null;
  industries: string[];
  experience_years: number | null;
  is_pool_candidate: boolean;
}

// ============================================================
// Role
// ============================================================

export interface RoleCreate {
  title: string;
  description: string;
  organisation_id: string;
  salary_band?: SalaryRange | null;
  location?: string | null;
  remote_policy?: RemotePolicy;
}

export interface Role {
  id: string;
  title: string;
  description: string;
  organisation_id: string;
  required_skills: RequiredSkill[];
  preferred_skills: RequiredSkill[];
  seniority: SeniorityLevel | null;
  salary_band: SalaryRange | null;
  location: string | null;
  remote_policy: RemotePolicy;
  industry: string | null;
  extraction_confidence: number | null;
  status: RoleStatus;
  created_at: string;
  created_by: string;
}

// ============================================================
// Match
// ============================================================

export interface Match {
  id: string;
  candidate_id: string;
  role_id: string;
  overall_score: number;
  structured_score: number;
  semantic_score: number;
  skill_overlap: SkillMatch[];
  confidence: ConfidenceLevel;
  explanation: string;
  strengths: string[];
  gaps: string[];
  recommendation: string;
  scoring_breakdown: Record<string, unknown>;
  model_version: string;
  created_at: string;
  status: MatchStatus;
}

// ============================================================
// Signal
// ============================================================

export interface SignalCreate {
  event_type: SignalType;
  actor_id: string;
  actor_role: UserRole;
  entity_type: string;
  entity_id: string;
  metadata?: Record<string, unknown>;
}

export interface Signal {
  id: string;
  event_type: SignalType;
  actor_id: string;
  actor_role: UserRole;
  entity_type: string;
  entity_id: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

// ============================================================
// Handoff
// ============================================================

export interface HandoffCreate {
  to_partner_id: string;
  candidate_ids: string[];
  context_notes: string;
  target_role_id?: string | null;
}

export interface Handoff {
  id: string;
  from_partner_id: string;
  to_partner_id: string;
  candidate_ids: string[];
  context_notes: string;
  target_role_id: string | null;
  status: HandoffStatus;
  response_notes: string | null;
  attribution_id: string;
  created_at: string;
  responded_at: string | null;
}

// ============================================================
// Quote
// ============================================================

export interface QuoteRequest {
  candidate_id: string;
  role_id: string;
}

export interface Quote {
  id: string;
  client_id: string;
  candidate_id: string;
  role_id: string;
  is_pool_candidate: boolean;
  base_fee: number;
  pool_discount: number | null;
  final_fee: number;
  fee_breakdown: Record<string, unknown>;
  status: QuoteStatus;
  created_at: string;
  expires_at: string;
}

// ============================================================
// Collection
// ============================================================

export interface CollectionCreate {
  name: string;
  description?: string | null;
  visibility?: Visibility;
  shared_with?: string[] | null;
  tags?: string[];
}

export interface Collection {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  visibility: Visibility;
  shared_with: string[] | null;
  candidate_ids: string[];
  tags: string[];
  candidate_count: number;
  avg_match_score: number | null;
  available_now_count: number;
  created_at: string;
  updated_at: string;
}

// ============================================================
// Organisation & User (additional types for frontend)
// ============================================================

export interface Organisation {
  id: string;
  name: string;
  industry: string | null;
  website: string | null;
  location: string | null;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organisation_id: string | null;
  avatar_url: string | null;
  created_at: string;
}
```

### API Client Skeleton (`frontend/lib/api.ts`)

```typescript
import type {
  Candidate, CandidateCreate, CandidateAnonymized,
  Role, RoleCreate,
  Match,
  Collection, CollectionCreate,
  Handoff, HandoffCreate,
  Quote, QuoteRequest,
  Signal,
  User, Organisation,
} from "@/contracts/canonical";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// Candidate endpoints
export const api = {
  candidates: {
    list: () => fetchAPI<Candidate[]>("/api/candidates"),
    get: (id: string) => fetchAPI<Candidate>(`/api/candidates/${id}`),
    create: (data: CandidateCreate) =>
      fetchAPI<Candidate>("/api/candidates", { method: "POST", body: JSON.stringify(data) }),
    search: (query: string) => fetchAPI<Candidate[]>(`/api/candidates/search?q=${query}`),
  },
  roles: {
    list: () => fetchAPI<Role[]>("/api/roles"),
    get: (id: string) => fetchAPI<Role>(`/api/roles/${id}`),
    create: (data: RoleCreate) =>
      fetchAPI<Role>("/api/roles", { method: "POST", body: JSON.stringify(data) }),
  },
  matches: {
    forRole: (roleId: string) => fetchAPI<Match[]>(`/api/matches/role/${roleId}`),
    forCandidate: (candidateId: string) => fetchAPI<Match[]>(`/api/matches/candidate/${candidateId}`),
  },
  collections: {
    list: () => fetchAPI<Collection[]>("/api/collections"),
    create: (data: CollectionCreate) =>
      fetchAPI<Collection>("/api/collections", { method: "POST", body: JSON.stringify(data) }),
  },
  handoffs: {
    inbox: () => fetchAPI<Handoff[]>("/api/handoffs/inbox"),
    outbox: () => fetchAPI<Handoff[]>("/api/handoffs/outbox"),
    create: (data: HandoffCreate) =>
      fetchAPI<Handoff>("/api/handoffs", { method: "POST", body: JSON.stringify(data) }),
    respond: (id: string, accept: boolean, notes?: string) =>
      fetchAPI<Handoff>(`/api/handoffs/${id}/respond`, {
        method: "POST", body: JSON.stringify({ accept, notes })
      }),
  },
  quotes: {
    request: (data: QuoteRequest) =>
      fetchAPI<Quote>("/api/quotes", { method: "POST", body: JSON.stringify(data) }),
    list: () => fetchAPI<Quote[]>("/api/quotes"),
  },
  copilot: {
    query: (message: string) =>
      fetch(`${API_BASE}/api/copilot/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      }),  // Returns stream, don't parse JSON
  },
  signals: {
    recent: (limit?: number) => fetchAPI<Signal[]>(`/api/signals/recent?limit=${limit || 20}`),
  },
  admin: {
    stats: () => fetchAPI<Record<string, unknown>>("/api/admin/stats"),
    funnelData: () => fetchAPI<Record<string, unknown>>("/api/admin/funnel"),
    adapterHealth: () => fetchAPI<Record<string, unknown>[]>("/api/admin/adapters"),
  },
  health: () => fetchAPI<{ status: string }>("/api/health"),
};
```

### Supabase Client (`frontend/lib/supabase.ts`)

```typescript
import { createBrowserClient } from "@supabase/ssr";

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
```

### Utils (`frontend/lib/utils.ts`)

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, currency = "GBP"): string {
  return new Intl.NumberFormat("en-GB", { style: "currency", currency }).format(amount);
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-GB", {
    day: "numeric", month: "short", year: "numeric"
  });
}

export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateString);
}

export function confidenceColor(confidence: string): string {
  switch (confidence) {
    case "strong": return "text-green-600 bg-green-50 border-green-200";
    case "good": return "text-amber-600 bg-amber-50 border-amber-200";
    case "possible": return "text-slate-500 bg-slate-50 border-slate-200";
    default: return "text-slate-400 bg-slate-50 border-slate-200";
  }
}

export function skillMatchColor(status: string): string {
  switch (status) {
    case "matched": return "bg-green-100 text-green-800 border-green-300";
    case "partial": return "bg-amber-100 text-amber-800 border-amber-300";
    case "missing": return "bg-slate-100 text-slate-500 border-slate-300";
    default: return "bg-slate-100 text-slate-500 border-slate-300";
  }
}
```

## Outputs
- `frontend/` — complete Next.js project scaffold
- `contracts/canonical.ts` — all TypeScript types
- `frontend/lib/api.ts` — typed API client
- `frontend/lib/supabase.ts` — Supabase client
- `frontend/lib/utils.ts` — shared utilities

## Acceptance Criteria
1. `cd frontend && npm run build` — builds successfully
2. `cd frontend && npm run lint` — no errors
3. TypeScript types in `contracts/canonical.ts` mirror Python contracts exactly (field names, types, optionality)
4. API client compiles without type errors

## Handoff Notes
- **To Agent A:** TypeScript types are in `contracts/canonical.ts`. If you change a Python contract, note it in HANDOFF.md so I can update the TS mirror.
- **To Task 02:** All lib files exist. Supabase client ready. API client typed and ready. shadcn/ui components installed.
- **Decision:** Using string literal unions instead of TS enums for better DX. UUIDs as `string` in TS (not a UUID type). Dates as `string` (ISO format from API).
