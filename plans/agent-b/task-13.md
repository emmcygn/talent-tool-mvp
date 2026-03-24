# Agent B — Task 13: Mind + Mothership — Dashboards

## Mission
Build the talent partner dashboard (Mothership) and the client dashboard (Mind) with metrics, action cards, activity feeds, pipeline health, and skeleton loading states.

## Context
Day 5. Dashboards are the first thing each persona sees after login. They must be immediately useful — surfacing what needs attention, not just displaying data. The talent partner dashboard is information-dense (Linear-inspired). The client dashboard is clean and guided (Stripe-inspired). Both use skeleton loading for a polished feel.

## Prerequisites
- B-01: Next.js scaffold, TypeScript contracts, shadcn/ui installed
- B-03: Shared UI components (candidate-card, match-card, skill-chips, confidence-badge, loading-skeleton, empty-state)
- B-04: API client
- B-05 through B-11: Core views exist so dashboard can link to them

## Checklist
- [ ] Create `MetricTile` component (`components/shared/metric-tile.tsx`)
- [ ] Create `ActionCard` component (`components/shared/action-card.tsx`)
- [ ] Create `SignalFeed` component (`components/mothership/signal-feed.tsx`)
- [ ] Create talent partner dashboard (`app/mothership/dashboard/page.tsx`)
- [ ] Create client dashboard (`app/mind/dashboard/page.tsx`)
- [ ] Implement skeleton loading states for all dashboard sections
- [ ] Wire to API client
- [ ] Commit: "Agent B Task 13: Mind + Mothership dashboards"

## Implementation Details

### Metric Tile (`components/shared/metric-tile.tsx`)

```tsx
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface MetricTileProps {
  label: string;
  value: string | number;
  subtitle?: string;
  trend?: { value: number; label: string };
  icon?: React.ReactNode;
  loading?: boolean;
  className?: string;
}

export function MetricTile({
  label, value, subtitle, trend, icon, loading, className,
}: MetricTileProps) {
  if (loading) {
    return (
      <Card className={cn("p-4", className)}>
        <Skeleton className="h-4 w-24 mb-2" />
        <Skeleton className="h-8 w-16 mb-1" />
        <Skeleton className="h-3 w-32" />
      </Card>
    );
  }

  return (
    <Card className={cn("p-4", className)}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          {label}
        </span>
        {icon && <span className="text-muted-foreground">{icon}</span>}
      </div>
      <div className="text-2xl font-bold tracking-tight">{value}</div>
      <div className="flex items-center gap-2 mt-1">
        {subtitle && (
          <span className="text-xs text-muted-foreground">{subtitle}</span>
        )}
        {trend && (
          <span className={cn(
            "flex items-center gap-0.5 text-xs font-medium",
            trend.value > 0 && "text-green-600",
            trend.value < 0 && "text-red-600",
            trend.value === 0 && "text-muted-foreground"
          )}>
            {trend.value > 0 && <TrendingUp className="h-3 w-3" />}
            {trend.value < 0 && <TrendingDown className="h-3 w-3" />}
            {trend.value === 0 && <Minus className="h-3 w-3" />}
            {trend.label}
          </span>
        )}
      </div>
    </Card>
  );
}
```

### Action Card (`components/shared/action-card.tsx`)

```tsx
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

interface ActionCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  actionLabel: string;
  onClick: () => void;
  variant?: "default" | "highlight";
}

export function ActionCard({
  icon, title, description, actionLabel, onClick, variant = "default",
}: ActionCardProps) {
  return (
    <Card className={`p-4 transition-all hover:shadow-md ${
      variant === "highlight"
        ? "border-blue-200 bg-blue-50/50"
        : ""
    }`}>
      <div className="flex items-start gap-3">
        <div className={`shrink-0 rounded-lg p-2 ${
          variant === "highlight"
            ? "bg-blue-100 text-blue-700"
            : "bg-slate-100 text-slate-600"
        }`}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold">{title}</h3>
          <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
          <Button
            variant="ghost"
            size="sm"
            className="mt-2 h-7 px-2 text-xs -ml-2"
            onClick={onClick}
          >
            {actionLabel}
            <ArrowRight className="h-3 w-3 ml-1" />
          </Button>
        </div>
      </div>
    </Card>
  );
}
```

### Signal Feed (`components/mothership/signal-feed.tsx`)

