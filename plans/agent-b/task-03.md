# Agent B — Task 03: Shared UI Components (Batch 1)

## Mission
Build the core reusable UI components used across Mind and Mothership: candidate-card, match-card, skill-chips, confidence-badge, loading-skeleton, empty-state, data-table, and notification-toast. All with full TypeScript props interfaces.

## Context
Day 2. These components are the building blocks for every page in the app. They must be polished, accessible, and consistent with the design direction (Linear + Notion + Stripe). Every subsequent task depends on these components existing.

## Prerequisites
- Agent B Task 01 complete (shadcn/ui installed, canonical types, utils with `cn()`, `confidenceColor()`, `skillMatchColor()`)
- Agent B Task 02 complete (layouts exist to visually test components)

## Checklist
- [ ] Create `components/shared/candidate-card.tsx` — name, skills, location, seniority, availability
- [ ] Create `components/shared/match-card.tsx` — extends candidate info with explanation, skill chips, confidence badge, action buttons
- [ ] Create `components/shared/skill-chips.tsx` — green/amber/grey for matched/partial/missing
- [ ] Create `components/shared/confidence-badge.tsx` — Strong/Good/Possible with colors
- [ ] Create `components/shared/loading-skeleton.tsx` — card-shaped and table-shaped skeletons
- [ ] Create `components/shared/empty-state.tsx` — icon + message + optional CTA
- [ ] Create `components/shared/data-table.tsx` — sortable, filterable, with inline actions
- [ ] Create `components/shared/notification-toast.tsx` — wrapper around shadcn toast with preset variants
- [ ] Verify: all components render without errors, TypeScript compiles clean
- [ ] Commit: "Agent B Task 03: Shared UI components batch 1"

## Implementation Details

### Candidate Card (`components/shared/candidate-card.tsx`)

```tsx
"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { MapPin, Clock, Briefcase } from "lucide-react";
import type { Candidate, CandidateAnonymized, SeniorityLevel, AvailabilityStatus } from "@/contracts/canonical";
import { cn } from "@/lib/utils";

interface CandidateCardProps {
  candidate: Candidate | CandidateAnonymized;
  anonymized?: boolean;
  isPoolCandidate?: boolean;
  onClick?: () => void;
  className?: string;
}

const SENIORITY_LABELS: Record<SeniorityLevel, string> = {
  junior: "Junior",
  mid: "Mid-level",
  senior: "Senior",
  lead: "Lead",
  principal: "Principal",
};

const AVAILABILITY_LABELS: Record<AvailabilityStatus, string> = {
  immediate: "Available now",
  "1_month": "1 month notice",
  "3_months": "3 months notice",
  not_looking: "Not looking",
};

const AVAILABILITY_COLORS: Record<AvailabilityStatus, string> = {
  immediate: "text-green-600",
  "1_month": "text-amber-600",
  "3_months": "text-slate-500",
  not_looking: "text-slate-400",
};

export function CandidateCard({
  candidate,
  anonymized = false,
  isPoolCandidate = false,
  onClick,
  className,
}: CandidateCardProps) {
  const displayName = anonymized && "last_initial" in candidate
    ? `${candidate.first_name} ${candidate.last_initial}.`
    : "last_name" in candidate
      ? `${candidate.first_name} ${candidate.last_name}`
      : candidate.first_name;

  const initials = candidate.first_name.charAt(0).toUpperCase();

  return (
    <Card
      className={cn(
        "transition-all hover:shadow-md",
        onClick && "cursor-pointer",
        className
      )}
      onClick={onClick}
    >
      <CardHeader className="flex flex-row items-start gap-4 pb-3">
        <Avatar className="h-10 w-10">
          <AvatarFallback className="bg-slate-100 text-sm font-medium">
            {initials}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-slate-900 truncate">{displayName}</h3>
            {isPoolCandidate && (
              <Badge variant="secondary" className="bg-blue-50 text-blue-700 text-xs shrink-0">
                Pre-vetted
              </Badge>
            )}
          </div>
          {candidate.seniority && (
            <p className="text-sm text-slate-500">{SENIORITY_LABELS[candidate.seniority]}</p>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pt-0">
        {/* Meta Row */}
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
          {candidate.location && (
            <span className="flex items-center gap-1 text-slate-500">
              <MapPin className="h-3.5 w-3.5" />
              {candidate.location}
            </span>
          )}
          {candidate.availability && (
            <span className={cn("flex items-center gap-1", AVAILABILITY_COLORS[candidate.availability])}>
              <Clock className="h-3.5 w-3.5" />
              {AVAILABILITY_LABELS[candidate.availability]}
            </span>
          )}
          {candidate.industries.length > 0 && (
            <span className="flex items-center gap-1 text-slate-500">
              <Briefcase className="h-3.5 w-3.5" />
              {candidate.industries.slice(0, 2).join(", ")}
            </span>
          )}
        </div>

        {/* Top Skills */}
        <div className="flex flex-wrap gap-1.5">
          {candidate.skills.slice(0, 5).map((skill) => (
            <Badge key={skill.name} variant="outline" className="text-xs font-normal">
              {skill.name}
              {skill.years && <span className="ml-1 text-slate-400">{skill.years}y</span>}
            </Badge>
          ))}
          {candidate.skills.length > 5 && (
            <Badge variant="outline" className="text-xs font-normal text-slate-400">
              +{candidate.skills.length - 5}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

### Match Card (`components/shared/match-card.tsx`)

```tsx
"use client";

