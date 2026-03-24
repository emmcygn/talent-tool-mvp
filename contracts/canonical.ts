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
  embedding: number[] | null;
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
  embedding: number[] | null;
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
  experience_score: number;
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
// Organisation & User
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
  first_name: string;
  last_name: string;
  role: UserRole;
  organisation_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Compute display name from User record. */
export function userFullName(u: Pick<User, "first_name" | "last_name">): string {
  return `${u.first_name} ${u.last_name}`;
}
