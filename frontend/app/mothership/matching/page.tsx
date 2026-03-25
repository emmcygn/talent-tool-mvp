"use client";

import { useState, useEffect, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import type { Match, Role, ConfidenceLevel, Candidate } from "@/contracts/canonical";
import { MatchDetailCard } from "@/components/mothership/match-detail-card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { Search, Users, Send, FolderOpen } from "lucide-react";
import { toast } from "sonner";

const CONFIDENCE_ORDER: Record<ConfidenceLevel, number> = {
  strong: 0,
  good: 1,
  possible: 2,
};

export default function MatchingPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState<string | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [candidates, setCandidates] = useState<Record<string, Candidate>>({});
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState<string>("score");
  const [filterConfidence, setFilterConfidence] = useState<string>("all");

  // Fetch roles on mount
  useEffect(() => {
    let cancelled = false;
    apiClient.roles.list().then((data) => {
      if (!cancelled) setRoles(data);
    }).catch(() => {});
    return () => { cancelled = true; };
  }, []);

  // Fetch matches + candidates when role selected
  useEffect(() => {
    if (!selectedRoleId) return;

    let cancelled = false;

    apiClient.matches.forRole(selectedRoleId).then(async (matchData) => {
      if (cancelled) return;
      setMatches(matchData);

      // Fetch candidate details for each match
      const candidateMap: Record<string, Candidate> = {};
      await Promise.all(
        matchData.map(async (m) => {
          try {
            const c = await apiClient.candidates.get(m.candidate_id);
            candidateMap[m.candidate_id] = c;
          } catch {
            // Candidate may not be fetchable; that is fine
          }
        })
      );

      if (!cancelled) {
        setCandidates(candidateMap);
        setLoading(false);
      }
    }).catch(() => {
      if (!cancelled) {
        setMatches([]);
        setLoading(false);
      }
    });

    return () => { cancelled = true; };
  }, [selectedRoleId]);

  // Sort and filter
  const filteredMatches = matches
    .filter((m) => {
      if (filterConfidence === "all") return true;
      if (filterConfidence === "strong") return m.confidence === "strong";
      if (filterConfidence === "good") return m.confidence === "strong" || m.confidence === "good";
      return true; // "possible" = all levels
    })
    .sort((a, b) => {
      if (sortBy === "confidence") {
        return CONFIDENCE_ORDER[a.confidence] - CONFIDENCE_ORDER[b.confidence];
      }
      return b.overall_score - a.overall_score;
    });

  const toggleSelect = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const handleSelectRole = useCallback((roleId: string) => {
    setSelectedRoleId(roleId);
    setMatches([]);
    setCandidates({});
    setSelectedIds(new Set());
    setLoading(true);
  }, []);

  const handleShortlist = useCallback(async (matchId: string) => {
    try {
      await apiClient.matches.updateStatus(matchId, "shortlisted");
      setMatches((prev) =>
        prev.map((m) => (m.id === matchId ? { ...m, status: "shortlisted" } : m))
      );
      toast.success("Candidate shortlisted");
    } catch {
      toast.error("Failed to shortlist candidate");
    }
  }, []);

  const handleAddToCollection = useCallback((matchId?: string) => {
    console.log("[PoC stub] Add to collection — match:", matchId);
    toast.success("Added to collection");
  }, []);

  const handleRefer = useCallback((matchId?: string) => {
    console.log("[PoC stub] Refer / handoff — match:", matchId);
    toast.success("Handoff initiated");
  }, []);

  const handleBulkAddToCollection = useCallback(() => {
    const ids = Array.from(selectedIds);
    console.log("[PoC stub] Bulk add to collection — matches:", ids);
    toast.success(`${selectedIds.size} candidate${selectedIds.size === 1 ? "" : "s"} added to collection`);
    setSelectedIds(new Set());
  }, [selectedIds]);

  const handleBulkSendHandoff = useCallback(() => {
    const ids = Array.from(selectedIds);
    console.log("[PoC stub] Bulk send handoff — matches:", ids);
    toast.success(`Handoff created for ${selectedIds.size} candidate${selectedIds.size === 1 ? "" : "s"}`);
    setSelectedIds(new Set());
  }, [selectedIds]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Match Results</h1>
          <p className="text-muted-foreground">AI-matched candidates ranked by fit</p>
        </div>
        {selectedIds.size > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{selectedIds.size} selected</Badge>
            <Button size="sm" variant="outline" onClick={handleBulkAddToCollection}>
              <FolderOpen className="mr-2 h-4 w-4" /> <span className="hidden sm:inline">Add to</span> Collection
            </Button>
            <Button size="sm" variant="outline" onClick={handleBulkSendHandoff}>
              <Send className="mr-2 h-4 w-4" /> <span className="hidden sm:inline">Send as</span> Handoff
            </Button>
          </div>
        )}
      </div>

      {/* Role selector + Filter bar */}
      <div className="flex flex-col gap-3 md:flex-row md:gap-4 md:items-center md:flex-wrap">
        <Select
          value={selectedRoleId ?? undefined}
          onValueChange={(val) => val && handleSelectRole(val)}
        >
          <SelectTrigger className="w-full md:w-[300px]">
            {selectedRoleId
              ? roles.find((r) => r.id === selectedRoleId)?.title ?? "Select a role..."
              : "Select a role..."}
          </SelectTrigger>
          <SelectContent>
            {roles.map((role) => (
              <SelectItem key={role.id} value={role.id}>
                {role.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={filterConfidence}
          onValueChange={(val) => val && setFilterConfidence(val)}
        >
          <SelectTrigger className="w-full md:w-[160px]">
            <SelectValue placeholder="Confidence" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All matches</SelectItem>
            <SelectItem value="strong">Strong only</SelectItem>
            <SelectItem value="good">Good+</SelectItem>
            <SelectItem value="possible">All levels</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={sortBy}
          onValueChange={(val) => val && setSortBy(val)}
        >
          <SelectTrigger className="w-full md:w-[160px]">
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="score">Highest score</SelectItem>
            <SelectItem value="confidence">Confidence level</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Match results */}
      {loading ? (
        <LoadingSkeleton variant="card" count={5} />
      ) : !selectedRoleId ? (
        <EmptyState
          icon={Search}
          title="Select a role"
          description="Choose a role above to see matched candidates"
        />
      ) : filteredMatches.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No matches found"
          description="No candidates match the requirements for this role yet"
        />
      ) : (
        <div className="space-y-3">
          {filteredMatches.map((match) => (
            <MatchDetailCard
              key={match.id}
              match={match}
              candidate={candidates[match.candidate_id] ?? null}
              selected={selectedIds.has(match.id)}
              onToggleSelect={() => toggleSelect(match.id)}
              onShortlist={() => handleShortlist(match.id)}
              onAddToCollection={() => handleAddToCollection(match.id)}
              onRefer={() => handleRefer(match.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
