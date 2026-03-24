# Agent B — Task 07: Mind — Candidate Browse + Matching

## Mission
Build the candidate browse page for clients in Mind: anonymized candidate cards, match explanations in plain English, skill chips, confidence badges, "Pre-vetted" badges, filter bar, shortlist/dismiss/request intro actions, and grid/list view toggle.

## Context
Day 3. This is the core value proposition for clients — viewing AI-matched candidates for their roles. Everything must be non-technical and clear. Candidates are anonymized (first name + last initial, no company names). The UI must feel premium and guide the hiring manager toward action. This is the page that converts a role posting into introductions.

## Prerequisites
- Agent B Task 01 complete (project scaffold, types)
- Agent B Task 02 complete (Mind layout)
- Agent B Task 03 complete (match-card, candidate-card, skill-chips, confidence-badge, loading-skeleton, empty-state)
- Agent B Task 04 complete (API client — `matches.forRoleAnonymized`)

## Checklist
- [ ] Create `app/mind/candidates/page.tsx` — candidate browse page with role selector
- [ ] Create `components/mind/candidate-filter-bar.tsx` — filter by skills, seniority, availability, location
- [ ] Create `components/mind/candidate-grid.tsx` — grid layout for candidate cards
- [ ] Create `components/mind/candidate-list.tsx` — list layout for candidate cards
- [ ] Create `components/mind/anonymized-match-card.tsx` — anonymized match card with client actions
- [ ] Create `components/mind/dismiss-dialog.tsx` — dismiss with optional reason
- [ ] Create `components/mind/view-toggle.tsx` — grid/list view toggle
- [ ] Wire up shortlist, dismiss, and request intro actions with API client
- [ ] Verify: page loads with mock data, filters work, view toggle works, actions fire
- [ ] Commit: "Agent B Task 07: Mind candidate browse + matching"

## Implementation Details

### Candidate Browse Page (`app/mind/candidates/page.tsx`)

