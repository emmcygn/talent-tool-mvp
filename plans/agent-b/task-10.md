# Agent B — Task 10: Mothership — Handoff Inbox/Outbox

## Mission
Build the handoff management interface: tabbed inbox/outbox view, send handoff flow with candidate selection and partner picker, accept/decline with notes, attribution trail timeline, and status badges.

## Context
Day 4. Handoffs are how talent partners share candidates with each other. A partner selects candidates, picks a receiving partner, adds context notes, and optionally links a role. The receiver sees it in their inbox and can accept or decline with notes. The attribution trail tracks the full chain from ingestion through handoff to placement for commission tracking.

## Prerequisites
- B-01: Next.js scaffold, TypeScript contracts, shadcn/ui installed
- B-03: Shared UI components (candidate-card, skill-chips, confidence-badge, loading-skeleton, empty-state)
- B-04: API client with `api.handoffs.*` methods

## Checklist
- [ ] Create `HandoffCard` component (`components/mothership/handoff-card.tsx`)
- [ ] Create `HandoffSendDialog` component (send flow: select candidates, pick partner, add notes, link role)
- [ ] Create `HandoffRespondDialog` component (accept/decline with notes field)
- [ ] Create `HandoffTimeline` component (attribution trail)
- [ ] Create handoffs page (`app/mothership/handoffs/page.tsx`) with Inbox/Outbox tabs
- [ ] Implement status badges (pending/accepted/declined/expired)
- [ ] Wire to API client with loading and empty states
- [ ] Commit: "Agent B Task 10: Mothership — Handoff inbox/outbox"

## Implementation Details

### Handoff Status Badge (`components/mothership/handoff-status-badge.tsx`)

```tsx
import { HandoffStatus } from "@/contracts/canonical";
import { Badge } from "@/components/ui/badge";
import { Clock, CheckCircle2, XCircle, Timer } from "lucide-react";

const statusConfig: Record<HandoffStatus, {
  label: string;
  variant: "default" | "secondary" | "destructive" | "outline";
  className: string;
  icon: React.ElementType;
}> = {
  pending: {
    label: "Pending",
    variant: "outline",
    className: "border-amber-300 bg-amber-50 text-amber-700",
    icon: Clock,
  },
  accepted: {
    label: "Accepted",
    variant: "outline",
    className: "border-green-300 bg-green-50 text-green-700",
    icon: CheckCircle2,
  },
  declined: {
    label: "Declined",
    variant: "outline",
    className: "border-red-300 bg-red-50 text-red-700",
    icon: XCircle,
  },
  expired: {
    label: "Expired",
    variant: "outline",
    className: "border-slate-300 bg-slate-50 text-slate-500",
    icon: Timer,
  },
};

interface HandoffStatusBadgeProps {
  status: HandoffStatus;
}

export function HandoffStatusBadge({ status }: HandoffStatusBadgeProps) {
  const config = statusConfig[status];
  const Icon = config.icon;
  return (
    <Badge variant={config.variant} className={config.className}>
      <Icon className="h-3 w-3 mr-1" />
      {config.label}
    </Badge>
  );
}
```

### Handoff Card (`components/mothership/handoff-card.tsx`)

