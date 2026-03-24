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

interface DedupPair {
  id: string;
  candidateA: { name: string; email: string; location: string; seniority: string };
  candidateB: { name: string; email: string; location: string; seniority: string };
  confidence: number;
  matchType: string;
}

const INITIAL_PAIRS: DedupPair[] = [
  {
    id: "dup-1",
    candidateA: { name: "James Walker", email: "j.walker@gmail.com", location: "London", seniority: "Senior" },
    candidateB: { name: "James Walker", email: "james.walker@outlook.com", location: "London", seniority: "Senior" },
    confidence: 0.94,
    matchType: "Name + Location",
  },
  {
    id: "dup-2",
    candidateA: { name: "Sarah O'Brien", email: "sarah.obrien@yahoo.co.uk", location: "Manchester", seniority: "Mid" },
    candidateB: { name: "Sarah O Brien", email: "sarah.obrien@yahoo.co.uk", location: "Manchester", seniority: "Senior" },
    confidence: 0.87,
    matchType: "Email exact",
  },
  {
    id: "dup-3",
    candidateA: { name: "Raj Patel", email: "raj.patel@techcorp.com", location: "Birmingham", seniority: "Lead" },
    candidateB: { name: "Rajesh Patel", email: "rajesh.p@techcorp.com", location: "Birmingham", seniority: "Lead" },
    confidence: 0.78,
    matchType: "Name fuzzy + Location",
  },
];

function fieldBg(a: string, b: string) {
  return a.toLowerCase() === b.toLowerCase() ? "bg-green-50" : "bg-red-50";
}

export default function DataQualityPage() {
  const [loading, setLoading] = useState(true);
  const [pairs, setPairs] = useState<DedupPair[]>(INITIAL_PAIRS);

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  function removePair(id: string) {
    setPairs((prev) => prev.filter((p) => p.id !== id));
  }

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
        ) : pairs.length === 0 ? (
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
          pairs.map((pair) => (
            <Card key={pair.id}>
              <CardContent className="p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <GitMerge className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium text-sm">Potential Duplicate</p>
                      <p className="text-xs text-muted-foreground">
                        {pair.matchType} &middot; {(pair.confidence * 100).toFixed(0)}% confidence
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="default" onClick={() => removePair(pair.id)}>
                      <GitMerge className="h-3.5 w-3.5 mr-1.5" />
                      Merge
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => removePair(pair.id)}>
                      Keep Separate
                    </Button>
                  </div>
                </div>

                <div className="rounded-md border overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-slate-50 border-b">
                        <th className="text-left font-medium px-3 py-2 w-28">Field</th>
                        <th className="text-left font-medium px-3 py-2">Candidate A</th>
                        <th className="text-left font-medium px-3 py-2">Candidate B</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(["name", "email", "location", "seniority"] as const).map((field) => {
                        const a = pair.candidateA[field];
                        const b = pair.candidateB[field];
                        const bg = fieldBg(a, b);
                        return (
                          <tr key={field} className="border-b last:border-0">
                            <td className="px-3 py-2 font-medium capitalize text-muted-foreground">{field}</td>
                            <td className={`px-3 py-2 ${bg}`}>{a}</td>
                            <td className={`px-3 py-2 ${bg}`}>{b}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
