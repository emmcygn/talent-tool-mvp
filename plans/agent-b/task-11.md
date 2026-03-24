# Agent B — Task 11: Mind — Quotes + Pipeline

## Mission
Build the quote request flow with fee breakdown display, quote list page with status tracking, and the hiring pipeline kanban board with drag-and-drop between stages.

## Context
Day 4. Quotes are how clients request introductions to candidates. When they click "Request Intro", the system generates a quote showing the fee breakdown including pool discounts. The pipeline kanban is the client's primary workflow view — tracking candidates from Matched through to Placed. This is premium, polished UI for non-technical hiring managers.

## Prerequisites
- B-01: Next.js scaffold, TypeScript contracts, shadcn/ui installed
- B-03: Shared UI components (candidate-card, skill-chips, confidence-badge, loading-skeleton, empty-state)
- B-04: API client with `api.quotes.*` methods

## Checklist
- [ ] Create `QuoteCard` component (`components/mind/quote-card.tsx`) — fee breakdown display
- [ ] Create `QuoteRequestDialog` component — "Request Intro" flow
- [ ] Create quotes page (`app/mind/quotes/page.tsx`) — all quote requests with status
- [ ] Create `KanbanBoard` component (`components/shared/kanban-board.tsx`) — reusable drag-and-drop
- [ ] Create `KanbanCandidateCard` component — candidate summary for kanban lanes
- [ ] Create pipeline page (`app/mind/pipeline/page.tsx`) — hiring pipeline kanban
- [ ] Implement stage notes per candidate
- [ ] Wire to API client with loading and empty states
- [ ] Commit: "Agent B Task 11: Mind — Quotes + pipeline kanban"

## Implementation Details

### Quote Card (`components/mind/quote-card.tsx`)

```tsx
"use client";

import { Quote, QuoteStatus } from "@/contracts/canonical";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { formatCurrency, formatDate } from "@/lib/utils";
import { CheckCircle2, XCircle, Clock, Sparkles, Tag, ArrowDown } from "lucide-react";

const statusConfig: Record<QuoteStatus, {
  label: string;
  className: string;
  icon: React.ElementType;
}> = {
  generated: { label: "Ready", className: "border-blue-300 bg-blue-50 text-blue-700", icon: Sparkles },
  sent: { label: "Sent", className: "border-amber-300 bg-amber-50 text-amber-700", icon: Clock },
  accepted: { label: "Accepted", className: "border-green-300 bg-green-50 text-green-700", icon: CheckCircle2 },
  declined: { label: "Declined", className: "border-red-300 bg-red-50 text-red-700", icon: XCircle },
  expired: { label: "Expired", className: "border-slate-300 bg-slate-50 text-slate-500", icon: Clock },
};

interface QuoteCardProps {
  quote: Quote;
  candidateName?: string;
  roleTitle?: string;
  onAccept?: () => void;
  onDecline?: () => void;
  compact?: boolean;
}

export function QuoteCard({
  quote, candidateName, roleTitle, onAccept, onDecline, compact,
}: QuoteCardProps) {
  const status = statusConfig[quote.status];
  const StatusIcon = status.icon;
  const hasDiscount = quote.is_pool_candidate && quote.pool_discount;
  const savingAmount = hasDiscount ? quote.base_fee - quote.final_fee : 0;

  if (compact) {
    return (
      <div className="flex items-center justify-between rounded-lg border p-3">
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium truncate">{candidateName ?? "Candidate"}</div>
          <div className="text-xs text-muted-foreground">{roleTitle ?? "Role"}</div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold">{formatCurrency(quote.final_fee)}</span>
          <Badge variant="outline" className={status.className}>
            <StatusIcon className="h-3 w-3 mr-1" />
            {status.label}
          </Badge>
        </div>
      </div>
    );
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{candidateName ?? "Candidate"}</CardTitle>
            <p className="text-sm text-muted-foreground mt-0.5">
              {roleTitle ?? "Role"} · Quoted {formatDate(quote.created_at)}
            </p>
          </div>
          <Badge variant="outline" className={status.className}>
            <StatusIcon className="h-3 w-3 mr-1" />
            {status.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {/* Fee breakdown */}
        <div className="rounded-lg bg-slate-50 p-4 space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Standard placement fee</span>
            <span className="font-medium">{formatCurrency(quote.base_fee)}</span>
          </div>

          {hasDiscount && (
            <>
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-1.5 text-green-700">
                  <Tag className="h-3.5 w-3.5" />
                  Pre-vetted talent network discount
                </span>
                <span className="font-medium text-green-700">
                  -{formatCurrency(savingAmount)}
                </span>
              </div>
              <div className="flex items-center justify-center">
                <ArrowDown className="h-4 w-4 text-muted-foreground" />
              </div>
            </>
          )}

          <Separator />

          <div className="flex items-center justify-between">
            <span className="font-semibold">
              {hasDiscount ? "Your fee" : "Placement fee"}
            </span>
            <span className="text-xl font-bold">{formatCurrency(quote.final_fee)}</span>
          </div>

          {hasDiscount && (
            <div className="rounded-md bg-green-50 border border-green-200 px-3 py-2 text-center">
              <p className="text-sm font-medium text-green-800">
                You save {formatCurrency(savingAmount)} with our pre-vetted talent network
              </p>
            </div>
          )}
        </div>

        {/* Expiry */}
        <p className="text-xs text-muted-foreground text-center mt-3">
          Quote valid until {formatDate(quote.expires_at)}
        </p>

        {/* Actions */}
        {(quote.status === "generated" || quote.status === "sent") && onAccept && onDecline && (
          <div className="flex gap-3 mt-4">
            <Button className="flex-1" onClick={onAccept}>
              <CheckCircle2 className="h-4 w-4 mr-1.5" />
              Accept &amp; Request Intro
            </Button>
            <Button variant="outline" className="flex-1" onClick={onDecline}>
              Decline
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

### Quote Request Dialog (`components/mind/quote-request-dialog.tsx`)

```tsx
"use client";

