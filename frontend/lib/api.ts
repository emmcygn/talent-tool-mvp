import type {
  Candidate, CandidateCreate,
  Role, RoleCreate,
  Match,
  Collection, CollectionCreate,
  Handoff, HandoffCreate,
  Quote, QuoteRequest,
  Signal,
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

export const api = {
  candidates: {
    list: () => fetchAPI<Candidate[]>("/api/candidates"),
    get: (id: string) => fetchAPI<Candidate>(`/api/candidates/${id}`),
    create: (data: CandidateCreate) =>
      fetchAPI<Candidate>("/api/candidates", { method: "POST", body: JSON.stringify(data) }),
    search: (query: string) => fetchAPI<Candidate[]>(`/api/candidates/search?q=${encodeURIComponent(query)}`),
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
      }),
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