```tsx
"use client";

import { useState, useEffect, useMemo } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { CandidateFilterBar, type FilterState } from "@/components/mind/candidate-filter-bar";
import { CandidateGrid } from "@/components/mind/candidate-grid";
import { CandidateList } from "@/components/mind/candidate-list";
import { ViewToggle } from "@/components/mind/view-toggle";
import { DismissDialog } from "@/components/mind/dismiss-dialog";
import { Users, Briefcase } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import type { Role, Match, CandidateAnonymized } from "@/contracts/canonical";
import { useNotify } from "@/components/shared/notification-toast";

interface MatchWithCandidate {
  match: Match;
  candidate: CandidateAnonymized;
}

export default function CandidateBrowsePage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState<string | null>(null);
  const [matches, setMatches] = useState<MatchWithCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"grid" | "list">("grid");
  const [filters, setFilters] = useState<FilterState>({
    skills: [],
    seniority: null,
    availability: null,
    location: "",
  });
  const [dismissTarget, setDismissTarget] = useState<string | null>(null);
  const notify = useNotify();

  // Load roles on mount
  useEffect(() => {
    async function loadRoles() {
      const data = await apiClient.roles.list();
      setRoles(data.filter((r) => r.status === "active"));
      if (data.length > 0) setSelectedRoleId(data[0].id);
      setLoading(false);
    }
    loadRoles();
  }, []);

  // Load matches when role changes
  useEffect(() => {
    if (!selectedRoleId) return;
    setLoading(true);
    async function loadMatches() {
      const data = await apiClient.matches.forRoleAnonymized(selectedRoleId!);
      setMatches(data);
      setLoading(false);
    }
    loadMatches();
  }, [selectedRoleId]);

  // Apply filters
  const filteredMatches = useMemo(() => {
    return matches.filter(({ match, candidate }) => {
      if (filters.seniority && candidate.seniority !== filters.seniority) return false;
      if (filters.availability && candidate.availability !== filters.availability) return false;
      if (filters.location && candidate.location &&
          !candidate.location.toLowerCase().includes(filters.location.toLowerCase())) return false;
      if (filters.skills.length > 0) {
        const candidateSkillNames = candidate.skills.map((s) => s.name.toLowerCase());
        const hasAllSkills = filters.skills.every((skill) =>
          candidateSkillNames.some((cs) => cs.includes(skill.toLowerCase()))
        );
        if (!hasAllSkills) return false;
      }
      return true;
    });
  }, [matches, filters]);

  // Sort by score descending
  const sortedMatches = useMemo(() => {
    return [...filteredMatches].sort((a, b) => b.match.overall_score - a.match.overall_score);
  }, [filteredMatches]);

  const handleShortlist = async (matchId: string) => {
    try {
      await apiClient.matches.updateStatus(matchId, "shortlisted");
      setMatches((prev) =>
        prev.map((m) =>
          m.match.id === matchId ? { ...m, match: { ...m.match, status: "shortlisted" } } : m
        )
      );
      notify({ title: "Candidate shortlisted", variant: "success" });
    } catch (err) {
      notify({ title: "Failed to shortlist", variant: "error" });
    }
  };

  const handleDismiss = async (matchId: string, reason?: string) => {
    try {
      await apiClient.matches.updateStatus(matchId, "dismissed", reason);
      setMatches((prev) =>
        prev.map((m) =>
          m.match.id === matchId ? { ...m, match: { ...m.match, status: "dismissed" } } : m
        )
      );
      setDismissTarget(null);
      notify({ title: "Candidate dismissed", variant: "info" });
    } catch (err) {
      notify({ title: "Failed to dismiss", variant: "error" });
    }
  };

  const handleRequestIntro = async (matchId: string) => {
    try {
      await apiClient.matches.updateStatus(matchId, "intro_requested");
      setMatches((prev) =>
        prev.map((m) =>
          m.match.id === matchId ? { ...m, match: { ...m.match, status: "intro_requested" } } : m
        )
      );
      notify({
        title: "Introduction requested",
        description: "We will prepare a quote and connect you shortly.",
        variant: "success",
      });
    } catch (err) {
      notify({ title: "Failed to request introduction", variant: "error" });
    }
  };

  // Collect all unique skills from current matches for filter suggestions
  const availableSkills = useMemo(() => {
    const skillSet = new Set<string>();
    matches.forEach(({ candidate }) => {
      candidate.skills.forEach((s) => skillSet.add(s.name));
    });
    return Array.from(skillSet).sort();
  }, [matches]);

  const selectedRole = roles.find((r) => r.id === selectedRoleId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Matched Candidates</h1>
          <p className="text-sm text-slate-500 mt-1">
            AI-matched candidates for your active roles
          </p>
        </div>

        {/* Role Selector */}
        <Select
          value={selectedRoleId ?? ""}
          onValueChange={setSelectedRoleId}
        >
          <SelectTrigger className="w-72">
            <SelectValue placeholder="Select a role" />
          </SelectTrigger>
          <SelectContent>
            {roles.map((role) => (
              <SelectItem key={role.id} value={role.id}>
                <div className="flex items-center gap-2">
                  <Briefcase className="h-4 w-4 text-slate-400" />
                  {role.title}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Summary bar */}
      {selectedRole && !loading && (
        <div className="flex items-center gap-4 text-sm text-slate-500">
          <span>{sortedMatches.length} candidates matched</span>
          <span className="text-slate-300">|</span>
          <span className="text-green-600">
            {sortedMatches.filter((m) => m.match.confidence === "strong").length} strong
          </span>
          <span className="text-amber-600">
            {sortedMatches.filter((m) => m.match.confidence === "good").length} good
          </span>
          <span className="text-slate-400">
            {sortedMatches.filter((m) => m.match.confidence === "possible").length} possible
          </span>
        </div>
      )}

      {/* Filter Bar + View Toggle */}
      <div className="flex items-start justify-between gap-4">
        <CandidateFilterBar
          filters={filters}
          onChange={setFilters}
          availableSkills={availableSkills}
        />
        <ViewToggle view={view} onChange={setView} />
      </div>

      {/* Content */}
      {loading ? (
        <LoadingSkeleton variant="card" count={3} />
      ) : sortedMatches.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No candidates found"
          description={
            matches.length > 0
              ? "Try adjusting your filters to see more candidates."
              : "No matches have been generated for this role yet. Check back soon."
          }
        />
      ) : view === "grid" ? (
        <CandidateGrid
          matches={sortedMatches}
          onShortlist={handleShortlist}
          onDismiss={(id) => setDismissTarget(id)}
          onRequestIntro={handleRequestIntro}
        />
      ) : (
        <CandidateList
          matches={sortedMatches}
          onShortlist={handleShortlist}
          onDismiss={(id) => setDismissTarget(id)}
          onRequestIntro={handleRequestIntro}
        />
      )}

      {/* Dismiss Dialog */}
      {dismissTarget && (
        <DismissDialog
          onConfirm={(reason) => handleDismiss(dismissTarget, reason)}
          onCancel={() => setDismissTarget(null)}
        />
      )}
    </div>
  );
}
```