import { Card, CardContent, CardHeader, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { MapPin, Clock, Heart, X, Send, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { SkillChips } from "./skill-chips";
import { ConfidenceBadge } from "./confidence-badge";
import type { Match, Candidate, CandidateAnonymized, SkillMatch } from "@/contracts/canonical";
import { cn } from "@/lib/utils";

interface MatchCardProps {
  match: Match;
  candidate: Candidate | CandidateAnonymized;
  anonymized?: boolean;
  isPoolCandidate?: boolean;
  onShortlist?: (matchId: string) => void;
  onDismiss?: (matchId: string) => void;
  onRequestIntro?: (matchId: string) => void;
  onAddToCollection?: (matchId: string) => void;
  expandable?: boolean;
  className?: string;
}

export function MatchCard({
  match,
  candidate,
  anonymized = false,
  isPoolCandidate = false,
  onShortlist,
  onDismiss,
  onRequestIntro,
  onAddToCollection,
  expandable = true,
  className,
}: MatchCardProps) {
  const [expanded, setExpanded] = useState(false);

  const displayName = anonymized && "last_initial" in candidate
    ? `${candidate.first_name} ${candidate.last_initial}.`
    : "last_name" in candidate
      ? `${candidate.first_name} ${candidate.last_name}`
      : candidate.first_name;

  return (
    <Card className={cn("transition-all", className)}>
      <CardHeader className="flex flex-row items-start gap-4 pb-3">
        <Avatar className="h-10 w-10">
          <AvatarFallback className="bg-slate-100 text-sm font-medium">
            {candidate.first_name.charAt(0)}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-slate-900 truncate">{displayName}</h3>
            <ConfidenceBadge confidence={match.confidence} />
            {isPoolCandidate && (
              <Badge variant="secondary" className="bg-blue-50 text-blue-700 text-xs">
                Pre-vetted
              </Badge>
            )}
          </div>
          {candidate.seniority && (
            <p className="text-sm text-slate-500 capitalize">{candidate.seniority}</p>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pt-0">
        {/* Match Explanation */}
        <p className="text-sm text-slate-600 leading-relaxed">{match.explanation}</p>

        {/* Skill Chips */}
        <SkillChips skills={match.skill_overlap} />

        {/* Meta Row */}
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-500">
          {candidate.location && (
            <span className="flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {candidate.location}
            </span>
          )}
          {candidate.availability && (
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {candidate.availability.replace("_", " ")}
            </span>
          )}
        </div>

        {/* Expanded Detail — scoring breakdown */}
        {expanded && (
          <div className="mt-4 space-y-3 rounded-lg bg-slate-50 p-4">
            {/* Strengths */}
            {match.strengths.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-green-700 mb-1">
                  Strengths
                </h4>
                <ul className="space-y-1">
                  {match.strengths.map((s, i) => (
                    <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-green-400 shrink-0" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Gaps */}
            {match.gaps.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-700 mb-1">
                  Gaps
                </h4>
                <ul className="space-y-1">
                  {match.gaps.map((g, i) => (
                    <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-amber-400 shrink-0" />
                      {g}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Recommendation */}
            <p className="text-sm font-medium text-slate-700 border-t border-slate-200 pt-3">
              {match.recommendation}
            </p>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex items-center justify-between pt-0">
        {/* Action Buttons */}
        <div className="flex gap-2">
          {onShortlist && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onShortlist(match.id)}
              className="gap-1.5 text-pink-600 hover:text-pink-700 hover:bg-pink-50"
            >
              <Heart className="h-3.5 w-3.5" />
              Shortlist
            </Button>
          )}
          {onDismiss && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDismiss(match.id)}
              className="gap-1.5 text-slate-500 hover:text-slate-700"
            >
              <X className="h-3.5 w-3.5" />
              Dismiss
            </Button>
          )}
          {onRequestIntro && (
            <Button
              variant="default"
              size="sm"
              onClick={() => onRequestIntro(match.id)}
              className="gap-1.5"
            >
              <Send className="h-3.5 w-3.5" />
              Request Intro
            </Button>
          )}
        </div>

        {/* Expand/Collapse */}
        {expandable && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="gap-1 text-slate-400"
          >
            {expanded ? (
              <>Less <ChevronUp className="h-3.5 w-3.5" /></>
            ) : (
              <>More <ChevronDown className="h-3.5 w-3.5" /></>
            )}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
```

### Skill Chips (`components/shared/skill-chips.tsx`)

```tsx
import { Badge } from "@/components/ui/badge";
import type { SkillMatch } from "@/contracts/canonical";
import { cn } from "@/lib/utils";
import { skillMatchColor } from "@/lib/utils";

interface SkillChipsProps {
  skills: SkillMatch[];
  maxDisplay?: number;
  className?: string;
}

export function SkillChips({ skills, maxDisplay = 8, className }: SkillChipsProps) {
  // Sort: matched first, then partial, then missing
  const sorted = [...skills].sort((a, b) => {
    const order = { matched: 0, partial: 1, missing: 2 };
    return order[a.status] - order[b.status];
  });

  const displayed = sorted.slice(0, maxDisplay);
  const remaining = sorted.length - maxDisplay;

  return (
    <div className={cn("flex flex-wrap gap-1.5", className)}>
      {displayed.map((skill) => (
        <Badge
          key={skill.skill_name}
          variant="outline"
          className={cn("text-xs font-normal border", skillMatchColor(skill.status))}
        >
          {skill.skill_name}
          {skill.candidate_years != null && (
            <span className="ml-1 opacity-70">{skill.candidate_years}y</span>
          )}
          {skill.required_years != null && (
            <span className="ml-0.5 opacity-50">/{skill.required_years}y</span>
          )}
        </Badge>
      ))}
      {remaining > 0 && (
        <Badge variant="outline" className="text-xs font-normal text-slate-400 border-slate-200">
          +{remaining} more
        </Badge>
      )}
    </div>
  );
}
```

### Confidence Badge (`components/shared/confidence-badge.tsx`)

```tsx
import { Badge } from "@/components/ui/badge";
import type { ConfidenceLevel } from "@/contracts/canonical";
import { cn } from "@/lib/utils";
import { confidenceColor } from "@/lib/utils";

interface ConfidenceBadgeProps {
  confidence: ConfidenceLevel;
  className?: string;
}

const LABELS: Record<ConfidenceLevel, string> = {
  strong: "Strong Match",
  good: "Good Match",
  possible: "Worth Considering",
};

export function ConfidenceBadge({ confidence, className }: ConfidenceBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "text-xs font-medium border",
        confidenceColor(confidence),
        className
      )}
    >
      {LABELS[confidence]}
    </Badge>
  );
}
```

### Loading Skeleton (`components/shared/loading-skeleton.tsx`)

```tsx
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface LoadingSkeletonProps {
  variant: "card" | "table" | "list-item";
  count?: number;
  className?: string;
}

function CardSkeleton() {
  return (
    <div className="rounded-lg border border-slate-200 p-6 space-y-4">
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-10 rounded-full" />
        <div className="space-y-2 flex-1">
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-3 w-1/5" />
        </div>
        <Skeleton className="h-6 w-24 rounded-full" />
      </div>
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-4/5" />
      <div className="flex gap-2">
        <Skeleton className="h-6 w-16 rounded-full" />
        <Skeleton className="h-6 w-20 rounded-full" />
        <Skeleton className="h-6 w-14 rounded-full" />
        <Skeleton className="h-6 w-18 rounded-full" />
      </div>
      <div className="flex gap-2 pt-2">
        <Skeleton className="h-8 w-24 rounded-md" />
        <Skeleton className="h-8 w-20 rounded-md" />
      </div>
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="rounded-lg border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="flex gap-4 bg-slate-50 px-4 py-3 border-b">
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-4 w-1/6" />
        <Skeleton className="h-4 w-1/6" />
        <Skeleton className="h-4 w-1/6" />
        <Skeleton className="h-4 w-1/8" />
      </div>
      {/* Rows */}
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3 border-b last:border-0">
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-4 w-1/6" />
          <Skeleton className="h-4 w-1/6" />
          <Skeleton className="h-4 w-1/6" />
          <Skeleton className="h-8 w-16 rounded-md" />
        </div>
      ))}
    </div>
  );
}

function ListItemSkeleton() {
  return (
    <div className="flex items-center gap-4 py-3">
      <Skeleton className="h-8 w-8 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-3 w-1/2" />
      </div>
      <Skeleton className="h-6 w-20 rounded-full" />
    </div>
  );
}

export function LoadingSkeleton({ variant, count = 1, className }: LoadingSkeletonProps) {
  const Component = {
    card: CardSkeleton,
    table: TableSkeleton,
    "list-item": ListItemSkeleton,
  }[variant];

  return (
    <div className={cn("space-y-4", className)}>
      {Array.from({ length: count }).map((_, i) => (
        <Component key={i} />
      ))}
    </div>
  );
}
```

### Empty State (`components/shared/empty-state.tsx`)

```tsx
import { Button } from "@/components/ui/button";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center py-16 px-4 text-center", className)}>
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 mb-4">
        <Icon className="h-8 w-8 text-slate-400" />
      </div>
      <h3 className="text-lg font-semibold text-slate-900 mb-1">{title}</h3>
      <p className="text-sm text-slate-500 max-w-sm mb-6">{description}</p>
      {actionLabel && onAction && (
        <Button onClick={onAction}>{actionLabel}</Button>
      )}
    </div>
  );
}
```

### Data Table (`components/shared/data-table.tsx`)

```tsx
"use client";

import { useState, useMemo, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ArrowUpDown, ArrowUp, ArrowDown, Search, MoreHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  header: string;
  sortable?: boolean;
  render: (item: T) => ReactNode;
  className?: string;
}

export interface RowAction<T> {
  label: string;
  onClick: (item: T) => void;
  icon?: ReactNode;
  destructive?: boolean;
}

interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  actions?: RowAction<T>[];
  searchable?: boolean;
  searchPlaceholder?: string;
  searchFn?: (item: T, query: string) => boolean;
  keyExtractor: (item: T) => string;
  emptyMessage?: string;
  className?: string;
}

type SortDirection = "asc" | "desc" | null;

export function DataTable<T>({
  data,
  columns,
  actions,
  searchable = false,
  searchPlaceholder = "Search...",
  searchFn,
  keyExtractor,
  emptyMessage = "No results found",
  className,
}: DataTableProps<T>) {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      if (sortDirection === "asc") setSortDirection("desc");
      else if (sortDirection === "desc") { setSortKey(null); setSortDirection(null); }
      else setSortDirection("asc");
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  };

  const filteredData = useMemo(() => {
    let result = data;
    if (searchable && searchQuery && searchFn) {
      result = result.filter((item) => searchFn(item, searchQuery));
    }
    return result;
  }, [data, searchQuery, searchable, searchFn]);

  return (
    <div className={cn("space-y-4", className)}>
      {/* Search Bar */}
      {searchable && (
        <div className="relative max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={searchPlaceholder}
            className="pl-9"
          />
        </div>
      )}

      {/* Table */}
      <div className="rounded-lg border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    "px-4 py-3 text-left font-medium text-slate-500",
                    col.sortable && "cursor-pointer select-none hover:text-slate-700",
                    col.className
                  )}
                  onClick={() => col.sortable && handleSort(col.key)}
                >
                  <div className="flex items-center gap-1">
                    {col.header}
                    {col.sortable && (
                      sortKey === col.key ? (
                        sortDirection === "asc" ? <ArrowUp className="h-3.5 w-3.5" /> : <ArrowDown className="h-3.5 w-3.5" />
                      ) : (
                        <ArrowUpDown className="h-3.5 w-3.5 opacity-30" />
                      )
                    )}
                  </div>
                </th>
              ))}
              {actions && actions.length > 0 && (
                <th className="px-4 py-3 text-right font-medium text-slate-500 w-12" />
              )}
            </tr>
          </thead>
          <tbody>
            {filteredData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (actions ? 1 : 0)}
                  className="px-4 py-12 text-center text-slate-400"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              filteredData.map((item) => (
                <tr
                  key={keyExtractor(item)}
                  className="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors"
                >
                  {columns.map((col) => (
                    <td key={col.key} className={cn("px-4 py-3", col.className)}>
                      {col.render(item)}
                    </td>
                  ))}
                  {actions && actions.length > 0 && (
                    <td className="px-4 py-3 text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          {actions.map((action) => (
                            <DropdownMenuItem
                              key={action.label}
                              onClick={() => action.onClick(item)}
                              className={cn(action.destructive && "text-red-600")}
                            >
                              {action.icon && <span className="mr-2">{action.icon}</span>}
                              {action.label}
                            </DropdownMenuItem>
                          ))}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

### Notification Toast (`components/shared/notification-toast.tsx`)

```tsx
"use client";

import { useToast } from "@/hooks/use-toast";
import { CheckCircle2, AlertCircle, Info, AlertTriangle } from "lucide-react";

type ToastVariant = "success" | "error" | "info" | "warning";

interface NotifyOptions {
  title: string;
  description?: string;
  variant?: ToastVariant;
}

const VARIANT_ICONS = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
};

export function useNotify() {
  const { toast } = useToast();

  return ({ title, description, variant = "info" }: NotifyOptions) => {
    const Icon = VARIANT_ICONS[variant];

    toast({
      title,
      description: description ? (
        <div className="flex items-start gap-2">
          <Icon className="h-4 w-4 mt-0.5 shrink-0" />
          <span>{description}</span>
        </div>
      ) : undefined,
      variant: variant === "error" ? "destructive" : "default",
    });
  };
}
```

## Outputs
- `components/shared/candidate-card.tsx` — candidate display card with name, skills, location, seniority, availability
- `components/shared/match-card.tsx` — match result card with explanation, skill chips, confidence badge, expandable detail, action buttons
- `components/shared/skill-chips.tsx` — color-coded skill match badges (green/amber/grey)
- `components/shared/confidence-badge.tsx` — Strong Match / Good Match / Worth Considering badge
- `components/shared/loading-skeleton.tsx` — card, table, and list-item skeleton loaders
- `components/shared/empty-state.tsx` — empty state with icon, message, and CTA
- `components/shared/data-table.tsx` — sortable, filterable data table with inline row actions
- `components/shared/notification-toast.tsx` — typed toast notification hook

## Acceptance Criteria
1. `npm run build` passes with no errors
2. All components accept typed props — no `any` types
3. `CandidateCard` renders candidate name, skills (max 5 + overflow badge), location, seniority, availability
4. `MatchCard` shows explanation text, skill chips, confidence badge, and action buttons (shortlist, dismiss, request intro)
5. `MatchCard` expands to show strengths, gaps, and recommendation
6. `SkillChips` colors: green for matched, amber for partial, grey for missing
7. `ConfidenceBadge` shows "Strong Match" (green), "Good Match" (amber), "Worth Considering" (grey)
8. `LoadingSkeleton` renders card-shaped, table-shaped, and list-item-shaped skeleton placeholders
9. `EmptyState` renders centered icon + title + description + optional action button
10. `DataTable` supports column sorting, search filtering, and inline row action menu

## Handoff Notes
- **To all subsequent tasks:** Import shared components from `@/components/shared/*`. Use `LoadingSkeleton` for loading states, `EmptyState` for empty views.
- **To Task 07 (Mind candidates):** `MatchCard` supports `anonymized` prop and `isPoolCandidate` prop. Pass `onShortlist`, `onDismiss`, `onRequestIntro` callbacks for client actions.
- **To Task 08 (Mothership matching):** `MatchCard` supports `onAddToCollection` callback and expandable scoring detail. For talent partner view, pass `anonymized={false}`.
- **Decision:** `DataTable` sorts client-side for now. Server-side pagination/sort can be added later when data volumes justify it. Skill chips sort order: matched first, then partial, then missing.
