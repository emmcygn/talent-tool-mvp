# Agent B — Task 12: Mothership — Copilot Sidebar

## Mission
Build the copilot sidebar: always-visible collapsible panel with chat-style conversation UI, streaming response rendering, structured query transparency, inline results with action buttons, and context-aware suggestions.

## Context
Day 5. The copilot is the signature feature of Mothership — a natural language interface that lets talent partners and admins query the system conversationally. "Who are my best Python candidates available in London?" returns results inline with one-click actions. Every response shows the structured query that was run for transparency. The sidebar is always accessible from the Mothership layout.

## Prerequisites
- B-01: Next.js scaffold, TypeScript contracts, shadcn/ui installed
- B-04: API client with `api.copilot.query()` streaming endpoint

## Checklist
- [ ] Create `CopilotSidebar` component (`components/mothership/copilot-sidebar.tsx`) — collapsible panel
- [ ] Create `CopilotMessage` component (`components/mothership/copilot-message.tsx`) — single message with results
- [ ] Create `CopilotInput` component — input with send button and autocomplete suggestions
- [ ] Create `CopilotQueryDetails` component — collapsible "Show query" section
- [ ] Create `CopilotResultActions` component — one-click action buttons on results
- [ ] Implement streaming response rendering (token by token)
- [ ] Implement multi-turn conversation with context
- [ ] Implement suggested queries based on current page context
- [ ] Integrate copilot sidebar into Mothership layout
- [ ] Commit: "Agent B Task 12: Mothership — Copilot sidebar"

## Implementation Details

### Copilot Types

```typescript
// lib/copilot-types.ts

import { Candidate, Match, Collection } from "@/contracts/canonical";

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
  description: string; // Human-readable summary of what was searched
}

export interface CopilotResult {
  type: "candidate" | "match" | "collection" | "stat";
  data: Candidate | Match | Collection | Record<string, unknown>;
  actions: CopilotAction[];
}

export interface CopilotAction {
  label: string;
  action: string; // "shortlist" | "add_to_collection" | "view_detail" | "refer"
  entityId: string;
}

export interface CopilotStreamChunk {
  type: "token" | "query" | "results" | "suggestions" | "done";
  content?: string;
  query?: CopilotStructuredQuery;
  results?: CopilotResult[];
  suggestions?: string[];
}
```

### Copilot Message Component (`components/mothership/copilot-message.tsx`)

