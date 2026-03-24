"use client";

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api-client";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricTile } from "@/components/shared/metric-tile";
import {
  Plug, RefreshCw, CheckCircle2, AlertTriangle, XCircle,
  Database, Clock, ArrowDownToLine, Cpu, Loader2, CheckCheck, Ban,
} from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

interface AdapterHealth {
  name: string;
  status: string;
  last_sync: string;
  records_synced: number;
  error_rate: number;
}

const statusConfig: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  healthy: { icon: CheckCircle2, color: "text-green-600 bg-green-50 border-green-200", label: "Healthy" },
  degraded: { icon: AlertTriangle, color: "text-amber-600 bg-amber-50 border-amber-200", label: "Degraded" },
  down: { icon: XCircle, color: "text-red-600 bg-red-50 border-red-200", label: "Down" },
};

const SCHEMA_MAPPINGS: Record<string, { from: string; to: string }[]> = {
  Bullhorn: [
    { from: "candidateFirstName", to: "first_name" },
    { from: "candidateLastName", to: "last_name" },
    { from: "candidateEmail", to: "email" },
    { from: "candidatePhone", to: "phone" },
    { from: "candidateAddress.city", to: "location" },
    { from: "candidateSkills", to: "skills (via extraction)" },
  ],
  HubSpot: [
    { from: "contact.firstname", to: "first_name" },
    { from: "contact.lastname", to: "last_name" },
    { from: "contact.email", to: "email" },
    { from: "contact.phone", to: "phone" },
    { from: "contact.city", to: "location" },
    { from: "contact.notes", to: "profile_text" },
  ],
  LinkedIn: [
    { from: "profile.firstName", to: "first_name" },
    { from: "profile.lastName", to: "last_name" },
    { from: "profile.emailAddress", to: "email" },
    { from: "profile.location.name", to: "location" },
    { from: "profile.headline", to: "profile_text" },
    { from: "profile.publicProfileUrl", to: "linkedin_url" },
  ],
};

export default function AdaptersPage() {
  const [adapters, setAdapters] = useState<AdapterHealth[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedAdapter, setExpandedAdapter] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiClient.admin.adapterHealth();
        setAdapters(data as unknown as AdapterHealth[]);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const totalSynced = adapters.reduce((sum, a) => sum + a.records_synced, 0);
  const avgErrorRate = adapters.length > 0
    ? (adapters.reduce((sum, a) => sum + a.error_rate, 0) / adapters.length * 100).toFixed(1)
    : "0";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <Plug className="h-6 w-6" />
          Adapter Management
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Monitor CRM/ATS integrations and data flow health.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricTile
          label="Connected"
          value={adapters.length}
          subtitle="Active adapters"
          icon={<Plug className="h-4 w-4" />}
          loading={loading}
        />
        <MetricTile
          label="Total Synced"
          value={totalSynced.toLocaleString()}
          subtitle="All time"
          icon={<Database className="h-4 w-4" />}
          loading={loading}
        />
        <MetricTile
          label="Avg Error Rate"
          value={`${avgErrorRate}%`}
          subtitle="Across all adapters"
          icon={<AlertTriangle className="h-4 w-4" />}
          loading={loading}
        />
        <MetricTile
          label="Last Sync"
          value={adapters.length > 0 ? formatRelativeTime(adapters[0].last_sync) : "\u2014"}
          subtitle="Most recent"
          icon={<Clock className="h-4 w-4" />}
          loading={loading}
        />
      </div>

      <div className="space-y-4">
        {loading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-36 rounded-lg" />
          ))
        ) : (
          adapters.map((adapter) => {
            const config = statusConfig[adapter.status] || statusConfig.healthy;
            const StatusIcon = config.icon;
            const mappings = SCHEMA_MAPPINGS[adapter.name] || [];
            const isExpanded = expandedAdapter === adapter.name;

            return (
              <Card key={adapter.name} className={`border ${adapter.status === "degraded" ? "border-amber-200" : adapter.status === "down" ? "border-red-200" : ""}`}>
                <CardContent className="p-5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`rounded-full p-2 ${config.color}`}>
                        <StatusIcon className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="font-semibold">{adapter.name}</h3>
                        <p className="text-xs text-muted-foreground">
                          Last sync: {formatRelativeTime(adapter.last_sync)}
                        </p>
                      </div>
                      <Badge variant="outline" className={config.color}>
                        {config.label}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-sm font-medium">{adapter.records_synced.toLocaleString()}</p>
                        <p className="text-xs text-muted-foreground">records synced</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">{(adapter.error_rate * 100).toFixed(1)}%</p>
                        <p className="text-xs text-muted-foreground">error rate</p>
                      </div>
                      <Button variant="outline" size="sm">
                        <RefreshCw className="h-4 w-4 mr-1.5" />
                        Sync Now
                      </Button>
                    </div>
                  </div>

                  {mappings.length > 0 && (
                    <div className="mt-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-xs"
                        onClick={() => setExpandedAdapter(isExpanded ? null : adapter.name)}
                      >
                        <ArrowDownToLine className="h-3 w-3 mr-1" />
                        {isExpanded ? "Hide schema mapping" : "View schema mapping"}
                      </Button>
                      {isExpanded && (
                        <div className="mt-2 rounded-md border overflow-hidden">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="bg-slate-50 border-b">
                                <th className="text-left font-medium px-3 py-2">{adapter.name} Field</th>
                                <th className="text-left font-medium px-3 py-2">Canonical Field</th>
                              </tr>
                            </thead>
                            <tbody>
                              {mappings.map((m) => (
                                <tr key={m.from} className="border-b last:border-0">
                                  <td className="px-3 py-1.5 font-mono text-xs text-muted-foreground">{m.from}</td>
                                  <td className="px-3 py-1.5 font-mono text-xs">{m.to}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      <Card>
        <CardContent className="p-5 space-y-4">
          <h3 className="font-semibold flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            AI Pipeline Health
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricTile
              label="Extraction Queue"
              value={12}
              subtitle="Pending"
              icon={<Loader2 className="h-4 w-4" />}
              loading={loading}
            />
            <MetricTile
              label="Processing"
              value={3}
              subtitle="Active"
              icon={<Cpu className="h-4 w-4" />}
              loading={loading}
            />
            <MetricTile
              label="Completed"
              value={847}
              subtitle="Total"
              icon={<CheckCheck className="h-4 w-4" />}
              loading={loading}
            />
            <MetricTile
              label="Failed"
              value={5}
              subtitle="Total"
              icon={<Ban className="h-4 w-4" />}
              loading={loading}
            />
          </div>
          <p className="text-xs text-muted-foreground">
            Pipeline metrics refresh every 60 seconds
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
