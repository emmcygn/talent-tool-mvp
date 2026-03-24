"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import type { CopilotMessage as CopilotMessageType } from "@/lib/copilot-types";
import { CopilotMessageComponent } from "./copilot-message";
import { CopilotInput } from "./copilot-input";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { Bot, PanelRightClose, PanelRightOpen, RotateCcw } from "lucide-react";

interface CopilotSidebarProps {
  pageContext?: string;
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
      // Use the SSE streaming endpoint — backend uses { query } not { message },
      // and sends events with 'phase' field, not 'type'
      const response = await apiClient.copilot.stream(text);
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

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n").filter((l) => l.startsWith("data: "));

        for (const line of lines) {
          try {
            const parsed = JSON.parse(line.slice(6));
            const phase: string = parsed.phase ?? "";

            if (phase === "parsing" || phase === "executing") {
              fullContent = parsed.message ?? fullContent;
            } else if (phase === "parsed") {
              fullContent = parsed.interpretation ?? fullContent;
            } else if (phase === "results" && parsed.results) {
              results = parsed.results;
            } else if (phase === "complete") {
              fullContent = parsed.summary ?? fullContent;
              structuredQuery = parsed.query_executed;
              replySuggestions = parsed.followup_suggestions ?? [];
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
                      isStreaming: phase !== "done",
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

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  function handleAction(action: string, entityId: string) {
    // Action handling — to be wired to real navigation/API calls
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
        <div
          className="text-xs text-muted-foreground font-medium tracking-wider rotate-180"
          style={{ writingMode: "vertical-rl" }}
        >
          COPILOT
        </div>
      </div>
    );
  }

  return (
    <div className="w-96 border-l bg-white flex flex-col h-full">
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