```tsx
"use client";

import { Signal } from "@/contracts/canonical";
import { Skeleton } from "@/components/ui/skeleton";
import { formatRelativeTime } from "@/lib/utils";
import {
  UserPlus, Eye, Star, XCircle, Zap, Send, CheckCircle2,
  DollarSign, Briefcase, MessageSquare,
} from "lucide-react";

const signalConfig: Record<string, {
  icon: React.ElementType;
  color: string;
  format: (s: Signal) => string;
}> = {
  candidate_ingested: {
    icon: UserPlus,
    color: "text-blue-500 bg-blue-50",
    format: () => "New candidate ingested",
  },
  candidate_viewed: {
    icon: Eye,
    color: "text-slate-500 bg-slate-50",
    format: () => "Candidate profile viewed",
  },
  candidate_shortlisted: {
    icon: Star,
    color: "text-amber-500 bg-amber-50",
    format: () => "Candidate shortlisted",
  },
  candidate_dismissed: {
    icon: XCircle,
    color: "text-red-400 bg-red-50",
    format: () => "Candidate dismissed",
  },
  match_generated: {
    icon: Zap,
    color: "text-purple-500 bg-purple-50",
    format: () => "New matches generated",
  },
  intro_requested: {
    icon: UserPlus,
    color: "text-green-500 bg-green-50",
    format: () => "Introduction requested",
  },
  handoff_sent: {
    icon: Send,
    color: "text-blue-500 bg-blue-50",
    format: () => "Handoff sent",
  },
  handoff_accepted: {
    icon: CheckCircle2,
    color: "text-green-500 bg-green-50",
    format: () => "Handoff accepted",
  },
  handoff_declined: {
    icon: XCircle,
    color: "text-red-400 bg-red-50",
    format: () => "Handoff declined",
  },
  quote_generated: {
    icon: DollarSign,
    color: "text-green-600 bg-green-50",
    format: () => "Quote generated",
  },
  placement_made: {
    icon: Briefcase,
    color: "text-green-700 bg-green-50",
    format: () => "Placement confirmed",
  },
  copilot_query: {
    icon: MessageSquare,
    color: "text-violet-500 bg-violet-50",
    format: () => "Copilot query",
  },
};

interface SignalFeedProps {
  signals: Signal[];
  loading?: boolean;
  maxItems?: number;
}

export function SignalFeed({ signals, loading, maxItems = 10 }: SignalFeedProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-8 w-8 rounded-full" />
            <div className="flex-1">
              <Skeleton className="h-4 w-48 mb-1" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (signals.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-6">
        No recent activity.
      </p>
    );
  }

  return (
    <div className="space-y-1">
      {signals.slice(0, maxItems).map((signal) => {
        const config = signalConfig[signal.event_type] || {
          icon: Zap,
          color: "text-slate-500 bg-slate-50",
          format: () => signal.event_type.replace(/_/g, " "),
        };
        const Icon = config.icon;

        return (
          <div
            key={signal.id}
            className="flex items-center gap-3 rounded-md px-2 py-2 hover:bg-slate-50 transition-colors"
          >
            <div className={`shrink-0 rounded-full p-1.5 ${config.color}`}>
              <Icon className="h-3.5 w-3.5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm truncate">{config.format(signal)}</p>
            </div>
            <span className="text-[11px] text-muted-foreground shrink-0">
              {formatRelativeTime(signal.created_at)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
```

### Talent Partner Dashboard (`app/mothership/dashboard/page.tsx`)

