"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, Loader2 } from "lucide-react";

interface AdapterSyncButtonsProps {
  onSyncStart: () => void;
  onExtractionComplete: () => void;
}

const ADAPTERS = [
  {
    id: "bullhorn",
    name: "Bullhorn",
    description: "ATS — sync candidates from your Bullhorn instance",
    lastSync: "2h ago",
    status: "connected" as const,
  },
  {
    id: "hubspot",
    name: "HubSpot",
    description: "CRM — import contacts tagged as candidates",
    lastSync: "4h ago",
    status: "connected" as const,
  },
  {
    id: "linkedin",
    name: "LinkedIn Recruiter",
    description: "Import profiles from LinkedIn Recruiter exports",
    lastSync: "1d ago",
    status: "degraded" as const,
  },
];

export function AdapterSyncButtons({ onSyncStart }: AdapterSyncButtonsProps) {
  const [syncing, setSyncing] = useState<string | null>(null);

  const handleSync = async (adapterId: string) => {
    setSyncing(adapterId);
    onSyncStart();
    await new Promise((r) => setTimeout(r, 2000));
    setSyncing(null);
  };

  return (
    <div className="grid gap-4">
      {ADAPTERS.map((adapter) => (
        <Card key={adapter.id}>
          <CardHeader className="flex flex-row items-center gap-4 pb-2">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <CardTitle className="text-base">{adapter.name}</CardTitle>
                <Badge
                  variant="outline"
                  className={
                    adapter.status === "connected"
                      ? "bg-green-50 text-green-700 border-green-200"
                      : "bg-amber-50 text-amber-700 border-amber-200"
                  }
                >
                  {adapter.status}
                </Badge>
              </div>
              <CardDescription className="mt-1">
                {adapter.description}
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="flex items-center justify-between pt-0">
            <span className="text-xs text-slate-400">
              Last synced: {adapter.lastSync}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={syncing !== null}
              onClick={() => handleSync(adapter.id)}
              className="gap-2"
            >
              {syncing === adapter.id ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              Sync Now
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
