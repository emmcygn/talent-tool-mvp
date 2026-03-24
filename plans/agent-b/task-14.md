# Agent B — Task 14: Admin — Analytics + Data Quality

## Mission
Build the admin analytics page with funnel visualization, trending skills chart, partner performance table, client engagement metrics, and time-series activity chart. Build the data quality page with dedup review queue, side-by-side comparison component, and merge/keep/split actions.

## Context
Day 6. Admin views are Grafana-inspired data density with Vercel-inspired cleanliness. Analytics turns the signal layer into actionable dashboards. Data quality review is critical for maintaining trust in the system — admins review auto-merged and pending dedup candidates with a side-by-side comparison showing agreements in green and conflicts in red.

## Prerequisites
- B-01: Next.js scaffold, TypeScript contracts, shadcn/ui installed
- B-04: API client
- A-15: Admin endpoints delivering funnel data, stats, dedup review queue

## Checklist
- [ ] Create `FunnelChart` component (`components/charts/funnel-chart.tsx`) — Recharts funnel visualization
- [ ] Create `TrendingSkillsChart` component (`components/charts/trending-skills-chart.tsx`) — bar chart
- [ ] Create `TimeSeriesChart` component (`components/charts/time-series-chart.tsx`) — activity over time
- [ ] Create `PartnerPerformanceTable` component — data table with partner metrics
- [ ] Create analytics page (`app/mothership/admin/analytics/page.tsx`)
- [ ] Create `DedupComparison` component (`components/mothership/dedup-comparison.tsx`) — side-by-side
- [ ] Create `DedupReviewQueue` component — sortable list of pending reviews
- [ ] Create quality page (`app/mothership/admin/quality/page.tsx`)
- [ ] Wire to API client with loading states
- [ ] Commit: "Agent B Task 14: Admin analytics + data quality"

## Implementation Details

### Funnel Chart (`components/charts/funnel-chart.tsx`)

```tsx
"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";

interface FunnelStage {
  label: string;
  value: number;
  color: string;
}

interface FunnelChartProps {
  stages: FunnelStage[];
  className?: string;
}

export function FunnelChart({ stages, className }: FunnelChartProps) {
  const maxValue = Math.max(...stages.map((s) => s.value));

  const withDropoff = useMemo(() => {
    return stages.map((stage, i) => ({
      ...stage,
      percentage: maxValue > 0 ? (stage.value / maxValue) * 100 : 0,
      dropoff: i > 0
        ? Math.round(((stages[i - 1].value - stage.value) / stages[i - 1].value) * 100)
        : null,
    }));
  }, [stages, maxValue]);

  return (
    <div className={cn("space-y-2", className)}>
      {withDropoff.map((stage, i) => (
        <div key={stage.label}>
          <div className="flex items-center gap-3">
            {/* Bar */}
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium">{stage.label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold">{stage.value.toLocaleString()}</span>
                  {stage.dropoff !== null && stage.dropoff > 0 && (
                    <span className="text-xs text-red-500">-{stage.dropoff}%</span>
                  )}
                </div>
              </div>
              <div className="h-8 rounded-md bg-slate-100 overflow-hidden">
                <div
                  className="h-full rounded-md transition-all duration-500"
                  style={{
                    width: `${stage.percentage}%`,
                    backgroundColor: stage.color,
                  }}
                />
              </div>
            </div>
          </div>
          {/* Drop-off connector */}
          {i < withDropoff.length - 1 && (
            <div className="flex justify-center py-0.5">
              <div className="w-px h-3 bg-slate-200" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

### Trending Skills Bar Chart (`components/charts/trending-skills-chart.tsx`)

```tsx
"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

interface SkillTrend {
  skill: string;
  demand: number;
  supply: number;
}

interface TrendingSkillsChartProps {
  data: SkillTrend[];
}

const COLORS = [
  "#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe",
  "#818cf8", "#4f46e5", "#4338ca",
];