```tsx
"use client";

import { Handoff, User } from "@/contracts/canonical";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { HandoffStatusBadge } from "./handoff-status-badge";
import { Users, ArrowRight, MessageSquare, LinkIcon } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

interface HandoffCardProps {
  handoff: Handoff;
  sender?: User;
  receiver?: User;
  direction: "inbox" | "outbox";
  onAccept?: () => void;
  onDecline?: () => void;
  onViewDetail?: () => void;
}

export function HandoffCard({
  handoff, sender, receiver, direction, onAccept, onDecline, onViewDetail,
}: HandoffCardProps) {
  const otherParty = direction === "inbox" ? sender : receiver;
  const initials = otherParty?.full_name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase() ?? "??";

  return (
    <Card className="hover:shadow-sm transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          {/* Left: sender info + context */}
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <Avatar className="h-9 w-9 shrink-0">
              <AvatarFallback className="text-xs bg-slate-100">
                {initials}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-medium text-sm">
                  {direction === "inbox" ? sender?.full_name ?? "Unknown" : receiver?.full_name ?? "Unknown"}
                </span>
                <ArrowRight className="h-3 w-3 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  {direction === "inbox" ? "you" : receiver?.full_name ?? "Unknown"}
                </span>
                <HandoffStatusBadge status={handoff.status} />
              </div>

              {/* Candidate count */}
              <div className="flex items-center gap-1 text-sm text-muted-foreground mt-1">
                <Users className="h-3.5 w-3.5" />
                <span>
                  {handoff.candidate_ids.length} candidate{handoff.candidate_ids.length !== 1 ? "s" : ""}
                </span>
                {handoff.target_role_id && (
                  <>
                    <span className="mx-1">·</span>
                    <LinkIcon className="h-3.5 w-3.5" />
                    <span>Linked to role</span>
                  </>
                )}
                <span className="mx-1">·</span>
                <span>{formatRelativeTime(handoff.created_at)}</span>
              </div>

              {/* Context notes */}
              {handoff.context_notes && (
                <div className="mt-2 flex items-start gap-1.5">
                  <MessageSquare className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
                  <p className="text-sm text-slate-600 line-clamp-2">
                    {handoff.context_notes}
                  </p>
                </div>
              )}

              {/* Response notes */}
              {handoff.response_notes && (
                <div className="mt-1.5 rounded-md bg-slate-50 px-3 py-2">
                  <p className="text-sm text-slate-600 italic">
                    &ldquo;{handoff.response_notes}&rdquo;
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Right: actions */}
          <div className="flex items-center gap-2 ml-4 shrink-0">
            {direction === "inbox" && handoff.status === "pending" && (
              <>
                <Button size="sm" onClick={onAccept}>
                  Accept
                </Button>
                <Button size="sm" variant="outline" onClick={onDecline}>
                  Decline
                </Button>
              </>
            )}
            <Button size="sm" variant="ghost" onClick={onViewDetail}>
              View
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Send Handoff Dialog (`components/mothership/handoff-send-dialog.tsx`)

```tsx
"use client";

import { useState } from "react";
import { Candidate, HandoffCreate, Role, User } from "@/contracts/canonical";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Search, X, Users, Send } from "lucide-react";

interface HandoffSendDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: HandoffCreate) => void;
  candidates: Candidate[];
  partners: User[];
  roles: Role[];
  preselectedCandidateIds?: string[];
}

