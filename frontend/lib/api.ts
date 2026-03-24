import { createClient } from "@/lib/supabase";
import type {
  Candidate, CandidateCreate, CandidateAnonymized,
  Role, RoleCreate,
  Match,
  Collection, CollectionCreate,
  Handoff, HandoffCreate,
  Quote, QuoteRequest, QuoteStatus,
  Signal,
  User,
} from "@/contracts/canonical";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1000;

// ---- Paginated response shape matching backend PaginatedResponse ----

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

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

  // Build headers: omit Content-Type when body is FormData so browser sets boundary
  const isFormData = options?.body instanceof FormData;
  const baseHeaders: Record<string, string> = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options?.headers as Record<string, string> ?? {}),
  };

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: baseHeaders,
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

/**
 * Unwrap a paginated response, returning just the data array.
 * Callers that need pagination metadata can use fetchAPI<PaginatedResponse<T>> directly.
 */
async function fetchPaginated<T>(path: string): Promise<T[]> {
  const response = await fetchAPI<PaginatedResponse<T>>(path);
  return response.data;
}

export const api = {
  candidates: {
    // Backend returns PaginatedResponse — unwrap to T[]
    list: () => fetchPaginated<Candidate>("/api/candidates"),
    get: (id: string) => fetchAPI<Candidate>(`/api/candidates/${id}`),
    create: (data: CandidateCreate) =>
      fetchAPI<Candidate>("/api/candidates", { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: Partial<CandidateCreate>) =>
      fetchAPI<Candidate>(`/api/candidates/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    // Backend returns PaginatedResponse for search too
    search: (query: string) => fetchPaginated<Candidate>(`/api/candidates/search?q=${encodeURIComponent(query)}`),
    uploadCV: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      // Don't pass Content-Type — let browser set multipart boundary
      return fetchAPI<Candidate>("/api/candidates/upload", {
        method: "POST",
        body: formData,
      });
    },
    extractFromText: (text: string) =>
      fetchAPI<Candidate>("/api/candidates/extract", { method: "POST", body: JSON.stringify({ text }) }),
  },
  roles: {
    // Backend returns PaginatedResponse
    list: () => fetchPaginated<Role>("/api/roles"),
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
      fetchAPI<{ status: string; match_id: string; new_status: string }>(`/api/matches/${matchId}/status`, {
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
    // Backend: PATCH /api/quotes/{id}/status with query param ?status=accepted
    updateStatus: (quoteId: string, status: QuoteStatus) =>
      fetchAPI<Quote>(`/api/quotes/${quoteId}/status?status=${status}`, {
        method: "PATCH",
      }),
  },
  copilot: {
    // Non-streaming: backend expects { query }, not { message }
    query: async (message: string) => {
      const token = await getAuthToken();
      return fetch(`${API_BASE}/api/copilot/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ query: message }),
      });
    },
    // SSE streaming endpoint (separate from /query)
    stream: async (message: string, sessionId?: string) => {
      const token = await getAuthToken();
      return fetch(`${API_BASE}/api/copilot/query/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ query: message, session_id: sessionId }),
      });
    },
  },
  signals: {
    recent: (limit?: number) => fetchAPI<Signal[]>(`/api/signals/recent?limit=${limit || 20}`),
  },
  admin: {
    stats: () => fetchAPI<Record<string, unknown>>("/api/admin/stats"),
    // Backend endpoint is /api/admin/pipeline/status, not /funnel
    pipelineStatus: () => fetchAPI<Record<string, unknown>>("/api/admin/pipeline/status"),
    // Backend endpoint is /api/admin/adapters/health, not /adapters
    adapterHealth: () => fetchAPI<Record<string, unknown>[]>("/api/admin/adapters/health"),
    // User management
    users: () => fetchAPI<User[]>("/api/admin/users"),
  },
  users: {
    me: () => fetchAPI<User>("/api/users/me"),
  },
  health: () => fetchAPI<{ status: string }>("/health"),
};

export type ApiClient = typeof api;