```tsx
"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Role, Collection, Handoff, Signal } from "@/contracts/canonical";
import { api } from "@/lib/api";
import { MetricTile } from "@/components/shared/metric-tile";
import { ActionCard } from "@/components/shared/action-card";
import { SignalFeed } from "@/components/mothership/signal-feed";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Users, Briefcase, Zap, Inbox, FolderOpen, Plus, ArrowRight,
  UserPlus, Search, BarChart3,
} from "lucide-react";

interface DashboardData {
  activeRoles: Role[];
  collections: Collection[];
  pendingHandoffs: Handoff[];
  signals: Signal[];
  stats: {
    totalCandidates: number;
    activeRoles: number;
    matchesGenerated: number;
    pendingReviews: number;
  };
}

export default function PartnerDashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [roles, collections, inbox, signals] = await Promise.all([
          api.roles.list(),
          api.collections.list(),
          api.handoffs.inbox(),
          api.signals.recent(20),
        ]);
        setData({
          activeRoles: roles.filter((r) => r.status === "active"),
          collections,
          pendingHandoffs: inbox.filter((h) => h.status === "pending"),
          signals,
          stats: {
            totalCandidates: 0, // From admin stats
            activeRoles: roles.filter((r) => r.status === "active").length,
            matchesGenerated: 0,
            pendingReviews: 0,
          },
        });
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="p-6 max-w-6xl">
      {/* Greeting */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Here is what needs your attention today.
        </p>
      </div>

      {/* Metric tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <MetricTile
          label="Candidates"
          value={data?.stats.totalCandidates ?? 0}
          subtitle="In your pipeline"
          icon={<Users className="h-4 w-4" />}
          loading={loading}
        />
        <MetricTile
          label="Active Roles"
          value={data?.stats.activeRoles ?? 0}
          subtitle="Currently sourcing"
          icon={<Briefcase className="h-4 w-4" />}
          loading={loading}
        />
        <MetricTile
          label="Matches"
          value={data?.stats.matchesGenerated ?? 0}
          subtitle="Generated this week"
          icon={<Zap className="h-4 w-4" />}
          trend={{ value: 12, label: "+12% vs last week" }}
          loading={loading}
        />
        <MetricTile
          label="Pending Reviews"
          value={data?.stats.pendingReviews ?? 0}
          subtitle="Awaiting action"
          icon={<BarChart3 className="h-4 w-4" />}
          loading={loading}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Actions + Active Roles */}
        <div className="lg:col-span-2 space-y-6">
          {/* Quick actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <ActionCard
              icon={<UserPlus className="h-5 w-5" />}
              title="Add Candidate"
              description="Upload a CV or paste a profile to add a new candidate."
              actionLabel="Add now"
              onClick={() => router.push("/mothership/candidates/new")}
            />
            <ActionCard
              icon={<Search className="h-5 w-5" />}
              title="Run Matches"
              description="Generate AI matches for your active roles."
              actionLabel="View matching"
              onClick={() => router.push("/mothership/matching")}
            />
          </div>

          {/* Active roles with match counts */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Active Roles</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs"
                  onClick={() => router.push("/mothership/matching")}
                >
                  View all <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              {loading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-14 rounded-md" />
                  ))}
                </div>
              ) : (data?.activeRoles.length ?? 0) === 0 ? (
                <p className="text-sm text-muted-foreground py-4 text-center">
                  No active roles. Match results will appear here.
                </p>
              ) : (
                <div className="space-y-2">
                  {data?.activeRoles.slice(0, 5).map((role) => (
                    <div
                      key={role.id}
                      className="flex items-center justify-between rounded-md border px-3 py-2.5 hover:bg-slate-50 cursor-pointer transition-colors"
                      onClick={() => router.push(`/mothership/matching?role=${role.id}`)}
                    >
                      <div>
                        <p className="text-sm font-medium">{role.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {role.location ?? "Remote"} · {role.seniority}
                        </p>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        <Zap className="h-3 w-3 mr-1" />
                        matches
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Handoff inbox preview */}
          {(data?.pendingHandoffs.length ?? 0) > 0 && (
            <Card className="border-amber-200 bg-amber-50/30">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Inbox className="h-4 w-4 text-amber-600" />
                    Pending Handoffs
                    <Badge className="bg-amber-100 text-amber-700 border-amber-300">
                      {data?.pendingHandoffs.length}
                    </Badge>
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs"
                    onClick={() => router.push("/mothership/handoffs")}
                  >
                    View inbox <ArrowRight className="h-3 w-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                {data?.pendingHandoffs.slice(0, 3).map((h) => (
                  <div key={h.id} className="flex items-center justify-between py-2 border-b last:border-0">
                    <div>
                      <p className="text-sm">{h.candidate_ids.length} candidates shared</p>
                      <p className="text-xs text-muted-foreground line-clamp-1">{h.context_notes}</p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      className="shrink-0"
                      onClick={() => router.push("/mothership/handoffs")}
                    >
                      Review
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right column: Activity feed */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Recent Activity</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <SignalFeed
                signals={data?.signals ?? []}
                loading={loading}
                maxItems={15}
              />
            </CardContent>
          </Card>

          {/* Collections preview */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <FolderOpen className="h-4 w-4" />
                  Collections
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs"
                  onClick={() => router.push("/mothership/collections")}
                >
                  View all <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              {loading ? (
                <div className="space-y-2">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-10 rounded-md" />
                  ))}
                </div>
              ) : (
                <div className="space-y-1.5">
                  {data?.collections.slice(0, 5).map((col) => (
                    <div
                      key={col.id}
                      className="flex items-center justify-between rounded-md px-2 py-1.5 hover:bg-slate-50 cursor-pointer transition-colors"
                      onClick={() => router.push("/mothership/collections")}
                    >
                      <span className="text-sm truncate">{col.name}</span>
                      <Badge variant="outline" className="text-[10px] shrink-0">
                        {col.candidate_count}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
```

