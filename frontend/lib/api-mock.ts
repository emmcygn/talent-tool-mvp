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
import type { Candidate, Role, Collection, Handoff, Quote } from "@/contracts/canonical";

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
      return {
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
        embedding: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        created_by: MOCK_USERS[0].id,
      } as Candidate;
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
    uploadCV: async () => {
      await delay(1500);
      return MOCK_CANDIDATES[0];
    },
    extractFromText: async () => {
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
      return {
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
        embedding: null,
        status: "draft",
        created_at: new Date().toISOString(),
        created_by: MOCK_USERS[1].id,
      } as Role;
    },
    update: async (id, data) => {
      await delay();
      const r = MOCK_ROLES.find((r) => r.id === id);
      if (!r) throw new Error("Role not found");
      return { ...r, ...data } as Role;
    },
    extractRequirements: async () => {
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
    updateStatus: async (matchId, status) => {
      await delay();
      const m = MOCK_MATCHES.find((m) => m.id === matchId);
      if (!m) throw new Error("Match not found");
      return { status: "updated", match_id: matchId, new_status: status };
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
    addCandidate: async (collectionId) => {
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
      const isPool = (MOCK_CANDIDATES.find((c) => c.id === data.candidate_id)?.sources.length ?? 0) > 1;
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
    get: async () => { await delay(); throw new Error("Quote not found"); },
    updateStatus: async (quoteId, status) => {
      await delay();
      return {
        id: quoteId,
        client_id: MOCK_USERS[1].id,
        candidate_id: MOCK_CANDIDATES[0].id,
        role_id: MOCK_ROLES[0].id,
        is_pool_candidate: false,
        base_fee: 15000,
        pool_discount: null,
        final_fee: 15000,
        fee_breakdown: {},
        status,
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
      } as Quote;
    },
  },
  copilot: {
    query: async () => {
      return new Response(
        JSON.stringify({
          summary: "Mock copilot response.",
          interpretation: "Interpreted your query",
          results: [],
          total_count: 0,
          actions: [],
          followup_suggestions: ["Show more candidates", "Filter by location"],
        }),
        { headers: { "Content-Type": "application/json" } }
      );
    },
    stream: async () => {
      // Return a mock SSE stream
      const events = [
        `data: ${JSON.stringify({ phase: "parsing", message: "Understanding..." })}\n\n`,
        `data: ${JSON.stringify({ phase: "parsed", interpretation: "Mock query parsed" })}\n\n`,
        `data: ${JSON.stringify({ phase: "executing", message: "Searching..." })}\n\n`,
        `data: ${JSON.stringify({ phase: "executed", total_count: 0 })}\n\n`,
        `data: ${JSON.stringify({ phase: "complete", summary: "Mock results", actions: [], followup_suggestions: [] })}\n\n`,
        `data: ${JSON.stringify({ phase: "done" })}\n\n`,
      ].join("");
      return new Response(events, { headers: { "Content-Type": "text/event-stream" } });
    },
  },
  signals: {
    recent: async () => { await delay(); return []; },
  },
  admin: {
    stats: async () => {
      await delay();
      return {
        totals: { candidates: MOCK_CANDIDATES.length, roles: MOCK_ROLES.length, matches: MOCK_MATCHES.length },
        active: { active_roles: MOCK_ROLES.filter((r) => r.status === "active").length },
        growth_7d: { new_candidates: 5, new_matches: 12 },
      };
    },
    pipelineStatus: async () => {
      await delay();
      return {
        extraction_queue: { pending: 12, low_confidence_review: 3, processed: 847 },
        confidence_distribution: { high: 42, medium: 8, low: 2 },
        embedding_coverage: { with_embedding: 45, total: 52, percentage: 86.5 },
      };
    },
    adapterHealth: async () => {
      await delay();
      return [
        { adapter_name: "bullhorn", status: "healthy", last_sync: "2026-03-24T08:00:00Z", records_processed: 312, error_count: 3 },
        { adapter_name: "hubspot", status: "healthy", last_sync: "2026-03-24T07:30:00Z", records_processed: 189, error_count: 4 },
        { adapter_name: "linkedin", status: "degraded", last_sync: "2026-03-23T22:00:00Z", records_processed: 95, error_count: 8 },
      ];
    },
    users: async () => { await delay(); return [...MOCK_USERS]; },
  },
  users: {
    me: async () => { await delay(); return MOCK_USERS[0]; },
  },
  health: async () => { await delay(); return { status: "ok" }; },
};