### Filter Bar (`components/mind/candidate-filter-bar.tsx`)

```tsx
"use client";

import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Search, X } from "lucide-react";
import type { SeniorityLevel, AvailabilityStatus } from "@/contracts/canonical";
import { useState } from "react";

export interface FilterState {
  skills: string[];
  seniority: SeniorityLevel | null;
  availability: AvailabilityStatus | null;
  location: string;
}

interface CandidateFilterBarProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  availableSkills: string[];
}

export function CandidateFilterBar({ filters, onChange, availableSkills }: CandidateFilterBarProps) {
  const [skillInput, setSkillInput] = useState("");

  const addSkillFilter = (skill: string) => {
    if (!skill.trim() || filters.skills.includes(skill)) return;
    onChange({ ...filters, skills: [...filters.skills, skill.trim()] });
    setSkillInput("");
  };

  const removeSkillFilter = (skill: string) => {
    onChange({ ...filters, skills: filters.skills.filter((s) => s !== skill) });
  };

  const clearAll = () => {
    onChange({ skills: [], seniority: null, availability: null, location: "" });
  };

  const hasFilters = filters.skills.length > 0 || filters.seniority || filters.availability || filters.location;

  return (
    <div className="space-y-3 flex-1">
      <div className="flex items-center gap-3 flex-wrap">
        {/* Skill Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            value={skillInput}
            onChange={(e) => setSkillInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addSkillFilter(skillInput);
              }
            }}
            placeholder="Filter by skill..."
            className="pl-9 w-48"
          />
        </div>

        {/* Seniority */}
        <Select
          value={filters.seniority ?? "all"}
          onValueChange={(val) =>
            onChange({ ...filters, seniority: val === "all" ? null : (val as SeniorityLevel) })
          }
        >
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Seniority" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Any seniority</SelectItem>
            <SelectItem value="junior">Junior</SelectItem>
            <SelectItem value="mid">Mid-level</SelectItem>
            <SelectItem value="senior">Senior</SelectItem>
            <SelectItem value="lead">Lead</SelectItem>
            <SelectItem value="principal">Principal</SelectItem>
          </SelectContent>
        </Select>

        {/* Availability */}
        <Select
          value={filters.availability ?? "all"}
          onValueChange={(val) =>
            onChange({ ...filters, availability: val === "all" ? null : (val as AvailabilityStatus) })
          }
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Availability" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Any availability</SelectItem>
            <SelectItem value="immediate">Available now</SelectItem>
            <SelectItem value="1_month">1 month</SelectItem>
            <SelectItem value="3_months">3 months</SelectItem>
          </SelectContent>
        </Select>

        {/* Location */}
        <Input
          value={filters.location}
          onChange={(e) => onChange({ ...filters, location: e.target.value })}
          placeholder="Location..."
          className="w-36"
        />

        {/* Clear */}
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clearAll} className="text-slate-400 gap-1">
            <X className="h-3.5 w-3.5" />
            Clear
          </Button>
        )}
      </div>

      {/* Active Skill Filters */}
      {filters.skills.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {filters.skills.map((skill) => (
            <Badge
              key={skill}
              variant="secondary"
              className="gap-1 pr-1"
            >
              {skill}
              <button
                onClick={() => removeSkillFilter(skill)}
                className="rounded-full hover:bg-slate-300 p-0.5"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
```

