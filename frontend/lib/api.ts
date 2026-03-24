import { createClient } from "@/lib/supabase";
import type {
  Candidate, CandidateCreate, CandidateAnonymized,
  Role, RoleCreate,
  Match,
  Collection, CollectionCreate,
  Handoff, HandoffCreate,
  Quote, QuoteRequest,
  Signal,
  User,
} from "@/contracts/canonical";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1000;

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

      if (res.status === 204) return undefined as T;

      return await res.json();
    } catch (err) {
      lastError = err as Error;

      if (err instanceof ApiError && err.status >= 400 && err.status < 500 && err.status !== 429) {
        throw err;
      }

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
        headers: {},
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
      });
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
