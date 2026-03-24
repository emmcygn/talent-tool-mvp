"use client";

import { useState, useEffect } from "react";
import { MetricTile } from "@/components/shared/metric-tile";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  GitMerge, ShieldCheck, AlertTriangle, CheckCircle2, Filter,
} from "lucide-react";

export default function DataQualityPage() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <ShieldCheck className="h-6 w-6" />
          Data Quality
        </h1>
        <p className="text-muted-foreground text-sm mt-1">
          Review potential duplicates and maintain data integrity.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricTile
          label="Review Queue"
          value={0}
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

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <Select defaultValue="confidence_desc">
            <SelectTrigger className="w-[200px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="confidence_desc">Highest confidence first</SelectItem>
              <SelectItem value="confidence_asc">Lowest confidence first</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-4">
        {loading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-72 rounded-lg" />
          ))
        ) : (
          <Card>
            <CardContent className="text-center py-12">
              <CheckCircle2 className="h-10 w-10 mx-auto text-green-500 mb-3" />
              <p className="text-lg font-medium">All clear</p>
              <p className="text-sm text-muted-foreground mt-1">
                No pending duplicate reviews. The system is healthy.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