### View Toggle (`components/mind/view-toggle.tsx`)

```tsx
"use client";

import { Button } from "@/components/ui/button";
import { LayoutGrid, List } from "lucide-react";
import { cn } from "@/lib/utils";

interface ViewToggleProps {
  view: "grid" | "list";
  onChange: (view: "grid" | "list") => void;
}

export function ViewToggle({ view, onChange }: ViewToggleProps) {
  return (
    <div className="flex items-center rounded-lg border border-slate-200 p-0.5">
      <Button
        variant="ghost"
        size="icon"
        className={cn("h-8 w-8 rounded-md", view === "grid" && "bg-slate-100")}
        onClick={() => onChange("grid")}
      >
        <LayoutGrid className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className={cn("h-8 w-8 rounded-md", view === "list" && "bg-slate-100")}
        onClick={() => onChange("list")}
      >
        <List className="h-4 w-4" />
      </Button>
    </div>
  );
}
```

### Candidate Grid (`components/mind/candidate-grid.tsx`)

```tsx
import { AnonymizedMatchCard } from "./anonymized-match-card";
import type { Match, CandidateAnonymized } from "@/contracts/canonical";

interface CandidateGridProps {
  matches: { match: Match; candidate: CandidateAnonymized }[];
  onShortlist: (matchId: string) => void;
  onDismiss: (matchId: string) => void;
  onRequestIntro: (matchId: string) => void;
}

export function CandidateGrid({ matches, onShortlist, onDismiss, onRequestIntro }: CandidateGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {matches.map(({ match, candidate }) => (
        <AnonymizedMatchCard
          key={match.id}
          match={match}
          candidate={candidate}
          onShortlist={onShortlist}
          onDismiss={onDismiss}
          onRequestIntro={onRequestIntro}
        />
      ))}
    </div>
  );
}
```

### Candidate List (`components/mind/candidate-list.tsx`)

```tsx
import { AnonymizedMatchCard } from "./anonymized-match-card";
import type { Match, CandidateAnonymized } from "@/contracts/canonical";

interface CandidateListProps {
  matches: { match: Match; candidate: CandidateAnonymized }[];
  onShortlist: (matchId: string) => void;
  onDismiss: (matchId: string) => void;
  onRequestIntro: (matchId: string) => void;
}

export function CandidateList({ matches, onShortlist, onDismiss, onRequestIntro }: CandidateListProps) {
  return (
    <div className="space-y-3">
      {matches.map(({ match, candidate }) => (
        <AnonymizedMatchCard
          key={match.id}
          match={match}
          candidate={candidate}
          layout="horizontal"
          onShortlist={onShortlist}
          onDismiss={onDismiss}
          onRequestIntro={onRequestIntro}
        />
      ))}
    </div>
  );
}
```

### Anonymized Match Card (`components/mind/anonymized-match-card.tsx`)

This is the client-facing match card — anonymized, non-technical, action-oriented.