```tsx
"use client";

import { useState } from "react";
import { CopilotMessage as CopilotMessageType } from "@/lib/copilot-types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Collapsible, CollapsibleContent, CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  ChevronDown, Code, Star, FolderPlus, ExternalLink, Send,
  Bot, User as UserIcon,
} from "lucide-react";
import { formatRelativeTime, confidenceColor } from "@/lib/utils";
import { Candidate, Match } from "@/contracts/canonical";

interface CopilotMessageProps {
  message: CopilotMessageType;
  onAction?: (action: string, entityId: string) => void;
}

export function CopilotMessageComponent({ message, onAction }: CopilotMessageProps) {
  const [queryOpen, setQueryOpen] = useState(false);
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${
        isUser ? "bg-slate-900 text-white" : "bg-gradient-to-br from-violet-500 to-blue-500 text-white"
      }`}>
        {isUser ? <UserIcon className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
      </div>

      <div className={`flex-1 min-w-0 space-y-2 ${isUser ? "text-right" : ""}`}>
        {/* Text content */}
        <div className={`inline-block rounded-lg px-3 py-2 text-sm max-w-full ${
          isUser
            ? "bg-slate-900 text-white rounded-tr-sm"
            : "bg-slate-100 text-slate-900 rounded-tl-sm"
        }`}>
          <p className="whitespace-pre-wrap text-left">{message.content}</p>
          {message.isStreaming && (
            <span className="inline-block w-1.5 h-4 bg-current animate-pulse ml-0.5 align-middle" />
          )}
        </div>

        {/* Structured query (collapsible) */}
        {message.structuredQuery && (
          <Collapsible open={queryOpen} onOpenChange={setQueryOpen}>
            <CollapsibleTrigger asChild>
              <button className="flex items-center gap-1 text-xs text-muted-foreground hover:text-slate-900 transition-colors">
                <Code className="h-3 w-3" />
                <span>Show query</span>
                <ChevronDown className={`h-3 w-3 transition-transform ${queryOpen ? "rotate-180" : ""}`} />
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="mt-1 rounded-md bg-slate-950 p-3 text-xs font-mono text-slate-300 overflow-x-auto">
                <p className="text-slate-400 mb-1">// {message.structuredQuery.description}</p>
                <pre>{JSON.stringify(message.structuredQuery.filters, null, 2)}</pre>
                {message.structuredQuery.sort_by && (
                  <p className="mt-1 text-slate-500">sort: {message.structuredQuery.sort_by}</p>
                )}
                <p className="text-slate-500">limit: {message.structuredQuery.limit}</p>
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}

        {/* Inline results */}
        {message.results && message.results.length > 0 && (
          <div className="space-y-2 mt-2">
            {message.results.map((result, i) => (
              <Card key={i} className="p-3">
                {result.type === "candidate" && (
                  <CandidateInlineResult
                    candidate={result.data as Candidate}
                    actions={result.actions}
                    onAction={onAction}
                  />
                )}
                {result.type === "match" && (
                  <MatchInlineResult
                    match={result.data as Match}
                    actions={result.actions}
                    onAction={onAction}
                  />
                )}
                {result.type === "stat" && (
                  <StatInlineResult data={result.data as Record<string, unknown>} />
                )}
              </Card>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <p className="text-[10px] text-muted-foreground">
          {formatRelativeTime(message.timestamp)}
        </p>
      </div>
    </div>
  );
}

function CandidateInlineResult({
  candidate, actions, onAction,
}: { candidate: Candidate; actions: { label: string; action: string; entityId: string }[]; onAction?: (a: string, id: string) => void }) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-medium">
            {candidate.first_name} {candidate.last_name}
          </span>
          <span className="text-xs text-muted-foreground ml-2">
            {candidate.seniority} · {candidate.location}
          </span>
        </div>
        {candidate.availability && (
          <Badge variant="outline" className="text-[10px]">
            {candidate.availability.replace("_", " ")}
          </Badge>
        )}
      </div>
      <div className="flex flex-wrap gap-1 mt-1.5">
        {candidate.skills.slice(0, 4).map((s) => (
          <Badge key={s.name} variant="secondary" className="text-[10px] py-0 px-1.5">
            {s.name}
          </Badge>
        ))}
      </div>
      {/* Action buttons */}
      {actions.length > 0 && (
        <div className="flex gap-1.5 mt-2 pt-2 border-t">
          {actions.map((a) => (
            <Button
              key={a.action}
              size="sm"
              variant="ghost"
              className="h-6 text-xs px-2"
              onClick={() => onAction?.(a.action, a.entityId)}
            >
              {a.action === "shortlist" && <Star className="h-3 w-3 mr-1" />}
              {a.action === "add_to_collection" && <FolderPlus className="h-3 w-3 mr-1" />}
              {a.action === "refer" && <Send className="h-3 w-3 mr-1" />}
              {a.action === "view_detail" && <ExternalLink className="h-3 w-3 mr-1" />}
              {a.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}

function MatchInlineResult({
  match, actions, onAction,
}: { match: Match; actions: { label: string; action: string; entityId: string }[]; onAction?: (a: string, id: string) => void }) {
  return (
    <div>
      <div className="flex items-center gap-2">
        <Badge variant="outline" className={`text-[10px] ${confidenceColor(match.confidence)}`}>
          {match.confidence}
        </Badge>
        <span className="text-xs text-muted-foreground">
          Score: {Math.round(match.overall_score * 100)}%
        </span>
      </div>
      <p className="text-sm mt-1">{match.explanation}</p>
      {actions.length > 0 && (
        <div className="flex gap-1.5 mt-2 pt-2 border-t">
          {actions.map((a) => (
            <Button
              key={a.action}
              size="sm"
              variant="ghost"
              className="h-6 text-xs px-2"
              onClick={() => onAction?.(a.action, a.entityId)}
            >
              {a.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}

function StatInlineResult({ data }: { data: Record<string, unknown> }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {Object.entries(data).map(([key, value]) => (
        <div key={key} className="text-center">
          <div className="text-lg font-semibold">{String(value)}</div>
          <div className="text-[10px] text-muted-foreground capitalize">
            {key.replace(/_/g, " ")}
          </div>
        </div>
      ))}
    </div>
  );
}
```

### Copilot Input (`components/mothership/copilot-input.tsx`)

```tsx
"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { SendHorizontal, Sparkles } from "lucide-react";

interface CopilotInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  suggestions: string[];
}

export function CopilotInput({ onSend, isLoading, suggestions }: CopilotInputProps) {
  const [value, setValue] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(true);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleSubmit() {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setValue("");
    setShowSuggestions(false);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  function handleSuggestionClick(suggestion: string) {
    onSend(suggestion);
    setShowSuggestions(false);
  }

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 120) + "px";
    }
  }, [value]);

  return (
    <div className="space-y-2">
      {/* Suggestions */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => handleSuggestionClick(s)}
              className="text-xs rounded-full border border-violet-200 bg-violet-50 text-violet-700 px-2.5 py-1 hover:bg-violet-100 transition-colors"
            >
              <Sparkles className="h-3 w-3 inline mr-1" />
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="flex items-end gap-2 rounded-lg border bg-white p-2">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => { setValue(e.target.value); setShowSuggestions(false); }}
          onKeyDown={handleKeyDown}
          placeholder="Ask about candidates, roles, matches..."
          className="min-h-[36px] max-h-[120px] resize-none border-0 focus-visible:ring-0 p-1 text-sm"
          rows={1}
        />
        <Button
          size="icon"
          onClick={handleSubmit}
          disabled={!value.trim() || isLoading}
          className="shrink-0 h-8 w-8"
        >
          <SendHorizontal className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
```

### Copilot Sidebar (`components/mothership/copilot-sidebar.tsx`)

```tsx
"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { CopilotMessage as CopilotMessageType, CopilotStreamChunk } from "@/lib/copilot-types";
import { CopilotMessageComponent } from "./copilot-message";
import { CopilotInput } from "./copilot-input";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { Bot, PanelRightClose, PanelRightOpen, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";

interface CopilotSidebarProps {
  pageContext?: string; // Current page for context-aware suggestions
}

const DEFAULT_SUGGESTIONS: Record<string, string[]> = {
  default: [
    "Who are my top Python candidates?",
    "Show available senior engineers in London",
    "Candidates with fintech experience",
  ],
  candidates: [
    "Show candidates available immediately",
    "Who has the most experience in React?",
    "Find ML engineers with 5+ years",
  ],
  matching: [
    "Best matches for this role",
    "Show strong matches only",
    "Candidates matching but missing one skill",
  ],
  collections: [
    "Show shared collections with most candidates",
    "Find collections tagged with backend",
  ],
  admin: [
    "Candidate-to-placement conversion rate",
    "Which adapters had sync failures?",
    "Show low-confidence extractions this week",
  ],
};

export function CopilotSidebar({ pageContext = "default" }: CopilotSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [messages, setMessages] = useState<CopilotMessageType[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestions = DEFAULT_SUGGESTIONS[pageContext] || DEFAULT_SUGGESTIONS.default;

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async (text: string) => {
    const userMsg: CopilotMessageType = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    const assistantMsg: CopilotMessageType = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsStreaming(true);

    try {
      const response = await api.copilot.query(text);
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No reader");

      let fullContent = "";
      let structuredQuery: CopilotMessageType["structuredQuery"] = undefined;
      let results: CopilotMessageType["results"] = undefined;
      let replySuggestions: string[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        // Parse SSE chunks
        const lines = text.split("\n").filter((l) => l.startsWith("data: "));

        for (const line of lines) {
          try {
            const chunk: CopilotStreamChunk = JSON.parse(line.slice(6));

            if (chunk.type === "token" && chunk.content) {
              fullContent += chunk.content;
            } else if (chunk.type === "query" && chunk.query) {
              structuredQuery = chunk.query;
            } else if (chunk.type === "results" && chunk.results) {
              results = chunk.results;
            } else if (chunk.type === "suggestions" && chunk.suggestions) {
              replySuggestions = chunk.suggestions;
            }

            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsg.id
                  ? {
                      ...m,
                      content: fullContent,
                      structuredQuery,
                      results,
                      suggestions: replySuggestions,
                      isStreaming: chunk.type !== "done",
                    }
                  : m
              )
            );
          } catch {
            // Skip malformed chunks
          }
        }
      }
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsg.id
            ? {
                ...m,
                content: "Sorry, I encountered an error processing your request. Please try again.",
                isStreaming: false,
              }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
    }
  }, []);

  function handleAction(action: string, entityId: string) {
    // Handle one-click actions from results
    // e.g., shortlist, add to collection, view detail, refer
    console.log("Copilot action:", action, entityId);
  }

  function handleReset() {
    setMessages([]);
  }

  if (collapsed) {
    return (
      <div className="flex flex-col items-center py-4 px-1 border-l bg-white">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(false)}
          className="mb-2"
          aria-label="Expand copilot"
        >
          <PanelRightOpen className="h-4 w-4" />
        </Button>
        <div className="writing-mode-vertical text-xs text-muted-foreground font-medium tracking-wider rotate-180"
             style={{ writingMode: "vertical-rl" }}>
          COPILOT
        </div>
      </div>
    );
  }

  return (
    <div className="w-96 border-l bg-white flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center">
            <Bot className="h-3.5 w-3.5 text-white" />
          </div>
          <span className="text-sm font-semibold">Copilot</span>
        </div>
        <div className="flex items-center gap-1">
          {messages.length > 0 && (
            <Button variant="ghost" size="icon" onClick={handleReset} className="h-7 w-7"
                    aria-label="Clear conversation">
              <RotateCcw className="h-3.5 w-3.5" />
            </Button>
          )}
          <Button variant="ghost" size="icon" onClick={() => setCollapsed(true)} className="h-7 w-7"
                  aria-label="Collapse copilot">
            <PanelRightClose className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-100 to-blue-100 flex items-center justify-center mx-auto mb-3">
              <Bot className="h-6 w-6 text-violet-600" />
            </div>
            <p className="text-sm font-medium">How can I help?</p>
            <p className="text-xs text-muted-foreground mt-1">
              Ask me about candidates, matches, collections, or anything else.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <CopilotMessageComponent
            key={msg.id}
            message={msg}
            onAction={handleAction}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t shrink-0">
        <CopilotInput
          onSend={handleSend}
          isLoading={isStreaming}
          suggestions={messages.length === 0 ? suggestions : []}
        />
      </div>
    </div>
  );
}
```

### Mothership Layout Integration

```tsx
// In app/mothership/layout.tsx — wrap content with copilot sidebar

import { CopilotSidebar } from "@/components/mothership/copilot-sidebar";

export default function MothershipLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      {/* Main sidebar nav (existing) */}
      <aside className="w-56 border-r bg-slate-50 shrink-0">
        {/* ... navigation items ... */}
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>

      {/* Copilot sidebar */}
      <CopilotSidebar />
    </div>
  );
}
```

## Outputs
- `frontend/lib/copilot-types.ts` — Copilot type definitions
- `frontend/components/mothership/copilot-sidebar.tsx` — Main sidebar panel
- `frontend/components/mothership/copilot-message.tsx` — Message with results + actions
- `frontend/components/mothership/copilot-input.tsx` — Input with suggestions
- Updated `frontend/app/mothership/layout.tsx` — Sidebar integrated into layout

## Acceptance Criteria
1. Copilot sidebar is always visible in the Mothership layout (collapsible)
2. Collapse/expand toggle works, collapsed state shows vertical "COPILOT" label
3. Chat-style conversation with user messages on right, assistant on left
4. Streaming response renders token by token with cursor animation
5. Each response can show a collapsible "Show query" section with structured query details
6. Results render inline as candidate cards, match cards, or stat grids
7. One-click action buttons appear on results (shortlist, add to collection, refer, view)
8. Suggested queries appear based on current page context when conversation is empty
9. Multi-turn conversation maintains context (messages persist in state)
10. Clear conversation button resets the chat

## Handoff Notes
- **To Agent A:** Frontend expects `POST /api/copilot/query` to return an SSE stream. Each chunk is `data: {json}\n\n` with types: token (incremental text), query (structured query object), results (array of result objects), suggestions (follow-up queries), done (end of stream). The copilot endpoint should accept a `messages` array for multi-turn context.
- **To Task 13:** The copilot sidebar context changes based on the current page — pass `pageContext` prop from each page.
- **Decision:** Using SSE (Server-Sent Events) for streaming rather than WebSockets — simpler for the request/response pattern of copilot queries. The sidebar is 384px wide (w-96) which balances information density with not consuming too much horizontal space.
