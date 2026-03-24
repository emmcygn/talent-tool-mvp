# Agent B — Task 04: API Client + Mock Layer

## Mission
Expand the API client from Task 01 with auth token injection from the Supabase session, error handling, and retry logic. Create a mock data layer that returns realistic data conforming to canonical types, toggled via environment variable, so frontend development can proceed independently of the backend.

## Context
Day 2. The API client skeleton exists from Task 01 but lacks auth headers and error handling. The backend may not be ready yet, so a mock layer is essential. The mock layer must return data that exactly matches canonical TypeScript types so components built against mocks work seamlessly when swapped to the real API.

## Prerequisites
- Agent B Task 01 complete (API client skeleton in `lib/api.ts`, Supabase client, canonical types)
- Agent B Task 02 complete (auth provider with session management)

## Checklist
- [ ] Enhance `lib/api.ts` — auth token injection, error class, retry logic, response typing
- [ ] Create `lib/mock-data.ts` — realistic mock data for candidates, roles, matches, collections
- [ ] Create `lib/api-mock.ts` — mock API implementation matching the same interface as `lib/api.ts`
- [ ] Create `lib/api-client.ts` — unified export that switches between real and mock based on `NEXT_PUBLIC_USE_MOCKS`
- [ ] Add `NEXT_PUBLIC_USE_MOCKS=true` to `.env.local.example`
- [ ] Verify: mock API returns typed data, all existing code compiles
- [ ] Commit: "Agent B Task 04: API client with auth + mock data layer"

## Implementation Details

### Enhanced API Client (`lib/api.ts`)