export function HandoffSendDialog({
  open, onOpenChange, onSubmit,
  candidates, partners, roles,
  preselectedCandidateIds = [],
}: HandoffSendDialogProps) {
  const [selectedCandidates, setSelectedCandidates] = useState<string[]>(preselectedCandidateIds);
  const [toPartnerId, setToPartnerId] = useState<string>("");
  const [contextNotes, setContextNotes] = useState("");
  const [targetRoleId, setTargetRoleId] = useState<string | null>(null);
  const [candidateSearch, setCandidateSearch] = useState("");

  const filteredCandidates = candidates.filter(
    (c) =>
      `${c.first_name} ${c.last_name}`.toLowerCase().includes(candidateSearch.toLowerCase()) ||
      c.skills.some((s) => s.name.toLowerCase().includes(candidateSearch.toLowerCase()))
  );

  function toggleCandidate(id: string) {
    setSelectedCandidates((prev) =>
      prev.includes(id) ? prev.filter((cid) => cid !== id) : [...prev, id]
    );
  }

  function handleSubmit() {
    onSubmit({
      to_partner_id: toPartnerId,
      candidate_ids: selectedCandidates,
      context_notes: contextNotes,
      target_role_id: targetRoleId,
    });
    onOpenChange(false);
    // Reset
    setSelectedCandidates([]);
    setToPartnerId("");
    setContextNotes("");
    setTargetRoleId(null);
  }

  const canSubmit = selectedCandidates.length > 0 && toPartnerId && contextNotes.trim();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Send className="h-5 w-5" />
            Send Handoff
          </DialogTitle>
          <DialogDescription>
            Share candidates with another talent partner. Add context to help them understand why.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-2">
          {/* Step 1: Select candidates */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">
              1. Select Candidates
              {selectedCandidates.length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {selectedCandidates.length} selected
                </Badge>
              )}
            </Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={candidateSearch}
                onChange={(e) => setCandidateSearch(e.target.value)}
                placeholder="Search by name or skill..."
                className="pl-9"
              />
            </div>
            {/* Selected chips */}
            {selectedCandidates.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {selectedCandidates.map((id) => {
                  const c = candidates.find((c) => c.id === id);
                  return (
                    <Badge key={id} variant="secondary" className="gap-1 pr-1">
                      {c ? `${c.first_name} ${c.last_name}` : id}
                      <button
                        type="button"
                        onClick={() => toggleCandidate(id)}
                        className="ml-0.5 rounded-full p-0.5 hover:bg-slate-200"
                        aria-label="Remove candidate"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  );
                })}
              </div>
            )}
            <div className="max-h-40 overflow-y-auto rounded-md border">
              {filteredCandidates.slice(0, 15).map((c) => (
                <label
                  key={c.id}
                  className="flex items-center gap-3 px-3 py-2 hover:bg-slate-50 cursor-pointer border-b last:border-0"
                >
                  <input
                    type="checkbox"
                    checked={selectedCandidates.includes(c.id)}
                    onChange={() => toggleCandidate(c.id)}
                    className="rounded border-slate-300"
                  />
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium">
                      {c.first_name} {c.last_name}
                    </span>
                    <span className="text-xs text-muted-foreground ml-2">
                      {c.seniority} · {c.location}
                    </span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Step 2: Pick partner */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">2. Send to Partner</Label>
            <Select value={toPartnerId} onValueChange={setToPartnerId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a partner..." />
              </SelectTrigger>
              <SelectContent>
                {partners.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Step 3: Context notes */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">3. Add Context</Label>
            <Textarea
              value={contextNotes}
              onChange={(e) => setContextNotes(e.target.value)}
              placeholder="Why are you sharing these candidates? Any relevant context for the receiving partner..."
              rows={3}
            />
          </div>

          {/* Step 4 (optional): Link role */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">
              4. Link to Role <span className="text-muted-foreground font-normal">(optional)</span>
            </Label>
            <Select
              value={targetRoleId ?? "none"}
              onValueChange={(v) => setTargetRoleId(v === "none" ? null : v)}
            >
              <SelectTrigger>
                <SelectValue placeholder="No role linked" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No role linked</SelectItem>
                {roles.map((r) => (
                  <SelectItem key={r.id} value={r.id}>
                    {r.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={!canSubmit}>
            <Send className="h-4 w-4 mr-1.5" />
            Send Handoff
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

### Respond Dialog (`components/mothership/handoff-respond-dialog.tsx`)

```tsx
"use client";

import { useState } from "react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { CheckCircle2, XCircle } from "lucide-react";

interface HandoffRespondDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onRespond: (accept: boolean, notes: string) => void;
  action: "accept" | "decline";
}

export function HandoffRespondDialog({
  open, onOpenChange, onRespond, action,
}: HandoffRespondDialogProps) {
  const [notes, setNotes] = useState("");
  const isAccept = action === "accept";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isAccept ? (
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            ) : (
              <XCircle className="h-5 w-5 text-red-500" />
            )}
            {isAccept ? "Accept Handoff" : "Decline Handoff"}
          </DialogTitle>
          <DialogDescription>
            {isAccept
              ? "Accept these candidates into your pipeline. Add a note for the sender."
              : "Decline this handoff. Let the sender know why."}
          </DialogDescription>
        </DialogHeader>
        <div className="py-2">
          <Label htmlFor="respond-notes">
            {isAccept ? "Notes (optional)" : "Reason for declining"}
          </Label>
          <Textarea
            id="respond-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder={
              isAccept
                ? "Thanks! I'll review these candidates..."
                : "These don't match what I'm looking for because..."
            }
            rows={3}
            className="mt-1.5"
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            onClick={() => { onRespond(isAccept, notes); onOpenChange(false); }}
            variant={isAccept ? "default" : "destructive"}
          >
            {isAccept ? "Accept" : "Decline"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

### Attribution Timeline (`components/mothership/handoff-timeline.tsx`)

```tsx
"use client";

import { Handoff, Signal } from "@/contracts/canonical";
import { formatRelativeTime } from "@/lib/utils";
import { UserPlus, Send, CheckCircle2, XCircle, Briefcase, Star } from "lucide-react";

interface TimelineEvent {
  type: string;
  label: string;
  description: string;
  timestamp: string;
  icon: React.ElementType;
  color: string;
}

interface HandoffTimelineProps {
  handoff: Handoff;
  relatedSignals?: Signal[];
}

export function HandoffTimeline({ handoff, relatedSignals = [] }: HandoffTimelineProps) {
  const events: TimelineEvent[] = [
    {
      type: "created",
      label: "Handoff Sent",
      description: `${handoff.candidate_ids.length} candidate(s) shared`,
      timestamp: handoff.created_at,
      icon: Send,
      color: "text-blue-500 bg-blue-50",
    },
  ];

  if (handoff.responded_at) {
    events.push({
      type: handoff.status,
      label: handoff.status === "accepted" ? "Handoff Accepted" : "Handoff Declined",
      description: handoff.response_notes ?? "",
      timestamp: handoff.responded_at,
      icon: handoff.status === "accepted" ? CheckCircle2 : XCircle,
      color: handoff.status === "accepted"
        ? "text-green-500 bg-green-50"
        : "text-red-500 bg-red-50",
    });
  }

  // Add signals as timeline events
  relatedSignals.forEach((signal) => {
    let icon = Star;
    let label = signal.event_type.replace(/_/g, " ");
    let color = "text-slate-500 bg-slate-50";

    if (signal.event_type === "candidate_shortlisted") {
      icon = Star;
      label = "Candidate Shortlisted";
      color = "text-amber-500 bg-amber-50";
    } else if (signal.event_type === "placement_made") {
      icon = Briefcase;
      label = "Placement Made";
      color = "text-green-600 bg-green-50";
    } else if (signal.event_type === "intro_requested") {
      icon = UserPlus;
      label = "Intro Requested";
      color = "text-purple-500 bg-purple-50";
    }

    events.push({
      type: signal.event_type,
      label,
      description: "",
      timestamp: signal.created_at,
      icon,
      color,
    });
  });

  // Sort chronologically
  events.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  return (
    <div className="relative space-y-0">
      {events.map((event, i) => {
        const Icon = event.icon;
        return (
          <div key={i} className="flex gap-3 pb-6 last:pb-0">
            {/* Timeline line */}
            <div className="flex flex-col items-center">
              <div className={`rounded-full p-1.5 ${event.color}`}>
                <Icon className="h-3.5 w-3.5" />
              </div>
              {i < events.length - 1 && (
                <div className="w-px flex-1 bg-slate-200 mt-1" />
              )}
            </div>
            {/* Content */}
            <div className="flex-1 min-w-0 pt-0.5">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{event.label}</span>
                <span className="text-xs text-muted-foreground">
                  {formatRelativeTime(event.timestamp)}
                </span>
              </div>
              {event.description && (
                <p className="text-sm text-muted-foreground mt-0.5">{event.description}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

### Handoffs Page (`app/mothership/handoffs/page.tsx`)

```tsx
"use client";

import { useState, useEffect } from "react";
import { Handoff, HandoffCreate, Candidate, Role, User } from "@/contracts/canonical";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { HandoffCard } from "@/components/mothership/handoff-card";
import { HandoffSendDialog } from "@/components/mothership/handoff-send-dialog";
import { HandoffRespondDialog } from "@/components/mothership/handoff-respond-dialog";
import { HandoffTimeline } from "@/components/mothership/handoff-timeline";
import { Send, Inbox, SendHorizontal, ArrowLeft } from "lucide-react";

export default function HandoffsPage() {
  const [inbox, setInbox] = useState<Handoff[]>([]);
  const [outbox, setOutbox] = useState<Handoff[]>([]);
  const [loading, setLoading] = useState(true);
  const [sendOpen, setSendOpen] = useState(false);
  const [respondTarget, setRespondTarget] = useState<{ handoff: Handoff; action: "accept" | "decline" } | null>(null);
  const [detailHandoff, setDetailHandoff] = useState<Handoff | null>(null);

  // Data for send dialog
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [partners, setPartners] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const [inboxData, outboxData, candidateData, roleData] = await Promise.all([
          api.handoffs.inbox(),
          api.handoffs.outbox(),
          api.candidates.list(),
          api.roles.list(),
        ]);
        setInbox(inboxData);
        setOutbox(outboxData);
        setCandidates(candidateData);
        setRoles(roleData);
        // Partners would come from a users endpoint
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleSend(data: HandoffCreate) {
    const created = await api.handoffs.create(data);
    setOutbox([created, ...outbox]);
  }

  async function handleRespond(accept: boolean, notes: string) {
    if (!respondTarget) return;
    const updated = await api.handoffs.respond(respondTarget.handoff.id, accept, notes);
    setInbox(inbox.map((h) => (h.id === updated.id ? updated : h)));
  }

  // Detail view with timeline
  if (detailHandoff) {
    return (
      <div className="p-6 max-w-3xl">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setDetailHandoff(null)}
          className="mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-1.5" />
          Back to handoffs
        </Button>
        <h2 className="text-xl font-semibold mb-6">Handoff Details</h2>
        <HandoffTimeline handoff={detailHandoff} />
      </div>
    );
  }

  const pendingCount = inbox.filter((h) => h.status === "pending").length;

  return (
    <div className="p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Handoffs</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Share candidates with partners and track referral attribution.
          </p>
        </div>
        <Button onClick={() => setSendOpen(true)}>
          <Send className="h-4 w-4 mr-1.5" />
          Send Handoff
        </Button>
      </div>

      <Tabs defaultValue="inbox">
        <TabsList>
          <TabsTrigger value="inbox" className="gap-1.5">
            <Inbox className="h-4 w-4" />
            Inbox
            {pendingCount > 0 && (
              <span className="ml-1 rounded-full bg-blue-100 text-blue-700 px-2 py-0.5 text-xs font-medium">
                {pendingCount}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="outbox" className="gap-1.5">
            <SendHorizontal className="h-4 w-4" />
            Outbox
          </TabsTrigger>
        </TabsList>

        <TabsContent value="inbox" className="mt-4 space-y-3">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-28 rounded-lg" />
            ))
          ) : inbox.length === 0 ? (
            <div className="text-center py-12 border rounded-lg border-dashed">
              <Inbox className="h-10 w-10 mx-auto text-muted-foreground/50 mb-3" />
              <p className="text-muted-foreground">No handoffs received yet.</p>
              <p className="text-sm text-muted-foreground mt-1">
                When a partner shares candidates with you, they will appear here.
              </p>
            </div>
          ) : (
            inbox.map((handoff) => (
              <HandoffCard
                key={handoff.id}
                handoff={handoff}
                direction="inbox"
                onAccept={() => setRespondTarget({ handoff, action: "accept" })}
                onDecline={() => setRespondTarget({ handoff, action: "decline" })}
                onViewDetail={() => setDetailHandoff(handoff)}
              />
            ))
          )}
        </TabsContent>

        <TabsContent value="outbox" className="mt-4 space-y-3">
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-28 rounded-lg" />
            ))
          ) : outbox.length === 0 ? (
            <div className="text-center py-12 border rounded-lg border-dashed">
              <SendHorizontal className="h-10 w-10 mx-auto text-muted-foreground/50 mb-3" />
              <p className="text-muted-foreground">No handoffs sent yet.</p>
              <Button
                variant="outline"
                size="sm"
                className="mt-3"
                onClick={() => setSendOpen(true)}
              >
                Send your first handoff
              </Button>
            </div>
          ) : (
            outbox.map((handoff) => (
              <HandoffCard
                key={handoff.id}
                handoff={handoff}
                direction="outbox"
                onViewDetail={() => setDetailHandoff(handoff)}
              />
            ))
          )}
        </TabsContent>
      </Tabs>

      {/* Send dialog */}
      <HandoffSendDialog
        open={sendOpen}
        onOpenChange={setSendOpen}
        onSubmit={handleSend}
        candidates={candidates}
        partners={partners}
        roles={roles}
      />

      {/* Respond dialog */}
      {respondTarget && (
        <HandoffRespondDialog
          open={!!respondTarget}
          onOpenChange={() => setRespondTarget(null)}
          onRespond={handleRespond}
          action={respondTarget.action}
        />
      )}
    </div>
  );
}
```

## Outputs
- `frontend/components/mothership/handoff-status-badge.tsx` — Status badge component
- `frontend/components/mothership/handoff-card.tsx` — Handoff list item card
- `frontend/components/mothership/handoff-send-dialog.tsx` — Send handoff flow
- `frontend/components/mothership/handoff-respond-dialog.tsx` — Accept/decline dialog
- `frontend/components/mothership/handoff-timeline.tsx` — Attribution trail timeline
- `frontend/app/mothership/handoffs/page.tsx` — Main handoffs page with tabs

## Acceptance Criteria
1. Inbox tab shows received handoffs with sender info, candidate count, context notes
2. Outbox tab shows sent handoffs with status tracking
3. Pending inbox items have Accept and Decline buttons
4. Accept/decline opens a dialog with notes field
5. Send handoff dialog allows selecting candidates, picking a partner, adding context, optionally linking a role
6. Status badges show correctly for pending/accepted/declined/expired
7. Attribution timeline renders chronological events with icons
8. Loading skeletons and empty states render correctly
9. Pending count badge shows on the Inbox tab

## Handoff Notes
- **To Agent A:** Frontend expects `GET /api/handoffs/inbox`, `GET /api/handoffs/outbox`, `POST /api/handoffs`, `POST /api/handoffs/{id}/respond`. Also needs a `GET /api/users?role=talent_partner` for the partner dropdown.
- **To Task 13:** Inbox pending count should be shown on the talent partner dashboard.
- **Decision:** Using a card-based list rather than a data table for handoffs — the context notes and attribution trail benefit from more vertical space. Timeline component is reusable for other attribution trails.
