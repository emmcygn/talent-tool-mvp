"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import type { Role, Quote } from "@/contracts/canonical";
import { apiClient } from "@/lib/api-client";
import { MetricTile } from "@/components/shared/metric-tile";
import { ActionCard } from "@/components/shared/action-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Briefcase, Users, Clock, Trophy, Plus, ArrowRight, Sparkles,
  FileText, TrendingUp,
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
}

export default function ClientDashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<ClientDashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [roles, quotes] = await Promise.all([
          apiClient.roles.list(),
          apiClient.quotes.list(),
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
    <div className="p-0 max-w-5xl mx-auto">
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
          value={data?.stats.avgTimeToShortlist ?? "\u2014"}
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

      {/* Action cards */}
      <div className="space-y-3 mb-8">
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-lg" />
            ))}
          </div>
        ) : (
          <>
            <ActionCard
              icon={<Sparkles className="h-5 w-5" />}
              title="New candidates matched"
              description="AI has found candidates for your active roles. Review and shortlist the best fits."
              actionLabel="Review candidates"
              onClick={() => router.push("/mind/candidates")}
              variant="highlight"
            />

            {(data?.stats.activeQuotes ?? 0) > 0 && (
              <ActionCard
                icon={<FileText className="h-5 w-5" />}
                title={`${data?.stats.activeQuotes} quote${(data?.stats.activeQuotes ?? 0) !== 1 ? "s" : ""} awaiting review`}
                description="Review placement fee quotes and request introductions."
                actionLabel="View quotes"
                onClick={() => router.push("/mind/quotes")}
              />
            )}

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
                onClick={() => router.push("/mind/roles/new")}
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
                    draft: "bg-muted text-muted-foreground",
                    active: "bg-emerald-500/10 text-emerald-400",
                    paused: "bg-amber-500/10 text-amber-400",
                    filled: "bg-blue-500/10 text-blue-400",
                    closed: "bg-muted text-muted-foreground",
                  }[role.status];

                  return (
                    <div
                      key={role.id}
                      className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted cursor-pointer transition-colors"
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
                    generated: "text-blue-400 bg-blue-500/10",
                    sent: "text-amber-400 bg-amber-500/10",
                    accepted: "text-emerald-400 bg-emerald-500/10",
                    declined: "text-red-400 bg-red-500/10",
                    expired: "text-muted-foreground bg-muted",
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