```typescript
import { createClient } from "@/lib/supabase";
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
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1000;

// Custom error class for API errors
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body?: unknown
  ) {
    super(`API error: ${status} ${statusText}`);
    this.name = "ApiError";
  }
}

async function getAuthToken(): Promise<string | null> {
  const supabase = createClient();
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

async function fetchAPI<T>(
  path: string,
  options?: RequestInit & { retries?: number }
): Promise<T> {
  const token = await getAuthToken();
  const retries = options?.retries ?? MAX_RETRIES;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options?.headers as Record<string, string> ?? {}),
  };

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
      });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new ApiError(res.status, res.statusText, body);
      }

      // Handle 204 No Content
      if (res.status === 204) return undefined as T;

      return await res.json();
    } catch (err) {
      lastError = err as Error;

      // Don't retry client errors (4xx) except 429
      if (err instanceof ApiError && err.status >= 400 && err.status < 500 && err.status !== 429) {
        throw err;
      }

      // Retry with exponential backoff for server errors and network errors
      if (attempt < retries) {
        await new Promise((resolve) =>
          setTimeout(resolve, RETRY_DELAY_MS * Math.pow(2, attempt))
        );
      }
    }
  }

  throw lastError!;
}

export const api = {
  candidates: {
    list: () => fetchAPI<Candidate[]>("/api/candidates"),
    get: (id: string) => fetchAPI<Candidate>(`/api/candidates/${id}`),
    create: (data: CandidateCreate) =>
      fetchAPI<Candidate>("/api/candidates", { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: Partial<CandidateCreate>) =>
      fetchAPI<Candidate>(`/api/candidates/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    search: (query: string) => fetchAPI<Candidate[]>(`/api/candidates/search?q=${encodeURIComponent(query)}`),
    uploadCV: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return fetchAPI<Candidate>("/api/candidates/upload", {
        method: "POST",
        body: formData,
        headers: {}, // Let browser set Content-Type with boundary
      });
    },
    extractFromText: (text: string) =>
      fetchAPI<Candidate>("/api/candidates/extract", { method: "POST", body: JSON.stringify({ text }) }),
  },
  roles: {
    list: () => fetchAPI<Role[]>("/api/roles"),
    get: (id: string) => fetchAPI<Role>(`/api/roles/${id}`),
    create: (data: RoleCreate) =>
      fetchAPI<Role>("/api/roles", { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: Partial<RoleCreate>) =>
      fetchAPI<Role>(`/api/roles/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    extractRequirements: (description: string) =>
      fetchAPI<{ required_skills: Role["required_skills"]; preferred_skills: Role["preferred_skills"]; seniority: Role["seniority"] }>(
        "/api/roles/extract-requirements", { method: "POST", body: JSON.stringify({ description }) }
      ),
  },
  matches: {
    forRole: (roleId: string) => fetchAPI<Match[]>(`/api/matches/role/${roleId}`),
    forCandidate: (candidateId: string) => fetchAPI<Match[]>(`/api/matches/candidate/${candidateId}`),
    updateStatus: (matchId: string, status: Match["status"], reason?: string) =>
      fetchAPI<Match>(`/api/matches/${matchId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status, reason }),
      }),
    forRoleAnonymized: (roleId: string) =>
      fetchAPI<{ match: Match; candidate: CandidateAnonymized }[]>(`/api/matches/role/${roleId}/anonymized`),
  },
  collections: {
    list: () => fetchAPI<Collection[]>("/api/collections"),
    get: (id: string) => fetchAPI<Collection>(`/api/collections/${id}`),
    create: (data: CollectionCreate) =>
      fetchAPI<Collection>("/api/collections", { method: "POST", body: JSON.stringify(data) }),
    addCandidate: (collectionId: string, candidateId: string) =>
      fetchAPI<Collection>(`/api/collections/${collectionId}/candidates`, {
        method: "POST",
        body: JSON.stringify({ candidate_id: candidateId }),
      }),
    removeCandidate: (collectionId: string, candidateId: string) =>
      fetchAPI<void>(`/api/collections/${collectionId}/candidates/${candidateId}`, { method: "DELETE" }),
  },
  handoffs: {
    inbox: () => fetchAPI<Handoff[]>("/api/handoffs/inbox"),
    outbox: () => fetchAPI<Handoff[]>("/api/handoffs/outbox"),
    create: (data: HandoffCreate) =>
      fetchAPI<Handoff>("/api/handoffs", { method: "POST", body: JSON.stringify(data) }),
    respond: (id: string, accept: boolean, notes?: string) =>
      fetchAPI<Handoff>(`/api/handoffs/${id}/respond`, {
        method: "POST",
        body: JSON.stringify({ accept, notes }),
      }),
  },
  quotes: {
    request: (data: QuoteRequest) =>
      fetchAPI<Quote>("/api/quotes", { method: "POST", body: JSON.stringify(data) }),
    list: () => fetchAPI<Quote[]>("/api/quotes"),
    get: (id: string) => fetchAPI<Quote>(`/api/quotes/${id}`),
  },
  copilot: {
    query: async (message: string) => {
      const token = await getAuthToken();
      return fetch(`${API_BASE}/api/copilot/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message }),
      }); // Returns stream, don't parse JSON
    },
  },
  signals: {
    recent: (limit?: number) => fetchAPI<Signal[]>(`/api/signals/recent?limit=${limit || 20}`),
  },
  admin: {
    stats: () => fetchAPI<Record<string, unknown>>("/api/admin/stats"),
    funnelData: () => fetchAPI<Record<string, unknown>>("/api/admin/funnel"),
    adapterHealth: () => fetchAPI<Record<string, unknown>[]>("/api/admin/adapters"),
  },
  users: {
    me: () => fetchAPI<User>("/api/users/me"),
  },
  health: () => fetchAPI<{ status: string }>("/api/health"),
};

export type ApiClient = typeof api;
```

### Mock Data (`lib/mock-data.ts`)

```typescript
import type {
  Candidate, CandidateAnonymized, Role, Match, Collection,
  Handoff, Quote, Signal, User, Organisation,
  ExtractedSkill, ExperienceEntry, RequiredSkill, SkillMatch, CandidateSource,
} from "@/contracts/canonical";

// ============================================================
// Helper: deterministic IDs
// ============================================================
const uuid = (n: number) => `00000000-0000-0000-0000-${String(n).padStart(12, "0")}`;

// ============================================================
// Users
// ============================================================
export const MOCK_USERS: User[] = [
  {
    id: uuid(1),
    email: "alex.morgan@mothership.demo",
    full_name: "Alex Morgan",
    role: "talent_partner",
    organisation_id: null,
    avatar_url: null,
    created_at: "2026-01-15T09:00:00Z",
  },
  {
    id: uuid(2),
    email: "jamie.chen@acmecorp.demo",
    full_name: "Jamie Chen",
    role: "client",
    organisation_id: uuid(100),
    avatar_url: null,
    created_at: "2026-02-01T09:00:00Z",
  },
  {
    id: uuid(3),
    email: "sam.patel@mothership.demo",
    full_name: "Sam Patel",
    role: "admin",
    organisation_id: null,
    avatar_url: null,
    created_at: "2026-01-10T09:00:00Z",
  },
];

// ============================================================
// Organisations
// ============================================================
export const MOCK_ORGANISATIONS: Organisation[] = [
  { id: uuid(100), name: "Acme Fintech", industry: "Fintech", website: "https://acmefintech.co.uk", location: "London" },
  { id: uuid(101), name: "HealthBridge", industry: "Healthtech", website: "https://healthbridge.io", location: "Manchester" },
  { id: uuid(102), name: "CloudScale Systems", industry: "SaaS", website: "https://cloudscale.dev", location: "Remote" },
];

// ============================================================
// Candidates (5)
// ============================================================
export const MOCK_CANDIDATES: Candidate[] = [
  {
    id: uuid(10),
    first_name: "Priya",
    last_name: "Sharma",
    email: "priya.sharma@gmail.com",
    phone: "+44 7700 900123",
    location: "London",
    linkedin_url: "https://linkedin.com/in/priyasharma",
    skills: [
      { name: "Python", years: 6, confidence: 0.95 },
      { name: "FastAPI", years: 3, confidence: 0.9 },
      { name: "PostgreSQL", years: 5, confidence: 0.88 },
      { name: "AWS", years: 4, confidence: 0.85 },
      { name: "Docker", years: 3, confidence: 0.9 },
      { name: "React", years: 2, confidence: 0.75 },
    ],
    experience: [
      { company: "Revolut", title: "Senior Backend Engineer", duration_months: 24, industry: "Fintech" },
      { company: "Monzo", title: "Backend Engineer", duration_months: 18, industry: "Fintech" },
      { company: "BBC", title: "Software Developer", duration_months: 30, industry: "Media" },
    ],
    seniority: "senior",
    salary_expectation: { min_amount: 85000, max_amount: 100000, currency: "GBP" },
    availability: "1_month",
    industries: ["Fintech", "Media"],
    cv_text: "Experienced backend engineer with 6 years of Python development...",
    profile_text: null,
    sources: [{ adapter_name: "bullhorn", external_id: "BH-4521", ingested_at: "2026-03-10T14:30:00Z" }],
    dedup_group: null,
    dedup_confidence: null,
    extraction_confidence: 0.92,
    extraction_flags: [],
    created_at: "2026-03-10T14:30:00Z",
    updated_at: "2026-03-10T14:30:00Z",
    created_by: uuid(1),
  },
  {
    id: uuid(11),
    first_name: "Marcus",
    last_name: "Williams",
    email: "marcus.w@protonmail.com",
    phone: "+44 7700 900456",
    location: "Manchester",
    linkedin_url: "https://linkedin.com/in/marcuswilliams",
    skills: [
      { name: "TypeScript", years: 5, confidence: 0.92 },
      { name: "React", years: 5, confidence: 0.95 },
      { name: "Next.js", years: 3, confidence: 0.88 },
      { name: "Node.js", years: 4, confidence: 0.9 },
      { name: "GraphQL", years: 2, confidence: 0.8 },
      { name: "Tailwind CSS", years: 2, confidence: 0.85 },
    ],
    experience: [
      { company: "Booking.com", title: "Senior Frontend Engineer", duration_months: 30, industry: "Travel" },
      { company: "THG", title: "Frontend Developer", duration_months: 24, industry: "E-commerce" },
    ],
    seniority: "senior",
    salary_expectation: { min_amount: 75000, max_amount: 90000, currency: "GBP" },
    availability: "immediate",
    industries: ["Travel", "E-commerce"],
    cv_text: "Senior frontend engineer specialising in React and TypeScript...",
    profile_text: null,
    sources: [{ adapter_name: "linkedin", external_id: "LI-8832", ingested_at: "2026-03-12T10:00:00Z" }],
    dedup_group: null,
    dedup_confidence: null,
    extraction_confidence: 0.89,
    extraction_flags: ["salary_expectation"],
    created_at: "2026-03-12T10:00:00Z",
    updated_at: "2026-03-12T10:00:00Z",
    created_by: uuid(1),
  },
  {
    id: uuid(12),
    first_name: "Elena",
    last_name: "Kovac",
    email: "elena.kovac@outlook.com",
    phone: "+44 7700 900789",
    location: "London",
    linkedin_url: "https://linkedin.com/in/elenakovac",
    skills: [
      { name: "Python", years: 8, confidence: 0.95 },
      { name: "Machine Learning", years: 5, confidence: 0.9 },
      { name: "TensorFlow", years: 4, confidence: 0.88 },
      { name: "SQL", years: 7, confidence: 0.92 },
      { name: "Spark", years: 3, confidence: 0.85 },
      { name: "Airflow", years: 2, confidence: 0.78 },
    ],
    experience: [
      { company: "DeepMind", title: "ML Engineer", duration_months: 36, industry: "AI" },
      { company: "Ocado Technology", title: "Data Scientist", duration_months: 24, industry: "E-commerce" },
    ],
    seniority: "lead",
    salary_expectation: { min_amount: 110000, max_amount: 130000, currency: "GBP" },
    availability: "3_months",
    industries: ["AI", "E-commerce"],
    cv_text: "Lead ML engineer with experience at DeepMind and Ocado...",
    profile_text: null,
    sources: [{ adapter_name: "hubspot", external_id: "HS-2211", ingested_at: "2026-03-08T16:00:00Z" }],
    dedup_group: null,
    dedup_confidence: null,
    extraction_confidence: 0.94,
    extraction_flags: [],
    created_at: "2026-03-08T16:00:00Z",
    updated_at: "2026-03-08T16:00:00Z",
    created_by: uuid(1),
  },
  {
    id: uuid(13),
    first_name: "Tom",
    last_name: "Bradley",
    email: "tom.bradley@gmail.com",
    phone: "+44 7700 900321",
    location: "Bristol",
    linkedin_url: "https://linkedin.com/in/tombradley",
    skills: [
      { name: "Python", years: 3, confidence: 0.9 },
      { name: "Django", years: 2, confidence: 0.85 },
      { name: "JavaScript", years: 3, confidence: 0.88 },
      { name: "PostgreSQL", years: 2, confidence: 0.82 },
      { name: "Docker", years: 1, confidence: 0.7 },
    ],
    experience: [
      { company: "Just Eat", title: "Software Engineer", duration_months: 18, industry: "Food Tech" },
      { company: "Graduate scheme", title: "Junior Developer", duration_months: 12, industry: "Consulting" },
    ],
    seniority: "mid",
    salary_expectation: { min_amount: 50000, max_amount: 60000, currency: "GBP" },
    availability: "immediate",
    industries: ["Food Tech", "Consulting"],
    cv_text: "Mid-level developer with full-stack experience...",
    profile_text: null,
    sources: [{ adapter_name: "bullhorn", external_id: "BH-6634", ingested_at: "2026-03-15T11:00:00Z" }],
    dedup_group: null,
    dedup_confidence: null,
    extraction_confidence: 0.86,
    extraction_flags: ["seniority"],
    created_at: "2026-03-15T11:00:00Z",
    updated_at: "2026-03-15T11:00:00Z",
    created_by: uuid(1),
  },
  {
    id: uuid(14),
    first_name: "Aisha",
    last_name: "Okafor",
    email: "aisha.okafor@gmail.com",
    phone: "+44 7700 900654",
    location: "London",
    linkedin_url: "https://linkedin.com/in/aishaokafor",
    skills: [
      { name: "Python", years: 5, confidence: 0.92 },
      { name: "FastAPI", years: 2, confidence: 0.85 },
      { name: "Kubernetes", years: 3, confidence: 0.88 },
      { name: "Terraform", years: 3, confidence: 0.9 },
      { name: "AWS", years: 4, confidence: 0.92 },
      { name: "Go", years: 2, confidence: 0.75 },
    ],
    experience: [
      { company: "Deliveroo", title: "Platform Engineer", duration_months: 24, industry: "Food Tech" },
      { company: "Sky", title: "DevOps Engineer", duration_months: 30, industry: "Media" },
    ],
    seniority: "senior",
    salary_expectation: { min_amount: 90000, max_amount: 105000, currency: "GBP" },
    availability: "1_month",
    industries: ["Food Tech", "Media"],
    cv_text: "Platform engineer with deep AWS and Kubernetes experience...",
    profile_text: null,
    sources: [
      { adapter_name: "linkedin", external_id: "LI-9912", ingested_at: "2026-03-14T09:00:00Z" },
      { adapter_name: "bullhorn", external_id: "BH-7745", ingested_at: "2026-03-11T13:00:00Z" },
    ],
    dedup_group: "dedup-group-1",
    dedup_confidence: 0.95,
    extraction_confidence: 0.91,
    extraction_flags: [],
    created_at: "2026-03-11T13:00:00Z",
    updated_at: "2026-03-14T09:00:00Z",
    created_by: uuid(1),
  },
];

// ============================================================
// Roles (3)
// ============================================================
export const MOCK_ROLES: Role[] = [
  {
    id: uuid(20),
    title: "Senior Backend Engineer",
    description: "We are looking for a Senior Backend Engineer to join our payments team. You will design and build high-throughput APIs processing millions of transactions. Experience with Python, FastAPI or Django, PostgreSQL, and AWS required. Fintech experience preferred.",
    organisation_id: uuid(100),
    required_skills: [
      { name: "Python", min_years: 4, importance: "required" },
      { name: "PostgreSQL", min_years: 3, importance: "required" },
      { name: "AWS", min_years: 2, importance: "required" },
    ],
    preferred_skills: [
      { name: "FastAPI", min_years: 1, importance: "preferred" },
      { name: "Docker", min_years: 1, importance: "preferred" },
      { name: "Fintech experience", min_years: null, importance: "preferred" },
    ],
    seniority: "senior",
    salary_band: { min_amount: 80000, max_amount: 100000, currency: "GBP" },
    location: "London",
    remote_policy: "hybrid",
    industry: "Fintech",
    extraction_confidence: 0.93,
    status: "active",
    created_at: "2026-03-18T10:00:00Z",
    created_by: uuid(2),
  },
  {
    id: uuid(21),
    title: "Senior Frontend Engineer",
    description: "Join our product team to build the next generation of our health records platform. We need a Senior Frontend Engineer with strong React/TypeScript skills. Experience with Next.js, design systems, and accessibility is highly valued. Healthtech background a plus.",
    organisation_id: uuid(101),
    required_skills: [
      { name: "React", min_years: 4, importance: "required" },
      { name: "TypeScript", min_years: 3, importance: "required" },
    ],
    preferred_skills: [
      { name: "Next.js", min_years: 1, importance: "preferred" },
      { name: "Tailwind CSS", min_years: 1, importance: "preferred" },
      { name: "Accessibility (a11y)", min_years: null, importance: "preferred" },
    ],
    seniority: "senior",
    salary_band: { min_amount: 70000, max_amount: 90000, currency: "GBP" },
    location: "Manchester",
    remote_policy: "remote",
    industry: "Healthtech",
    extraction_confidence: 0.91,
    status: "active",
    created_at: "2026-03-19T14:00:00Z",
    created_by: uuid(2),
  },
  {
    id: uuid(22),
    title: "ML Engineer",
    description: "We are hiring an ML Engineer to work on our recommendation engine. You will design, train, and deploy machine learning models at scale. Deep experience with Python, TensorFlow/PyTorch, and cloud ML services required. Must be comfortable with data pipelines (Spark, Airflow).",
    organisation_id: uuid(102),
    required_skills: [
      { name: "Python", min_years: 5, importance: "required" },
      { name: "Machine Learning", min_years: 3, importance: "required" },
      { name: "TensorFlow", min_years: 2, importance: "required" },
    ],
    preferred_skills: [
      { name: "Spark", min_years: 1, importance: "preferred" },
      { name: "Airflow", min_years: 1, importance: "preferred" },
      { name: "Kubernetes", min_years: null, importance: "preferred" },
    ],
    seniority: "lead",
    salary_band: { min_amount: 100000, max_amount: 130000, currency: "GBP" },
    location: "London",
    remote_policy: "hybrid",
    industry: "SaaS",
    extraction_confidence: 0.95,
    status: "active",
    created_at: "2026-03-20T09:00:00Z",
    created_by: uuid(2),
  },
];

// ============================================================
// Matches
// ============================================================
export const MOCK_MATCHES: Match[] = [
  // Priya -> Senior Backend Engineer (strong)
  {
    id: uuid(30),
    candidate_id: uuid(10),
    role_id: uuid(20),
    overall_score: 0.88,
    structured_score: 0.91,
    semantic_score: 0.85,
    skill_overlap: [
      { skill_name: "Python", status: "matched", candidate_years: 6, required_years: 4 },
      { skill_name: "PostgreSQL", status: "matched", candidate_years: 5, required_years: 3 },
      { skill_name: "AWS", status: "matched", candidate_years: 4, required_years: 2 },
      { skill_name: "FastAPI", status: "matched", candidate_years: 3, required_years: 1 },
      { skill_name: "Docker", status: "matched", candidate_years: 3, required_years: 1 },
      { skill_name: "Fintech experience", status: "matched", candidate_years: null, required_years: null },
    ],
    confidence: "strong",
    explanation: "Priya is an excellent fit for this role. She has 6 years of Python experience and has worked extensively with FastAPI and PostgreSQL in fintech environments at Revolut and Monzo. Her AWS and Docker skills exceed the requirements.",
    strengths: [
      "6 years of Python exceeds the 4-year requirement",
      "Direct FastAPI production experience at Revolut",
      "Strong fintech background with payments exposure",
      "All required and preferred skills matched",
    ],
    gaps: [
      "Currently on a 1-month notice period",
    ],
    recommendation: "Strong match — schedule an introduction promptly.",
    scoring_breakdown: { skill_weight: 0.4, semantic_weight: 0.35, experience_weight: 0.25 },
    model_version: "gpt-4o-2026-03",
    created_at: "2026-03-20T12:00:00Z",
    status: "generated",
  },
  // Aisha -> Senior Backend Engineer (good)
  {
    id: uuid(31),
    candidate_id: uuid(14),
    role_id: uuid(20),
    overall_score: 0.72,
    structured_score: 0.68,
    semantic_score: 0.76,
    skill_overlap: [
      { skill_name: "Python", status: "matched", candidate_years: 5, required_years: 4 },
      { skill_name: "PostgreSQL", status: "missing", candidate_years: null, required_years: 3 },
      { skill_name: "AWS", status: "matched", candidate_years: 4, required_years: 2 },
      { skill_name: "FastAPI", status: "matched", candidate_years: 2, required_years: 1 },
      { skill_name: "Docker", status: "partial", candidate_years: null, required_years: 1 },
      { skill_name: "Fintech experience", status: "missing", candidate_years: null, required_years: null },
    ],
    confidence: "good",
    explanation: "Aisha has strong Python and AWS experience from platform engineering roles. While she lacks direct PostgreSQL and fintech experience, her infrastructure expertise and FastAPI skills make her a solid candidate who could ramp up quickly.",
    strengths: [
      "5 years of Python with production API experience",
      "Strong AWS and infrastructure skills",
      "Platform engineering background valuable for high-throughput systems",
    ],
    gaps: [
      "No listed PostgreSQL experience",
      "No fintech industry background",
      "Docker experience not explicitly listed (but likely from Kubernetes work)",
    ],
    recommendation: "Good match — worth an introduction, especially if infrastructure depth is valued.",
    scoring_breakdown: { skill_weight: 0.4, semantic_weight: 0.35, experience_weight: 0.25 },
    model_version: "gpt-4o-2026-03",
    created_at: "2026-03-20T12:00:00Z",
    status: "generated",
  },
  // Tom -> Senior Backend Engineer (possible)
  {
    id: uuid(32),
    candidate_id: uuid(13),
    role_id: uuid(20),
    overall_score: 0.45,
    structured_score: 0.4,
    semantic_score: 0.5,
    skill_overlap: [
      { skill_name: "Python", status: "partial", candidate_years: 3, required_years: 4 },
      { skill_name: "PostgreSQL", status: "partial", candidate_years: 2, required_years: 3 },
      { skill_name: "AWS", status: "missing", candidate_years: null, required_years: 2 },
      { skill_name: "FastAPI", status: "missing", candidate_years: null, required_years: 1 },
      { skill_name: "Docker", status: "partial", candidate_years: 1, required_years: 1 },
    ],
    confidence: "possible",
    explanation: "Tom has relevant Python and PostgreSQL experience but falls short of the seniority level required. At mid-level with 3 years of Python, he is still growing into the senior space. Could be worth considering if the team is open to a strong mid-level hire.",
    strengths: [
      "Available immediately",
      "Python and PostgreSQL foundations in place",
      "Lower salary expectations could fit budget",
    ],
    gaps: [
      "3 years Python vs 4 required — slightly under",
      "No AWS or FastAPI experience listed",
      "Mid-level seniority, role requires senior",
    ],
    recommendation: "Possible fit if the team would consider a strong mid-level candidate at a lower cost.",
    scoring_breakdown: { skill_weight: 0.4, semantic_weight: 0.35, experience_weight: 0.25 },
    model_version: "gpt-4o-2026-03",
    created_at: "2026-03-20T12:00:00Z",
    status: "generated",
  },
  // Marcus -> Senior Frontend Engineer (strong)
  {
    id: uuid(33),
    candidate_id: uuid(11),
    role_id: uuid(21),
    overall_score: 0.92,
    structured_score: 0.95,
    semantic_score: 0.89,
    skill_overlap: [
      { skill_name: "React", status: "matched", candidate_years: 5, required_years: 4 },
      { skill_name: "TypeScript", status: "matched", candidate_years: 5, required_years: 3 },
      { skill_name: "Next.js", status: "matched", candidate_years: 3, required_years: 1 },
      { skill_name: "Tailwind CSS", status: "matched", candidate_years: 2, required_years: 1 },
    ],
    confidence: "strong",
    explanation: "Marcus is an outstanding match. His 5 years of React and TypeScript experience, combined with deep Next.js and Tailwind CSS skills, align perfectly with the role. His experience building UI at Booking.com demonstrates large-scale frontend expertise.",
    strengths: [
      "5 years React and TypeScript — exceeds requirements",
      "3 years Next.js — strong match",
      "Large-scale frontend experience at Booking.com",
      "Available immediately",
    ],
    gaps: [],
    recommendation: "Excellent match — prioritise this introduction.",
    scoring_breakdown: { skill_weight: 0.4, semantic_weight: 0.35, experience_weight: 0.25 },
    model_version: "gpt-4o-2026-03",
    created_at: "2026-03-20T12:00:00Z",
    status: "generated",
  },
  // Elena -> ML Engineer (strong)
  {
    id: uuid(34),
    candidate_id: uuid(12),
    role_id: uuid(22),
    overall_score: 0.9,
    structured_score: 0.92,
    semantic_score: 0.88,
    skill_overlap: [
      { skill_name: "Python", status: "matched", candidate_years: 8, required_years: 5 },
      { skill_name: "Machine Learning", status: "matched", candidate_years: 5, required_years: 3 },
      { skill_name: "TensorFlow", status: "matched", candidate_years: 4, required_years: 2 },
      { skill_name: "Spark", status: "matched", candidate_years: 3, required_years: 1 },
      { skill_name: "Airflow", status: "matched", candidate_years: 2, required_years: 1 },
    ],
    confidence: "strong",
    explanation: "Elena is a top-tier match with 8 years of Python and 5 years of ML experience from DeepMind. Her Spark and Airflow skills cover the data pipeline requirements. She brings world-class ML expertise to the recommendation engine.",
    strengths: [
      "8 years Python — well above requirement",
      "DeepMind ML experience — elite pedigree",
      "Full data pipeline skills (Spark + Airflow)",
      "Lead-level seniority matches role",
    ],
    gaps: [
      "3-month notice period",
      "Salary expectations at top of band (110-130k)",
    ],
    recommendation: "Exceptional match — the notice period is the only consideration.",
    scoring_breakdown: { skill_weight: 0.4, semantic_weight: 0.35, experience_weight: 0.25 },
    model_version: "gpt-4o-2026-03",
    created_at: "2026-03-20T12:00:00Z",
    status: "generated",
  },
];

// ============================================================
// Collections
// ============================================================
export const MOCK_COLLECTIONS: Collection[] = [
  {
    id: uuid(40),
    name: "Senior Backend — London",
    description: "Strong backend candidates based in London for fintech roles",
    owner_id: uuid(1),
    visibility: "shared_all",
    shared_with: null,
    candidate_ids: [uuid(10), uuid(14)],
    tags: ["backend", "london", "senior"],
    candidate_count: 2,
    avg_match_score: 0.8,
    available_now_count: 0,
    created_at: "2026-03-15T10:00:00Z",
    updated_at: "2026-03-20T12:00:00Z",
  },
  {
    id: uuid(41),
    name: "ML Engineers — Remote OK",
    description: "ML and data science talent open to remote positions",
    owner_id: uuid(1),
    visibility: "private",
    shared_with: null,
    candidate_ids: [uuid(12)],
    tags: ["ml", "data-science", "remote"],
    candidate_count: 1,
    avg_match_score: 0.9,
    available_now_count: 0,
    created_at: "2026-03-16T11:00:00Z",
    updated_at: "2026-03-20T12:00:00Z",
  },
  {
    id: uuid(42),
    name: "Immediate Availability",
    description: "Candidates available to start right away",
    owner_id: uuid(1),
    visibility: "shared_all",
    shared_with: null,
    candidate_ids: [uuid(11), uuid(13)],
    tags: ["immediate", "available-now"],
    candidate_count: 2,
    avg_match_score: null,
    available_now_count: 2,
    created_at: "2026-03-17T09:00:00Z",
    updated_at: "2026-03-20T12:00:00Z",
  },
];

// ============================================================
// Anonymized candidates helper
// ============================================================
export function anonymizeCandidate(c: Candidate): CandidateAnonymized {
  return {
    id: c.id,
    first_name: c.first_name,
    last_initial: c.last_name.charAt(0),
    location: c.location,
    skills: c.skills,
    seniority: c.seniority,
    availability: c.availability,
    industries: c.industries,
    experience_years: c.experience.reduce((sum, e) => sum + (e.duration_months ?? 0), 0) / 12,
    is_pool_candidate: c.sources.length > 1 || (c.dedup_group !== null),
  };
}

// ============================================================
// Lookup helpers
// ============================================================
export function getCandidateById(id: string): Candidate | undefined {
  return MOCK_CANDIDATES.find((c) => c.id === id);
}

export function getRoleById(id: string): Role | undefined {
  return MOCK_ROLES.find((r) => r.id === id);
}

export function getMatchesForRole(roleId: string): Match[] {
  return MOCK_MATCHES.filter((m) => m.role_id === roleId);
}

export function getMatchesForCandidate(candidateId: string): Match[] {
  return MOCK_MATCHES.filter((m) => m.candidate_id === candidateId);
}
```

### Mock API (`lib/api-mock.ts`)

```typescript
import type { ApiClient } from "./api";
import {
  MOCK_CANDIDATES,
  MOCK_ROLES,
  MOCK_MATCHES,
  MOCK_COLLECTIONS,
  MOCK_USERS,
  anonymizeCandidate,
  getCandidateById,
} from "./mock-data";
import type { Candidate, Role, Match, Collection, Handoff, Quote, Signal } from "@/contracts/canonical";

// Simulate network delay
const delay = (ms = 300) => new Promise((resolve) => setTimeout(resolve, ms + Math.random() * 200));

export const mockApi: ApiClient = {
  candidates: {
    list: async () => { await delay(); return [...MOCK_CANDIDATES]; },
    get: async (id) => {
      await delay();
      const c = MOCK_CANDIDATES.find((c) => c.id === id);
      if (!c) throw new Error("Candidate not found");
      return c;
    },
    create: async (data) => {
      await delay(500);
      const newCandidate: Candidate = {
        id: crypto.randomUUID(),
        ...data,
        email: data.email ?? null,
        phone: data.phone ?? null,
        location: data.location ?? null,
        linkedin_url: data.linkedin_url ?? null,
        cv_text: data.cv_text ?? null,
        profile_text: data.profile_text ?? null,
        skills: [],
        experience: [],
        seniority: null,
        salary_expectation: null,
        availability: null,
        industries: [],
        sources: [],
        dedup_group: null,
        dedup_confidence: null,
        extraction_confidence: 0,
        extraction_flags: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        created_by: MOCK_USERS[0].id,
      };
      return newCandidate;
    },
    update: async (id, data) => {
      await delay();
      const c = MOCK_CANDIDATES.find((c) => c.id === id);
      if (!c) throw new Error("Candidate not found");
      return { ...c, ...data, updated_at: new Date().toISOString() } as Candidate;
    },
    search: async (query) => {
      await delay();
      const q = query.toLowerCase();
      return MOCK_CANDIDATES.filter(
        (c) =>
          c.first_name.toLowerCase().includes(q) ||
          c.last_name.toLowerCase().includes(q) ||
          c.skills.some((s) => s.name.toLowerCase().includes(q)) ||
          c.location?.toLowerCase().includes(q)
      );
    },
    uploadCV: async (_file) => {
      await delay(1500); // Simulate extraction time
      return MOCK_CANDIDATES[0]; // Return first mock candidate as if just extracted
    },
    extractFromText: async (_text) => {
      await delay(1500);
      return MOCK_CANDIDATES[0];
    },
  },
  roles: {
    list: async () => { await delay(); return [...MOCK_ROLES]; },
    get: async (id) => {
      await delay();
      const r = MOCK_ROLES.find((r) => r.id === id);
      if (!r) throw new Error("Role not found");
      return r;
    },
    create: async (data) => {
      await delay(500);
      const newRole: Role = {
        id: crypto.randomUUID(),
        ...data,
        required_skills: [],
        preferred_skills: [],
        seniority: null,
        salary_band: data.salary_band ?? null,
        location: data.location ?? null,
        remote_policy: data.remote_policy ?? "hybrid",
        industry: null,
        extraction_confidence: null,
        status: "draft",
        created_at: new Date().toISOString(),
        created_by: MOCK_USERS[1].id,
      };
      return newRole;
    },
    update: async (id, data) => {
      await delay();
      const r = MOCK_ROLES.find((r) => r.id === id);
      if (!r) throw new Error("Role not found");
      return { ...r, ...data } as Role;
    },
    extractRequirements: async (_description) => {
      await delay(1000);
      return {
        required_skills: MOCK_ROLES[0].required_skills,
        preferred_skills: MOCK_ROLES[0].preferred_skills,
        seniority: MOCK_ROLES[0].seniority,
      };
    },
  },
  matches: {
    forRole: async (roleId) => {
      await delay();
      return MOCK_MATCHES.filter((m) => m.role_id === roleId);
    },
    forCandidate: async (candidateId) => {
      await delay();
      return MOCK_MATCHES.filter((m) => m.candidate_id === candidateId);
    },
    updateStatus: async (matchId, status, _reason) => {
      await delay();
      const m = MOCK_MATCHES.find((m) => m.id === matchId);
      if (!m) throw new Error("Match not found");
      return { ...m, status };
    },
    forRoleAnonymized: async (roleId) => {
      await delay();
      const matches = MOCK_MATCHES.filter((m) => m.role_id === roleId);
      return matches.map((match) => {
        const candidate = getCandidateById(match.candidate_id);
        return {
          match,
          candidate: candidate ? anonymizeCandidate(candidate) : anonymizeCandidate(MOCK_CANDIDATES[0]),
        };
      });
    },
  },
  collections: {
    list: async () => { await delay(); return [...MOCK_COLLECTIONS]; },
    get: async (id) => {
      await delay();
      const c = MOCK_COLLECTIONS.find((c) => c.id === id);
      if (!c) throw new Error("Collection not found");
      return c;
    },
    create: async (data) => {
      await delay();
      return {
        id: crypto.randomUUID(),
        name: data.name,
        description: data.description ?? null,
        owner_id: MOCK_USERS[0].id,
        visibility: data.visibility ?? "private",
        shared_with: data.shared_with ?? null,
        candidate_ids: [],
        tags: data.tags ?? [],
        candidate_count: 0,
        avg_match_score: null,
        available_now_count: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as Collection;
    },
    addCandidate: async (collectionId, _candidateId) => {
      await delay();
      const c = MOCK_COLLECTIONS.find((c) => c.id === collectionId);
      if (!c) throw new Error("Collection not found");
      return c;
    },
    removeCandidate: async () => { await delay(); },
  },
  handoffs: {
    inbox: async () => { await delay(); return []; },
    outbox: async () => { await delay(); return []; },
    create: async (data) => {
      await delay();
      return {
        id: crypto.randomUUID(),
        from_partner_id: MOCK_USERS[0].id,
        to_partner_id: data.to_partner_id,
        candidate_ids: data.candidate_ids,
        context_notes: data.context_notes,
        target_role_id: data.target_role_id ?? null,
        status: "pending",
        response_notes: null,
        attribution_id: crypto.randomUUID(),
        created_at: new Date().toISOString(),
        responded_at: null,
      } as Handoff;
    },
    respond: async (id, accept, notes) => {
      await delay();
      return {
        id,
        from_partner_id: MOCK_USERS[0].id,
        to_partner_id: MOCK_USERS[0].id,
        candidate_ids: [],
        context_notes: "",
        target_role_id: null,
        status: accept ? "accepted" : "declined",
        response_notes: notes ?? null,
        attribution_id: crypto.randomUUID(),
        created_at: new Date().toISOString(),
        responded_at: new Date().toISOString(),
      } as Handoff;
    },
  },
  quotes: {
    request: async (data) => {
      await delay();
      const isPool = MOCK_CANDIDATES.find((c) => c.id === data.candidate_id)?.sources.length ?? 0 > 1;
      return {
        id: crypto.randomUUID(),
        client_id: MOCK_USERS[1].id,
        candidate_id: data.candidate_id,
        role_id: data.role_id,
        is_pool_candidate: isPool,
        base_fee: 15000,
        pool_discount: isPool ? 3000 : null,
        final_fee: isPool ? 12000 : 15000,
        fee_breakdown: {
          calculation: "15% of estimated first-year salary",
          base: "15,000",
          discount: isPool ? "Pre-vetted talent network discount: -3,000" : null,
        },
        status: "generated",
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
      } as Quote;
    },
    list: async () => { await delay(); return []; },
    get: async (_id) => { await delay(); throw new Error("Quote not found"); },
  },
  copilot: {
    query: async (_message) => {
      return new Response(
        JSON.stringify({ response: "Mock copilot response. The real copilot will stream results." }),
        { headers: { "Content-Type": "application/json" } }
      );
    },
  },
  signals: {
    recent: async (_limit) => { await delay(); return []; },
  },
  admin: {
    stats: async () => {
      await delay();
      return {
        total_candidates: MOCK_CANDIDATES.length,
        active_roles: MOCK_ROLES.filter((r) => r.status === "active").length,
        total_matches: MOCK_MATCHES.length,
        placements_this_quarter: 3,
        revenue_pipeline: 45000,
      };
    },
    funnelData: async () => {
      await delay();
      return {
        stages: [
          { name: "Ingested", count: 52 },
          { name: "Deduplicated", count: 48 },
          { name: "Enriched", count: 45 },
          { name: "Matched", count: 38 },
          { name: "Shortlisted", count: 15 },
          { name: "Intro Requested", count: 8 },
          { name: "Placed", count: 3 },
        ],
      };
    },
    adapterHealth: async () => {
      await delay();
      return [
        { name: "Bullhorn", status: "healthy", last_sync: "2026-03-24T08:00:00Z", records_synced: 312, error_rate: 0.01 },
        { name: "HubSpot", status: "healthy", last_sync: "2026-03-24T07:30:00Z", records_synced: 189, error_rate: 0.02 },
        { name: "LinkedIn", status: "degraded", last_sync: "2026-03-23T22:00:00Z", records_synced: 95, error_rate: 0.08 },
      ];
    },
  },
  users: {
    me: async () => { await delay(); return MOCK_USERS[0]; },
  },
  health: async () => { await delay(); return { status: "ok" }; },
};
```

### Unified Export (`lib/api-client.ts`)

```typescript
import { api } from "./api";
import { mockApi } from "./api-mock";
import type { ApiClient } from "./api";

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

export const apiClient: ApiClient = USE_MOCKS ? mockApi : api;
```

### Environment Variable (`.env.local.example`)

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here

# Toggle mock data (set to "true" when backend is unavailable)
NEXT_PUBLIC_USE_MOCKS=true
```

## Outputs
- `lib/api.ts` — enhanced API client with auth injection, ApiError class, retry logic
- `lib/mock-data.ts` — 5 candidates, 3 roles, 5 matches, 3 collections with realistic UK market data
- `lib/api-mock.ts` — full mock implementation of ApiClient interface
- `lib/api-client.ts` — unified export switching real/mock via env var
- `.env.local.example` — documented environment variables

## Acceptance Criteria
1. `npm run build` passes with no errors
2. `apiClient` is a drop-in replacement — same interface whether using real or mock API
3. Mock candidates have realistic UK names, locations, skills, and experience entries
4. Mock matches include proper skill overlap data with all three statuses (matched/partial/missing)
5. Mock data conforms exactly to canonical TypeScript types — no type errors
6. Setting `NEXT_PUBLIC_USE_MOCKS=true` routes all API calls through mock layer
7. Setting `NEXT_PUBLIC_USE_MOCKS=false` (or unset) routes through real API with auth token injection
8. API errors are instances of `ApiError` with status, statusText, and body
9. Retry logic retries on 5xx and network errors but not on 4xx (except 429)
10. `anonymizeCandidate()` correctly strips last name, company names, and computes experience years

## Handoff Notes
- **To all subsequent tasks:** Import `apiClient` from `@/lib/api-client` instead of `@/lib/api`. This ensures mock data is used during development.
- **To Agent A:** The frontend expects these endpoint paths — see the `api` object in `lib/api.ts` for the full list. Key additions beyond Task 01: `PATCH /api/candidates/:id`, `POST /api/candidates/upload`, `POST /api/candidates/extract`, `POST /api/roles/extract-requirements`, `PATCH /api/matches/:id/status`, `GET /api/matches/role/:id/anonymized`, `GET /api/users/me`.
- **Decision:** Mock data uses deterministic UUIDs (`00000000-0000-0000-0000-000000000010` etc.) for easy debugging. Network delay is randomized (300-500ms) to simulate realistic API latency. The `anonymizeCandidate` helper lives in mock-data but is also used by the mock API for the anonymized match endpoint.