import { useState } from "react";
import { Quote, CandidateAnonymized } from "@/contracts/canonical";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import { QuoteCard } from "./quote-card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";

interface QuoteRequestDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  candidate: CandidateAnonymized | null;
  roleId: string;
  onQuoteAccepted?: (quote: Quote) => void;
}

export function QuoteRequestDialog({
  open, onOpenChange, candidate, roleId, onQuoteAccepted,
}: QuoteRequestDialogProps) {
  const [quote, setQuote] = useState<Quote | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generateQuote() {
    if (!candidate) return;
    setLoading(true);
    setError(null);
    try {
      const q = await api.quotes.request({ candidate_id: candidate.id, role_id: roleId });
      setQuote(q);
    } catch {
      setError("Failed to generate quote. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  // Auto-generate on open
  useState(() => {
    if (open && candidate && !quote) {
      generateQuote();
    }
  });

  async function handleAccept() {
    if (!quote) return;
    // Accept the quote via API (update status)
    onQuoteAccepted?.(quote);
    onOpenChange(false);
  }

  function handleDecline() {
    onOpenChange(false);
    setQuote(null);
  }

  const candidateName = candidate
    ? `${candidate.first_name} ${candidate.last_initial}.`
    : "Candidate";

  return (
    <Dialog open={open} onOpenChange={(o) => { onOpenChange(o); if (!o) setQuote(null); }}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>Request Introduction</DialogTitle>
          <DialogDescription>
            Review the placement fee for {candidateName} before requesting an introduction.
          </DialogDescription>
        </DialogHeader>

        <div className="py-2">
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-40 w-full rounded-lg" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : error ? (
            <div className="text-center py-6">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          ) : quote ? (
            <QuoteCard
              quote={quote}
              candidateName={candidateName}
              onAccept={handleAccept}
              onDecline={handleDecline}
            />
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

### Quotes Page (`app/mind/quotes/page.tsx`)

```tsx
"use client";

import { useState, useEffect } from "react";
import { Quote } from "@/contracts/canonical";
import { api } from "@/lib/api";
import { QuoteCard } from "@/components/mind/quote-card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileText, Clock, CheckCircle2, XCircle } from "lucide-react";

export default function QuotesPage() {
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.quotes.list();
        setQuotes(data);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const active = quotes.filter((q) => q.status === "generated" || q.status === "sent");
  const accepted = quotes.filter((q) => q.status === "accepted");
  const declined = quotes.filter((q) => q.status === "declined" || q.status === "expired");

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Quotes</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Review and manage your introduction requests.
        </p>
      </div>

      <Tabs defaultValue="active">
        <TabsList>
          <TabsTrigger value="active" className="gap-1.5">
            <Clock className="h-4 w-4" />
            Active
            {active.length > 0 && (
              <span className="ml-1 rounded-full bg-blue-100 text-blue-700 px-2 py-0.5 text-xs font-medium">
                {active.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="accepted" className="gap-1.5">
            <CheckCircle2 className="h-4 w-4" />
            Accepted
          </TabsTrigger>
          <TabsTrigger value="history" className="gap-1.5">
            <FileText className="h-4 w-4" />
            History
          </TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="mt-4 space-y-4">
          {loading ? (
            Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-64 rounded-lg" />
            ))
          ) : active.length === 0 ? (
            <div className="text-center py-12 border rounded-lg border-dashed">
              <FileText className="h-10 w-10 mx-auto text-muted-foreground/50 mb-3" />
              <p className="text-muted-foreground">No active quotes.</p>
              <p className="text-sm text-muted-foreground mt-1">
                Request an introduction from the candidates page to get started.
              </p>
            </div>
          ) : (
            active.map((q) => (
              <QuoteCard
                key={q.id}
                quote={q}
                onAccept={() => {/* Accept via API */}}
                onDecline={() => {/* Decline via API */}}
              />
            ))
          )}
        </TabsContent>

        <TabsContent value="accepted" className="mt-4 space-y-4">
          {accepted.length === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">
              No accepted quotes yet.
            </p>
          ) : (
            accepted.map((q) => (
              <QuoteCard key={q.id} quote={q} />
            ))
          )}
        </TabsContent>

        <TabsContent value="history" className="mt-4 space-y-3">
          {declined.length === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">
              No past quotes.
            </p>
          ) : (
            declined.map((q) => (
              <QuoteCard key={q.id} quote={q} compact />
            ))
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### Kanban Board (`components/shared/kanban-board.tsx`)

```tsx
"use client";

import { useState, useCallback } from "react";
import { cn } from "@/lib/utils";

export interface KanbanStage {
  id: string;
  label: string;
  color: string; // Tailwind color class for header
}

export interface KanbanItem {
  id: string;
  stage: string;
}

interface KanbanBoardProps<T extends KanbanItem> {
  stages: KanbanStage[];
  items: T[];
  onMoveItem: (itemId: string, toStage: string) => void;
  renderItem: (item: T) => React.ReactNode;
  renderStageHeader?: (stage: KanbanStage, count: number) => React.ReactNode;
}

export function KanbanBoard<T extends KanbanItem>({
  stages, items, onMoveItem, renderItem, renderStageHeader,
}: KanbanBoardProps<T>) {
  const [dragItem, setDragItem] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState<string | null>(null);

  const handleDragStart = useCallback((itemId: string) => {
    setDragItem(itemId);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent, stageId: string) => {
    e.preventDefault();
    setDragOver(stageId);
  }, []);

  const handleDrop = useCallback((stageId: string) => {
    if (dragItem) {
      onMoveItem(dragItem, stageId);
    }
    setDragItem(null);
    setDragOver(null);
  }, [dragItem, onMoveItem]);

  const handleDragEnd = useCallback(() => {
    setDragItem(null);
    setDragOver(null);
  }, []);

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {stages.map((stage) => {
        const stageItems = items.filter((item) => item.stage === stage.id);
        const isOver = dragOver === stage.id;

        return (
          <div
            key={stage.id}
            className={cn(
              "flex-shrink-0 w-72 rounded-lg border bg-slate-50/50 transition-colors",
              isOver && "border-blue-300 bg-blue-50/30"
            )}
            onDragOver={(e) => handleDragOver(e, stage.id)}
            onDrop={() => handleDrop(stage.id)}
            onDragLeave={() => setDragOver(null)}
          >
            {/* Stage header */}
            <div className="p-3 border-b">
              {renderStageHeader ? (
                renderStageHeader(stage, stageItems.length)
              ) : (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={cn("w-2 h-2 rounded-full", stage.color)} />
                    <span className="text-sm font-medium">{stage.label}</span>
                  </div>
                  <span className="text-xs text-muted-foreground bg-white rounded-full px-2 py-0.5 border">
                    {stageItems.length}
                  </span>
                </div>
              )}
            </div>

            {/* Items */}
            <div className="p-2 space-y-2 min-h-[200px]">
              {stageItems.map((item) => (
                <div
                  key={item.id}
                  draggable
                  onDragStart={() => handleDragStart(item.id)}
                  onDragEnd={handleDragEnd}
                  className={cn(
                    "cursor-grab active:cursor-grabbing transition-opacity",
                    dragItem === item.id && "opacity-50"
                  )}
                >
                  {renderItem(item)}
                </div>
              ))}
              {stageItems.length === 0 && (
                <div className="flex items-center justify-center h-24 text-xs text-muted-foreground border border-dashed rounded-md">
                  Drop here
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

### Pipeline Candidate Card (`components/mind/pipeline-candidate-card.tsx`)

```tsx
"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ConfidenceLevel, AvailabilityStatus } from "@/contracts/canonical";
import { confidenceColor } from "@/lib/utils";
import { MessageSquare, StickyNote } from "lucide-react";

interface PipelineCandidateItem {
  id: string;
  stage: string;
  candidateId: string;
  name: string;
  location: string | null;
  skills: string[];
  confidence: ConfidenceLevel;
  availability: AvailabilityStatus | null;
  stageNotes: string;
}

interface PipelineCandidateCardProps {
  item: PipelineCandidateItem;
  onUpdateNotes: (itemId: string, notes: string) => void;
}

export function PipelineCandidateCard({ item, onUpdateNotes }: PipelineCandidateCardProps) {
  const [showNotes, setShowNotes] = useState(false);
  const [notes, setNotes] = useState(item.stageNotes);

  return (
    <Card className="shadow-sm hover:shadow transition-shadow">
      <CardContent className="p-3">
        <div className="flex items-start justify-between">
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{item.name}</p>
            {item.location && (
              <p className="text-xs text-muted-foreground">{item.location}</p>
            )}
          </div>
          <Badge
            variant="outline"
            className={`text-[10px] shrink-0 ${confidenceColor(item.confidence)}`}
          >
            {item.confidence}
          </Badge>
        </div>

        {/* Skills */}
        <div className="flex flex-wrap gap-1 mt-2">
          {item.skills.slice(0, 3).map((skill) => (
            <Badge key={skill} variant="secondary" className="text-[10px] py-0 px-1.5">
              {skill}
            </Badge>
          ))}
          {item.skills.length > 3 && (
            <span className="text-[10px] text-muted-foreground">
              +{item.skills.length - 3}
            </span>
          )}
        </div>

        {/* Availability */}
        {item.availability && (
          <p className="text-[10px] text-muted-foreground mt-1.5 capitalize">
            {item.availability.replace("_", " ")}
          </p>
        )}

        {/* Notes toggle */}
        <div className="mt-2 pt-2 border-t">
          <button
            onClick={(e) => { e.stopPropagation(); setShowNotes(!showNotes); }}
            className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-slate-900 transition-colors"
          >
            {item.stageNotes ? (
              <StickyNote className="h-3 w-3 text-amber-500" />
            ) : (
              <MessageSquare className="h-3 w-3" />
            )}
            {item.stageNotes ? "View notes" : "Add notes"}
          </button>

          {showNotes && (
            <div className="mt-2" onClick={(e) => e.stopPropagation()}>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                onBlur={() => onUpdateNotes(item.id, notes)}
                placeholder="Add stage notes..."
                rows={2}
                className="text-xs"
              />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export type { PipelineCandidateItem };
```

### Pipeline Page (`app/mind/pipeline/page.tsx`)

```tsx
"use client";

import { useState, useEffect } from "react";
import { KanbanBoard, KanbanStage } from "@/components/shared/kanban-board";
import {
  PipelineCandidateCard,
  PipelineCandidateItem,
} from "@/components/mind/pipeline-candidate-card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Role } from "@/contracts/canonical";
import { api } from "@/lib/api";
import { Columns3, Filter } from "lucide-react";

const PIPELINE_STAGES: KanbanStage[] = [
  { id: "matched", label: "Matched", color: "bg-slate-400" },
  { id: "shortlisted", label: "Shortlisted", color: "bg-blue-500" },
  { id: "intro_requested", label: "Intro Requested", color: "bg-purple-500" },
  { id: "interviewing", label: "Interviewing", color: "bg-amber-500" },
  { id: "offer", label: "Offer", color: "bg-orange-500" },
  { id: "placed", label: "Placed", color: "bg-green-500" },
];

export default function PipelinePage() {
  const [items, setItems] = useState<PipelineCandidateItem[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedRole, setSelectedRole] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const rolesData = await api.roles.list();
        setRoles(rolesData);
        // Pipeline items would come from a dedicated endpoint or composed from matches
        // For now, mock structure
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function handleMoveItem(itemId: string, toStage: string) {
    setItems((prev) =>
      prev.map((item) =>
        item.id === itemId ? { ...item, stage: toStage } : item
      )
    );
    // Also call API to update match status / pipeline stage
  }

  function handleUpdateNotes(itemId: string, notes: string) {
    setItems((prev) =>
      prev.map((item) =>
        item.id === itemId ? { ...item, stageNotes: notes } : item
      )
    );
    // Also persist via API
  }

  const filteredItems =
    selectedRole === "all"
      ? items
      : items.filter((item) => true); // Filter by role when data model supports it

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
            <Columns3 className="h-6 w-6" />
            Hiring Pipeline
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Track candidates through your hiring process. Drag cards between stages.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <Select value={selectedRole} onValueChange={setSelectedRole}>
            <SelectTrigger className="w-[220px]">
              <SelectValue placeholder="All roles" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All roles</SelectItem>
              {roles.map((role) => (
                <SelectItem key={role.id} value={role.id}>
                  {role.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Kanban */}
      {loading ? (
        <div className="flex gap-4">
          {PIPELINE_STAGES.map((stage) => (
            <Skeleton key={stage.id} className="h-96 w-72 rounded-lg" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 border rounded-lg border-dashed">
          <Columns3 className="h-10 w-10 mx-auto text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground">No candidates in your pipeline yet.</p>
          <p className="text-sm text-muted-foreground mt-1">
            Review matched candidates and shortlist them to build your pipeline.
          </p>
        </div>
      ) : (
        <KanbanBoard
          stages={PIPELINE_STAGES}
          items={filteredItems}
          onMoveItem={handleMoveItem}
          renderItem={(item) => (
            <PipelineCandidateCard
              item={item}
              onUpdateNotes={handleUpdateNotes}
            />
          )}
        />
      )}
    </div>
  );
}
```

## Outputs
- `frontend/components/mind/quote-card.tsx` — Quote fee breakdown display
- `frontend/components/mind/quote-request-dialog.tsx` — Request Intro flow
- `frontend/components/mind/pipeline-candidate-card.tsx` — Kanban card for pipeline
- `frontend/components/shared/kanban-board.tsx` — Reusable drag-and-drop kanban
- `frontend/app/mind/quotes/page.tsx` — Quote list with tabs
- `frontend/app/mind/pipeline/page.tsx` — Hiring pipeline kanban

## Acceptance Criteria
1. Quote card shows fee breakdown: base fee, pool discount (if applicable), final fee, and saving amount
2. "Request Intro" opens dialog that generates and displays a quote
3. Accept/decline buttons work on active quotes
4. Quotes page shows tabs: Active, Accepted, History
5. Kanban board renders all 6 pipeline stages with correct column headers
6. Drag-and-drop moves candidates between stages
7. Stage notes can be added/edited per candidate per stage
8. Role filter dropdown filters kanban items
9. Loading skeletons and empty states render correctly
10. Pre-vetted pool discount is visually highlighted with green savings callout

## Handoff Notes
- **To Agent A:** Frontend expects `GET /api/quotes` to list client's quotes. `POST /api/quotes` generates a new quote. Needs an endpoint for pipeline state (or frontend composes from match statuses). Needs `PUT /api/quotes/{id}/accept` and `PUT /api/quotes/{id}/decline`.
- **To Task 13:** Quote counts and pipeline summary will be shown on the client dashboard.
- **Decision:** Kanban uses native HTML drag-and-drop rather than a library (simpler, no dependency). The KanbanBoard component is generic and reusable. Pipeline stages map 1:1 with the match status flow but extend it with "Interviewing", "Offer", and "Placed" stages.