```tsx
"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  MapPin, Clock, Heart, X, Send, ChevronDown, ChevronUp,
  ShieldCheck, CheckCircle2,
} from "lucide-react";
import { SkillChips } from "@/components/shared/skill-chips";
import { ConfidenceBadge } from "@/components/shared/confidence-badge";
import type { Match, CandidateAnonymized } from "@/contracts/canonical";
import { cn } from "@/lib/utils";

interface AnonymizedMatchCardProps {
  match: Match;
  candidate: CandidateAnonymized;
  layout?: "vertical" | "horizontal";
  onShortlist: (matchId: string) => void;
  onDismiss: (matchId: string) => void;
  onRequestIntro: (matchId: string) => void;
}

const AVAILABILITY_LABELS: Record<string, string> = {
  immediate: "Available now",
  "1_month": "1 month notice",
  "3_months": "3 months notice",
  not_looking: "Not looking",
};

const STATUS_BADGES: Record<string, { label: string; className: string }> = {
  shortlisted: { label: "Shortlisted", className: "bg-pink-50 text-pink-700 border-pink-200" },
  intro_requested: { label: "Intro Requested", className: "bg-blue-50 text-blue-700 border-blue-200" },
  dismissed: { label: "Dismissed", className: "bg-slate-100 text-slate-400 border-slate-200" },
};

export function AnonymizedMatchCard({
  match,
  candidate,
  layout = "vertical",
  onShortlist,
  onDismiss,
  onRequestIntro,
}: AnonymizedMatchCardProps) {
  const [expanded, setExpanded] = useState(false);

  const displayName = `${candidate.first_name} ${candidate.last_initial}.`;
  const statusBadge = STATUS_BADGES[match.status];
  const isActioned = match.status !== "generated";

  return (
    <Card className={cn(
      "transition-all",
      isActioned && match.status === "dismissed" && "opacity-60",
    )}>
      <CardHeader className="flex flex-row items-start gap-4 pb-3">
        <Avatar className="h-11 w-11">
          <AvatarFallback className="bg-gradient-to-br from-slate-100 to-slate-200 text-sm font-semibold text-slate-600">
            {candidate.first_name.charAt(0)}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-slate-900">{displayName}</h3>
            <ConfidenceBadge confidence={match.confidence} />
            {candidate.is_pool_candidate && (
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 gap-1 text-xs">
                <ShieldCheck className="h-3 w-3" />
                Pre-vetted
              </Badge>
            )}
            {statusBadge && (
              <Badge variant="outline" className={cn("gap-1 text-xs", statusBadge.className)}>
                <CheckCircle2 className="h-3 w-3" />
                {statusBadge.label}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-3 mt-1 text-sm text-slate-500">
            {candidate.seniority && (
              <span className="capitalize">{candidate.seniority}</span>
            )}
            {candidate.experience_years != null && (
              <span>{Math.round(candidate.experience_years)} years experience</span>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pt-0">
        {/* Explanation — plain English */}
        <p className="text-sm text-slate-600 leading-relaxed">{match.explanation}</p>

        {/* Skill Chips */}
        <SkillChips skills={match.skill_overlap} maxDisplay={6} />

        {/* Meta */}
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-500">
          {candidate.location && (
            <span className="flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {candidate.location}
            </span>
          )}
          {candidate.availability && (
            <span className={cn(
              "flex items-center gap-1",
              candidate.availability === "immediate" ? "text-green-600" : ""
            )}>
              <Clock className="h-3.5 w-3.5" />
              {AVAILABILITY_LABELS[candidate.availability] ?? candidate.availability}
            </span>
          )}
        </div>

        {/* Expanded — strengths + gaps */}
        {expanded && (
          <div className="mt-3 space-y-3 rounded-lg bg-slate-50 p-4 text-sm">
            {match.strengths.length > 0 && (
              <div>
                <p className="font-medium text-slate-700 mb-1">Why they are a great fit:</p>
                <ul className="space-y-1">
                  {match.strengths.map((s, i) => (
                    <li key={i} className="text-slate-600 flex items-start gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-green-400 shrink-0" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {match.gaps.length > 0 && (
              <div>
                <p className="font-medium text-slate-700 mb-1">Things to consider:</p>
                <ul className="space-y-1">
                  {match.gaps.map((g, i) => (
                    <li key={i} className="text-slate-600 flex items-start gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-amber-400 shrink-0" />
                      {g}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <p className="text-slate-700 font-medium border-t border-slate-200 pt-2">
              {match.recommendation}
            </p>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex items-center justify-between pt-0">
        <div className="flex gap-2">
          {!isActioned && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onShortlist(match.id)}
                className="gap-1.5 text-pink-600 hover:text-pink-700 hover:bg-pink-50"
              >
                <Heart className="h-3.5 w-3.5" />
                Shortlist
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDismiss(match.id)}
                className="gap-1.5 text-slate-400 hover:text-slate-600"
              >
                <X className="h-3.5 w-3.5" />
              </Button>
              <Button
                size="sm"
                onClick={() => onRequestIntro(match.id)}
                className="gap-1.5"
              >
                <Send className="h-3.5 w-3.5" />
                Request Intro
              </Button>
            </>
          )}
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded(!expanded)}
          className="gap-1 text-slate-400"
        >
          {expanded ? (
            <>Less <ChevronUp className="h-3.5 w-3.5" /></>
          ) : (
            <>Details <ChevronDown className="h-3.5 w-3.5" /></>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}
```