### Client Dashboard (`app/mind/dashboard/page.tsx`)

```tsx
"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Role, Quote, Match } from "@/contracts/canonical";
import { api } from "@/lib/api";
import { MetricTile } from "@/components/shared/metric-tile";
import { ActionCard } from "@/components/shared/action-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Briefcase, Users, Clock, Trophy, Plus, ArrowRight, Sparkles,
  Zap, FileText, TrendingUp,
} from "lucide-react";

interface ClientDashboardData {
  roles: Role[];
  quotes: Quote[];
  stats: {
    candidatesInPipeline: number;
    avgTimeToShortlist: string;
    placementsThisQuarter: number;
    activeQuotes: number;
  };
  recommendations: { roleTitle: string; candidateCount: number }[];
}

export default function ClientDashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<ClientDashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [roles, quotes] = await Promise.all([
          api.roles.list(),
          api.quotes.list(),
        ]);
        setData({
          roles,
          quotes,
          stats: {
            candidatesInPipeline: 0,
            avgTimeToShortlist: "2.3 days",
            placementsThisQuarter: 0,
            activeQuotes: quotes.filter((q) => q.status === "generated" || q.status === "sent").length,
          },
          recommendations: [],
        });
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const activeRoles = data?.roles.filter((r) => r.status === "active") ?? [];

  return (
    <div className="p-6 md:p-10 max-w-5xl mx-auto">
      {/* Greeting */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">Welcome back</h1>
        <p className="text-muted-foreground mt-1">
          Here is an overview of your hiring activity.
        </p>
      </div>

      {/* Metric tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <MetricTile
          label="In Pipeline"
          value={data?.stats.candidatesInPipeline ?? 0}
          subtitle="Active candidates"
          icon={<Users className="h-4 w-4" />}
          loading={loading}
        />
        <MetricTile
          label="Avg. Time to Shortlist"
          value={data?.stats.avgTimeToShortlist ?? "—"}
          subtitle="From match to review"
          icon={<Clock className="h-4 w-4" />}
          loading={loading}
        />
        <MetricTile
          label="Placements"
          value={data?.stats.placementsThisQuarter ?? 0}
          subtitle="This quarter"
          icon={<Trophy className="h-4 w-4" />}
          loading={loading}
        />
        <MetricTile
          label="Active Quotes"
          value={data?.stats.activeQuotes ?? 0}
          subtitle="Pending review"
          icon={<FileText className="h-4 w-4" />}
          loading={loading}
        />
      </div>

      {/* Action cards — these are the key CTAs */}
      <div className="space-y-3 mb-8">
        {/* Dynamic action cards based on state */}
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-lg" />
            ))}
          </div>
        ) : (
          <>
            {/* New matches action */}
            <ActionCard
              icon={<Sparkles className="h-5 w-5" />}
              title="New candidates matched"
              description="AI has found candidates for your active roles. Review and shortlist the best fits."
              actionLabel="Review candidates"
              onClick={() => router.push("/mind/candidates")}
              variant="highlight"
            />

            {/* Quote action */}
            {(data?.stats.activeQuotes ?? 0) > 0 && (
              <ActionCard
                icon={<FileText className="h-5 w-5" />}
                title={`${data?.stats.activeQuotes} quote${(data?.stats.activeQuotes ?? 0) !== 1 ? "s" : ""} awaiting review`}
                description="Review placement fee quotes and request introductions."
                actionLabel="View quotes"
                onClick={() => router.push("/mind/quotes")}
              />
            )}

            {/* Post role action */}
            <ActionCard
              icon={<Plus className="h-5 w-5" />}
              title="Post a new role"
              description="Describe what you are looking for and AI will start matching candidates immediately."
              actionLabel="Post role"
              onClick={() => router.push("/mind/roles/new")}
            />
          </>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active roles */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <Briefcase className="h-4 w-4" />
                Your Roles
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs"
                onClick={() => router.push("/mind/roles")}
              >
                View all <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            {loading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-16 rounded-md" />
                ))}
              </div>
            ) : activeRoles.length === 0 ? (
              <div className="text-center py-6">
                <p className="text-sm text-muted-foreground">No active roles.</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={() => router.push("/mind/roles/new")}
                >
                  <Plus className="h-3.5 w-3.5 mr-1" />
                  Post your first role
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                {activeRoles.map((role) => {
                  const statusColor = {
                    draft: "bg-slate-100 text-slate-600",
                    active: "bg-green-100 text-green-700",
                    paused: "bg-amber-100 text-amber-700",
                    filled: "bg-blue-100 text-blue-700",
                    closed: "bg-slate-100 text-slate-500",
                  }[role.status];

                  return (
                    <div
                      key={role.id}
                      className="flex items-center justify-between rounded-lg border p-3 hover:bg-slate-50 cursor-pointer transition-colors"
                      onClick={() => router.push(`/mind/candidates?role=${role.id}`)}
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{role.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {role.location ?? "Remote"} · {role.remote_policy}
                        </p>
                      </div>
                      <Badge className={`text-[10px] ${statusColor}`}>
                        {role.status}
                      </Badge>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recommendations */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Recommended for You
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {loading ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-14 rounded-md" />
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                <div className="rounded-lg border border-dashed p-4 text-center">
                  <Sparkles className="h-8 w-8 mx-auto text-muted-foreground/50 mb-2" />
                  <p className="text-sm text-muted-foreground">
                    Recommendations will appear here based on your hiring patterns and our talent pool.
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quote status */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Recent Quotes
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs"
                onClick={() => router.push("/mind/quotes")}
              >
                View all <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 2 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 rounded-md" />
                ))}
              </div>
            ) : (data?.quotes.length ?? 0) === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">
                No quotes yet. Request an introduction to see quotes here.
              </p>
            ) : (
              <div className="space-y-2">
                {data?.quotes.slice(0, 4).map((q) => {
                  const statusStyle = {
                    generated: "text-blue-700 bg-blue-50",
                    sent: "text-amber-700 bg-amber-50",
                    accepted: "text-green-700 bg-green-50",
                    declined: "text-red-700 bg-red-50",
                    expired: "text-slate-500 bg-slate-50",
                  }[q.status];

                  return (
                    <div
                      key={q.id}
                      className="flex items-center justify-between rounded-md border px-3 py-2.5"
                    >
                      <span className="text-sm">Quote for candidate</span>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-medium">
                          {new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" }).format(q.final_fee)}
                        </span>
                        <Badge className={`text-[10px] ${statusStyle}`}>
                          {q.status}
                        </Badge>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

## Outputs
- `frontend/components/shared/metric-tile.tsx` — Metric display tile with trend
- `frontend/components/shared/action-card.tsx` — CTA action card
- `frontend/components/mothership/signal-feed.tsx` — Activity feed component
- `frontend/app/mothership/dashboard/page.tsx` — Talent partner dashboard
- `frontend/app/mind/dashboard/page.tsx` — Client dashboard

## Acceptance Criteria
1. Talent partner dashboard shows: metric tiles, quick actions, active roles with match badges, handoff inbox preview, activity feed, collections preview
2. Client dashboard shows: metric tiles, action cards with clear CTAs, active roles with status, quote status, recommendations section
3. All sections have skeleton loading states (not spinners)
4. Action cards link to correct pages (candidates, quotes, roles, etc.)
5. Handoff inbox preview highlights pending count with amber accent
6. Signal feed shows icons and formatted labels for each event type
7. Empty states display helpful messages
8. Dashboards are responsive (2-column on desktop, single on mobile)

## Handoff Notes
- **To Agent A:** Client dashboard needs a stats endpoint returning `candidatesInPipeline`, `avgTimeToShortlist`, `placementsThisQuarter`. Partner dashboard needs similar aggregate stats. These may come from signal analytics.
- **To Task 16:** Dashboards are the first impression — priority for visual QA. Ensure skeleton loading durations feel natural. Dark mode support needed.
- **Decision:** Client dashboard uses larger spacing and text (premium feel). Partner dashboard is more information-dense (power user). Metric tiles use a consistent pattern across both. Recommendations section starts as an empty state placeholder — will populate from signal-powered suggestions when Agent A delivers that endpoint.