export function TrendingSkillsChart({ data }: TrendingSkillsChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ left: 80 }}>
        <XAxis type="number" tick={{ fontSize: 12 }} />
        <YAxis
          type="category"
          dataKey="skill"
          tick={{ fontSize: 12 }}
          width={80}
        />
        <Tooltip
          contentStyle={{
            fontSize: 12,
            borderRadius: 8,
            border: "1px solid #e2e8f0",
            boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
          }}
        />
        <Bar dataKey="demand" name="Demand (roles)" radius={[0, 4, 4, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
        <Bar dataKey="supply" name="Supply (candidates)" fill="#94a3b8" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

### Time Series Chart (`components/charts/time-series-chart.tsx`)

```tsx
"use client";

import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

interface TimeSeriesDataPoint {
  date: string;
  value: number;
  label?: string;
}

interface TimeSeriesChartProps {
  data: TimeSeriesDataPoint[];
  color?: string;
  height?: number;
  showGrid?: boolean;
}

export function TimeSeriesChart({
  data, color = "#6366f1", height = 200, showGrid = true,
}: TimeSeriesChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
        {showGrid && (
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        )}
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          width={40}
        />
        <Tooltip
          contentStyle={{
            fontSize: 12,
            borderRadius: 8,
            border: "1px solid #e2e8f0",
            boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
          }}
        />
        <defs>
          <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.2} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          fill={`url(#gradient-${color})`}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
```

### Partner Performance Table

```tsx
// Inline in analytics page or separate component

interface PartnerPerformance {
  id: string;
  name: string;
  candidatesAdded: number;
  handoffsSent: number;
  handoffsAccepted: number;
  avgResponseTime: string;
  placementRate: number;
}

function PartnerPerformanceTable({ data }: { data: PartnerPerformance[] }) {
  return (
    <div className="rounded-md border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-slate-50">
            <th className="text-left font-medium px-4 py-2.5">Partner</th>
            <th className="text-right font-medium px-4 py-2.5">Candidates</th>
            <th className="text-right font-medium px-4 py-2.5">Handoffs</th>
            <th className="text-right font-medium px-4 py-2.5">Accept Rate</th>
            <th className="text-right font-medium px-4 py-2.5">Avg Response</th>
            <th className="text-right font-medium px-4 py-2.5">Placement %</th>
          </tr>
        </thead>
        <tbody>
          {data.map((p) => (
            <tr key={p.id} className="border-b last:border-0 hover:bg-slate-50 transition-colors">
              <td className="px-4 py-2.5 font-medium">{p.name}</td>
              <td className="px-4 py-2.5 text-right">{p.candidatesAdded}</td>
              <td className="px-4 py-2.5 text-right">
                {p.handoffsSent}
                <span className="text-muted-foreground ml-1">sent</span>
              </td>
              <td className="px-4 py-2.5 text-right">
                {p.handoffsSent > 0
                  ? `${Math.round((p.handoffsAccepted / p.handoffsSent) * 100)}%`
                  : "—"}
              </td>
              <td className="px-4 py-2.5 text-right text-muted-foreground">
                {p.avgResponseTime}
              </td>
              <td className="px-4 py-2.5 text-right">
                <span className={p.placementRate > 10 ? "text-green-600 font-medium" : ""}>
                  {p.placementRate}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Analytics Page (`app/mothership/admin/analytics/page.tsx`)

```tsx
"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricTile } from "@/components/shared/metric-tile";
import { FunnelChart } from "@/components/charts/funnel-chart";
import { TrendingSkillsChart } from "@/components/charts/trending-skills-chart";
import { TimeSeriesChart } from "@/components/charts/time-series-chart";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Users, Briefcase, Zap, DollarSign, BarChart3, TrendingUp,
  Activity, UserCheck,
} from "lucide-react";

export default function AnalyticsPage() {
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [funnelData, setFunnelData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [statsData, funnel] = await Promise.all([
          api.admin.stats(),
          api.admin.funnelData(),
        ]);
        setStats(statsData);
        setFunnelData(funnel);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Mock data for charts (will be replaced by API data)
  const funnelStages = [
    { label: "Ingested", value: 847, color: "#6366f1" },
    { label: "Deduplicated", value: 623, color: "#8b5cf6" },
    { label: "Enriched", value: 601, color: "#a78bfa" },
    { label: "Matched", value: 412, color: "#c084fc" },
    { label: "Shortlisted", value: 156, color: "#e879f9" },
    { label: "Intro Requested", value: 89, color: "#f472b6" },
    { label: "Placed", value: 23, color: "#10b981" },
  ];

  const trendingSkills = [
    { skill: "Python", demand: 45, supply: 62 },
    { skill: "React", demand: 38, supply: 48 },
    { skill: "TypeScript", demand: 34, supply: 41 },
    { skill: "AWS", demand: 28, supply: 35 },
    { skill: "Kubernetes", demand: 22, supply: 18 },
    { skill: "Machine Learning", demand: 19, supply: 12 },
    { skill: "Go", demand: 15, supply: 9 },
    { skill: "Rust", demand: 8, supply: 4 },
  ];

  const activityTimeSeries = Array.from({ length: 30 }, (_, i) => ({
    date: `Mar ${i + 1}`,
    value: Math.floor(Math.random() * 50) + 20,
  }));

  return (
    <div className="p-6 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <BarChart3 className="h-6 w-6" />
          Platform Analytics
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Signal-powered insights across the entire platform.
        </p>
      </div>

      {/* Top-level metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <MetricTile
          label="Total Candidates"
          value={847}
          icon={<Users className="h-4 w-4" />}
          trend={{ value: 15, label: "+15% this month" }}
          loading={loading}
        />
        <MetricTile
          label="Active Roles"
          value={34}
          icon={<Briefcase className="h-4 w-4" />}
          loading={loading}
        />
        <MetricTile
          label="Matches Generated"
          value="2.4k"
          icon={<Zap className="h-4 w-4" />}
          trend={{ value: 8, label: "+8% vs last month" }}
          loading={loading}
        />
        <MetricTile
          label="Revenue Pipeline"
          value="\u00a3842k"
          icon={<DollarSign className="h-4 w-4" />}
          loading={loading}
        />
      </div>

      <Tabs defaultValue="funnel" className="space-y-6">
        <TabsList>
          <TabsTrigger value="funnel">Pipeline Funnel</TabsTrigger>
          <TabsTrigger value="skills">Trending Skills</TabsTrigger>
          <TabsTrigger value="partners">Partner Performance</TabsTrigger>
          <TabsTrigger value="engagement">Client Engagement</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="funnel">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                Candidate Pipeline Funnel
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  {Array.from({ length: 7 }).map((_, i) => (
                    <Skeleton key={i} className="h-10 rounded-md" />
                  ))}
                </div>
              ) : (
                <FunnelChart stages={funnelStages} />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="skills">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Most In-Demand Skills
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-[300px] rounded-md" />
              ) : (
                <TrendingSkillsChart data={trendingSkills} />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="partners">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <UserCheck className="h-4 w-4" />
                Partner Performance
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-64 rounded-md" />
              ) : (
                <PartnerPerformanceTable data={[]} />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="engagement">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Client Engagement</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <MetricTile label="Browse Frequency" value="4.2/week" subtitle="Avg per client" loading={loading} />
                <MetricTile label="Shortlist Rate" value="38%" subtitle="Of viewed candidates" loading={loading} />
                <MetricTile label="Quote Acceptance" value="67%" subtitle="Of generated quotes" loading={loading} />
                <MetricTile label="Avg Time to Hire" value="18 days" subtitle="Match to placement" loading={loading} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Platform Activity (30 days)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-[200px] rounded-md" />
              ) : (
                <TimeSeriesChart data={activityTimeSeries} />
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Inline PartnerPerformanceTable for this page
interface PartnerPerformance {
  id: string;
  name: string;
  candidatesAdded: number;
  handoffsSent: number;
  handoffsAccepted: number;
  avgResponseTime: string;
  placementRate: number;
}

function PartnerPerformanceTable({ data }: { data: PartnerPerformance[] }) {
  if (data.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        Partner performance data will appear here once signals are collected.
      </p>
    );
  }

  return (
    <div className="rounded-md border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-slate-50">
            <th className="text-left font-medium px-4 py-2.5">Partner</th>
            <th className="text-right font-medium px-4 py-2.5">Candidates</th>
            <th className="text-right font-medium px-4 py-2.5">Handoffs</th>
            <th className="text-right font-medium px-4 py-2.5">Accept Rate</th>
            <th className="text-right font-medium px-4 py-2.5">Avg Response</th>
            <th className="text-right font-medium px-4 py-2.5">Placement %</th>
          </tr>
        </thead>
        <tbody>
          {data.map((p) => (
            <tr key={p.id} className="border-b last:border-0 hover:bg-slate-50">
              <td className="px-4 py-2.5 font-medium">{p.name}</td>
              <td className="px-4 py-2.5 text-right">{p.candidatesAdded}</td>
              <td className="px-4 py-2.5 text-right">{p.handoffsSent}</td>
              <td className="px-4 py-2.5 text-right">
                {p.handoffsSent > 0 ? `${Math.round((p.handoffsAccepted / p.handoffsSent) * 100)}%` : "—"}
              </td>
              <td className="px-4 py-2.5 text-right text-muted-foreground">{p.avgResponseTime}</td>
              <td className="px-4 py-2.5 text-right font-medium">{p.placementRate}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Dedup Comparison (`components/mothership/dedup-comparison.tsx`)

```tsx
"use client";

import { Candidate } from "@/contracts/canonical";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { GitMerge, SplitSquareHorizontal, Check, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface DedupPair {
  id: string;
  candidateA: Candidate;
  candidateB: Candidate;
  confidence: number;
  matchType: "exact_email" | "fuzzy_name" | "semantic";
}

interface DedupComparisonProps {
  pair: DedupPair;
  onMerge: (keepId: string) => void;
  onKeepSeparate: () => void;
}

type FieldComparison = {
  label: string;
  valueA: string | null;
  valueB: string | null;
  status: "agree" | "conflict" | "one_missing";
};

function compareFields(a: Candidate, b: Candidate): FieldComparison[] {
  const fields: { label: string; keyA: string | null; keyB: string | null }[] = [
    { label: "Name", keyA: `${a.first_name} ${a.last_name}`, keyB: `${b.first_name} ${b.last_name}` },
    { label: "Email", keyA: a.email, keyB: b.email },
    { label: "Phone", keyA: a.phone, keyB: b.phone },
    { label: "Location", keyA: a.location, keyB: b.location },
    { label: "Seniority", keyA: a.seniority, keyB: b.seniority },
    { label: "Availability", keyA: a.availability, keyB: b.availability },
  ];

  return fields.map(({ label, keyA, keyB }) => {
    let status: "agree" | "conflict" | "one_missing";
    if (!keyA && !keyB) status = "agree";
    else if (!keyA || !keyB) status = "one_missing";
    else if (keyA.toLowerCase() === keyB.toLowerCase()) status = "agree";
    else status = "conflict";

    return { label, valueA: keyA, valueB: keyB, status };
  });
}

export function DedupComparison({ pair, onMerge, onKeepSeparate }: DedupComparisonProps) {
  const fields = compareFields(pair.candidateA, pair.candidateB);
  const conflicts = fields.filter((f) => f.status === "conflict").length;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">
            Potential Duplicate
            <Badge variant="outline" className="ml-2 text-xs">
              {Math.round(pair.confidence * 100)}% confidence
            </Badge>
            <Badge variant="secondary" className="ml-1 text-xs">
              {pair.matchType.replace("_", " ")}
            </Badge>
          </CardTitle>
          {conflicts > 0 && (
            <Badge variant="outline" className="border-red-300 text-red-700 bg-red-50 text-xs">
              {conflicts} conflict{conflicts !== 1 ? "s" : ""}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {/* Side by side comparison */}
        <div className="rounded-md border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 border-b">
                <th className="text-left font-medium px-3 py-2 w-28">Field</th>
                <th className="text-left font-medium px-3 py-2">
                  Record A
                  <span className="text-xs text-muted-foreground ml-1">
                    ({pair.candidateA.sources[0]?.adapter_name ?? "Unknown"})
                  </span>
                </th>
                <th className="text-left font-medium px-3 py-2">
                  Record B
                  <span className="text-xs text-muted-foreground ml-1">
                    ({pair.candidateB.sources[0]?.adapter_name ?? "Unknown"})
                  </span>
                </th>
              </tr>
            </thead>
            <tbody>
              {fields.map((field) => (
                <tr
                  key={field.label}
                  className={cn(
                    "border-b last:border-0",
                    field.status === "agree" && "bg-green-50/50",
                    field.status === "conflict" && "bg-red-50/50",
                    field.status === "one_missing" && "bg-amber-50/30"
                  )}
                >
                  <td className="px-3 py-2 font-medium text-muted-foreground">
                    {field.label}
                  </td>
                  <td className="px-3 py-2">
                    {field.valueA ?? <span className="text-muted-foreground italic">missing</span>}
                  </td>
                  <td className="px-3 py-2">
                    {field.valueB ?? <span className="text-muted-foreground italic">missing</span>}
                  </td>
                </tr>
              ))}
              {/* Skills comparison */}
              <tr className="border-b">
                <td className="px-3 py-2 font-medium text-muted-foreground align-top">Skills</td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap gap-1">
                    {pair.candidateA.skills.slice(0, 6).map((s) => (
                      <Badge key={s.name} variant="outline" className="text-[10px] py-0">
                        {s.name}
                      </Badge>
                    ))}
                  </div>
                </td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap gap-1">
                    {pair.candidateB.skills.slice(0, 6).map((s) => (
                      <Badge key={s.name} variant="outline" className="text-[10px] py-0">
                        {s.name}
                      </Badge>
                    ))}
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 mt-4">
          <Button onClick={() => onMerge(pair.candidateA.id)} size="sm">
            <GitMerge className="h-4 w-4 mr-1.5" />
            Merge (keep A)
          </Button>
          <Button onClick={() => onMerge(pair.candidateB.id)} size="sm" variant="outline">
            <GitMerge className="h-4 w-4 mr-1.5" />
            Merge (keep B)
          </Button>
          <Button onClick={onKeepSeparate} size="sm" variant="ghost">
            <SplitSquareHorizontal className="h-4 w-4 mr-1.5" />
            Keep Separate
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export type { DedupPair };
```

### Data Quality Page (`app/mothership/admin/quality/page.tsx`)

```tsx
"use client";

import { useState, useEffect } from "react";
import { Candidate } from "@/contracts/canonical";
import { api } from "@/lib/api";
import { DedupComparison, DedupPair } from "@/components/mothership/dedup-comparison";
import { MetricTile } from "@/components/shared/metric-tile";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  GitMerge, ShieldCheck, AlertTriangle, CheckCircle2, Filter,
} from "lucide-react";

export default function DataQualityPage() {
  const [pairs, setPairs] = useState<DedupPair[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<"confidence_desc" | "confidence_asc">("confidence_desc");

  useEffect(() => {
    async function load() {
      try {
        // Fetch dedup review queue from admin endpoint
        // const data = await api.admin.dedupQueue();
        // setPairs(data);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function handleMerge(pairId: string, keepId: string) {
    setPairs((prev) => prev.filter((p) => p.id !== pairId));
    // Call merge API
  }

  function handleKeepSeparate(pairId: string) {
    setPairs((prev) => prev.filter((p) => p.id !== pairId));
    // Call keep-separate API
  }

  function handleBulkApprove() {
    // Auto-merge all pairs with confidence > 0.9
    const highConfidence = pairs.filter((p) => p.confidence > 0.9);
    setPairs((prev) => prev.filter((p) => p.confidence <= 0.9));
    // Call bulk merge API
  }

  const sorted = [...pairs].sort((a, b) =>
    sortBy === "confidence_desc"
      ? b.confidence - a.confidence
      : a.confidence - b.confidence
  );

  const highConfCount = pairs.filter((p) => p.confidence > 0.9).length;

  return (
    <div className="p-6 max-w-5xl">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <ShieldCheck className="h-6 w-6" />
          Data Quality
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Review potential duplicates and maintain data integrity.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <MetricTile
          label="Review Queue"
          value={pairs.length}
          subtitle="Pending reviews"
          icon={<AlertTriangle className="h-4 w-4" />}
          loading={loading}
        />
        <MetricTile
          label="Auto-Merged"
          value={142}
          subtitle="This month"
          icon={<GitMerge className="h-4 w-4" />}
          loading={loading}
        />
        <MetricTile
          label="Accuracy"
          value="96.2%"
          subtitle="Auto-merge accuracy"
          icon={<CheckCircle2 className="h-4 w-4" />}
          loading={loading}
        />
        <MetricTile
          label="Top Source"
          value="Bullhorn"
          subtitle="Most duplicates"
          loading={loading}
        />
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <Select value={sortBy} onValueChange={(v) => setSortBy(v as typeof sortBy)}>
            <SelectTrigger className="w-[200px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="confidence_desc">Highest confidence first</SelectItem>
              <SelectItem value="confidence_asc">Lowest confidence first</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {highConfCount > 0 && (
          <Button onClick={handleBulkApprove} size="sm">
            <CheckCircle2 className="h-4 w-4 mr-1.5" />
            Bulk approve {highConfCount} high-confidence merge{highConfCount !== 1 ? "s" : ""}
          </Button>
        )}
      </div>

      {/* Review queue */}
      <div className="space-y-4">
        {loading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-72 rounded-lg" />
          ))
        ) : sorted.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <CheckCircle2 className="h-10 w-10 mx-auto text-green-500 mb-3" />
              <p className="text-lg font-medium">All clear</p>
              <p className="text-sm text-muted-foreground mt-1">
                No pending duplicate reviews. The system is healthy.
              </p>
            </CardContent>
          </Card>
        ) : (
          sorted.map((pair) => (
            <DedupComparison
              key={pair.id}
              pair={pair}
              onMerge={(keepId) => handleMerge(pair.id, keepId)}
              onKeepSeparate={() => handleKeepSeparate(pair.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}
```

## Outputs
- `frontend/components/charts/funnel-chart.tsx` — Pipeline funnel visualization
- `frontend/components/charts/trending-skills-chart.tsx` — Trending skills bar chart (Recharts)
- `frontend/components/charts/time-series-chart.tsx` — Time-series area chart (Recharts)
- `frontend/components/mothership/dedup-comparison.tsx` — Side-by-side dedup comparison
- `frontend/app/mothership/admin/analytics/page.tsx` — Platform analytics dashboard
- `frontend/app/mothership/admin/quality/page.tsx` — Data quality review page

## Acceptance Criteria
1. Funnel chart shows pipeline stages with counts, percentages, and drop-off rates
2. Trending skills bar chart renders with demand vs supply comparison
3. Time-series chart shows activity over 30 days with gradient fill
4. Partner performance table displays all metrics with proper formatting
5. Client engagement metrics display in tile format
6. Dedup comparison shows side-by-side fields with green for agreements, red for conflicts
7. Merge/keep separate/bulk approve actions work
8. Review queue is sortable by confidence
9. All sections have skeleton loading states
10. Empty state shows "All clear" when no pending reviews

## Handoff Notes
- **To Agent A:** Frontend expects `GET /api/admin/stats`, `GET /api/admin/funnel` (returning stage labels + counts), `GET /api/admin/dedup-queue` (returning pairs with both candidate records + confidence + match type). Need `POST /api/admin/dedup/{pairId}/merge`, `POST /api/admin/dedup/{pairId}/keep-separate`, and `POST /api/admin/dedup/bulk-approve`.
- **To Task 15:** Analytics page layout and chart components are reusable for adapter monitoring charts.
- **Decision:** Using a custom FunnelChart rather than a Recharts funnel — simpler and more visually aligned with the design direction. Recharts used for bar and time-series charts where the library adds real value. Dedup comparison uses a table layout for clear field-by-field comparison.