### Dismiss Dialog (`components/mind/dismiss-dialog.tsx`)

```tsx
"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { X } from "lucide-react";

interface DismissDialogProps {
  onConfirm: (reason?: string) => void;
  onCancel: () => void;
}

const QUICK_REASONS = [
  "Not the right skill set",
  "Seniority mismatch",
  "Location does not work",
  "Already in process with this person",
  "Budget does not align",
];

export function DismissDialog({ onConfirm, onCancel }: DismissDialogProps) {
  const [reason, setReason] = useState("");

  return (
    <Dialog open onOpenChange={(open) => !open && onCancel()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Dismiss candidate</DialogTitle>
          <DialogDescription>
            Optionally share why this candidate is not a fit. This helps us improve future matches.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Quick reasons */}
          <div className="flex flex-wrap gap-2">
            {QUICK_REASONS.map((r) => (
              <Button
                key={r}
                variant={reason === r ? "default" : "outline"}
                size="sm"
                onClick={() => setReason(reason === r ? "" : r)}
                className="text-xs"
              >
                {r}
              </Button>
            ))}
          </div>

          {/* Custom reason */}
          <Textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Or type your own reason..."
            className="min-h-[80px]"
          />

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onCancel}>Cancel</Button>
            <Button
              variant="default"
              onClick={() => onConfirm(reason || undefined)}
              className="gap-1.5"
            >
              <X className="h-3.5 w-3.5" />
              Dismiss
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

## Outputs
- `app/mind/candidates/page.tsx` — candidate browse page with role selector, filters, and match cards
- `components/mind/candidate-filter-bar.tsx` — filter bar (skills, seniority, availability, location)
- `components/mind/candidate-grid.tsx` — 2-column grid layout
- `components/mind/candidate-list.tsx` — single-column list layout
- `components/mind/anonymized-match-card.tsx` — anonymized match card with actions
- `components/mind/dismiss-dialog.tsx` — dismiss with optional reason dialog
- `components/mind/view-toggle.tsx` — grid/list view toggle

## Acceptance Criteria
1. `npm run build` passes with no errors
2. Page loads with a role selector dropdown showing active roles
3. Selecting a role loads matched candidates sorted by score (highest first)
4. Candidates are anonymized: first name + last initial only (e.g., "Priya S.")
5. No company names visible on the cards
6. Each card shows: match explanation, skill chips, confidence badge, location, availability
7. "Pre-vetted" badge appears on pool candidates (those with `is_pool_candidate === true`)
8. Filter bar filters candidates by skills, seniority, availability, and location
9. Grid view shows 2 columns on desktop, 1 on mobile
10. List view shows full-width cards stacked vertically
11. View toggle switches between grid and list
12. Shortlist action marks card as "Shortlisted" with pink badge
13. Dismiss action opens dialog with quick reasons + custom text area
14. Request Intro action marks card as "Intro Requested" with blue badge
15. Actioned cards disable their action buttons and show status badge
16. Summary bar shows count breakdown by confidence level

## Handoff Notes
- **To Task 11 (Quotes + Pipeline):** When "Request Intro" is clicked, the match status becomes `intro_requested`. The quotes page should show pending intro requests and allow the client to view/accept quotes.
- **To Agent A:** Dismissal reasons are sent via `PATCH /api/matches/:id/status` with `{ status: "dismissed", reason: "..." }`. Capture the reason in the signal layer for match quality feedback.
- **Decision:** Using client-side filtering for the PoC. All matches for a role are loaded at once and filtered in the browser. For production, add server-side filtering and pagination. Expanded card detail uses non-technical language: "Why they are a great fit" and "Things to consider" instead of "Strengths" and "Gaps".
