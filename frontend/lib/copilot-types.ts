import type { Candidate, Match, Collection } from "@/contracts/canonical";

export interface CopilotMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  structuredQuery?: CopilotStructuredQuery;
  results?: CopilotResult[];
  suggestions?: string[];
  isStreaming?: boolean;
}

export interface CopilotStructuredQuery {
  filters: Record<string, unknown>;
  sort_by: string | null;
  limit: number;
  description: string;
}

export interface CopilotResult {
  type: "candidate" | "match" | "collection" | "stat";
  data: Candidate | Match | Collection | Record<string, unknown>;
  actions: CopilotAction[];
}

export interface CopilotAction {
  label: string;
  action: string;
  entityId: string;
}

export interface CopilotStreamChunk {
  type: "token" | "query" | "results" | "suggestions" | "done";
  content?: string;
  query?: CopilotStructuredQuery;
  results?: CopilotResult[];
  suggestions?: string[];
}
