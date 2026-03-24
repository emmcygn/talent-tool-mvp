"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api-client";
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
                {p.handoffsSent > 0 ? `${Math.round((p.handoffsAccepted / p.handoffsSent) * 100)}%` : "\u2014"}
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

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        await Promise.all([
          apiClient.admin.stats(),
          apiClient.admin.pipelineStatus(),
        ]);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

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
    value: Math.floor(20 + ((i * 7 + 13) % 50)),
  }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <BarChart3 className="h-6 w-6" />
          Platform Analytics
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Signal-powered insights across the entire platform.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
          value={"\u00a3842k"}
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
              <CardTitle className="text-base">Candidate Pipeline Funnel</CardTitle>
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
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
