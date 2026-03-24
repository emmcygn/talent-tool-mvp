"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import type { Role, Collection, Handoff, Signal } from "@/contracts/canonical";
import { apiClient } from "@/lib/api-client";
import { MetricTile } from "@/components/shared/metric-tile";
import { ActionCard } from "@/components/shared/action-card";
import { SignalFeed } from "@/components/mothership/signal-feed";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Users, Briefcase, Zap, Inbox, FolderOpen, ArrowRight,
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
          apiClient.roles.list(),
          apiClient.collections.list(),
          apiClient.handoffs.inbox(),
          apiClient.signals.recent(20),
        ]);
        setData({
          activeRoles: roles.filter((r) => r.status === "active"),
          collections,
          pendingHandoffs: inbox.filter((h) => h.status === "pending"),
          signals,
          stats: {
            totalCandidates: 0,
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
    <div className="space-y-6">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Here is what needs your attention today.
        </p>
      </div>

      {/* Metric tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
