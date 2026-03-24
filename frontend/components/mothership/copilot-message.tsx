"use client";

import { useState } from "react";
import type { CopilotMessage as CopilotMessageType } from "@/lib/copilot-types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  ChevronDown, Code, Star, FolderPlus, ExternalLink, Send,
  Bot, User as UserIcon,
} from "lucide-react";
import { formatRelativeTime, confidenceColor } from "@/lib/utils";
import type { Candidate, Match } from "@/contracts/canonical";

interface CopilotMessageProps {
  message: CopilotMessageType;
  onAction?: (action: string, entityId: string) => void;
}

export function CopilotMessageComponent({ message, onAction }: CopilotMessageProps) {
  const [queryOpen, setQueryOpen] = useState(false);
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${
        isUser ? "bg-slate-900 text-white" : "bg-gradient-to-br from-violet-500 to-blue-500 text-white"
      }`}>
        {isUser ? <UserIcon className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
      </div>

      <div className={`flex-1 min-w-0 space-y-2 ${isUser ? "text-right" : ""}`}>
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

        {message.structuredQuery && (
          <div>
            <button
              onClick={() => setQueryOpen(!queryOpen)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-slate-900 transition-colors"
            >
              <Code className="h-3 w-3" />
              <span>Show query</span>
              <ChevronDown className={`h-3 w-3 transition-transform ${queryOpen ? "rotate-180" : ""}`} />
            </button>
            {queryOpen && (
              <div className="mt-1 rounded-md bg-slate-950 p-3 text-xs font-mono text-slate-300 overflow-x-auto">
                <p className="text-slate-400 mb-1">{"// "}{message.structuredQuery.description}</p>
                <pre>{JSON.stringify(message.structuredQuery.filters, null, 2)}</pre>
                {message.structuredQuery.sort_by && (
                  <p className="mt-1 text-slate-500">sort: {message.structuredQuery.sort_by}</p>
                )}
                <p className="text-slate-500">limit: {message.structuredQuery.limit}</p>
              </div>
            )}
          </div>
        )}

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
