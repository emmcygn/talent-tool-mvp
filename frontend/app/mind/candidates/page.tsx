"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { CandidateFilterBar, type FilterState } from "@/components/mind/candidate-filter-bar";
import { CandidateGrid } from "@/components/mind/candidate-grid";
import { CandidateList } from "@/components/mind/candidate-list";
import { ViewToggle } from "@/components/mind/view-toggle";
import { DismissDialog } from "@/components/mind/dismiss-dialog";
import { Users, Briefcase } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import type { Role, Match, CandidateAnonymized } from "@/contracts/canonical";
import { useNotify } from "@/components/shared/notification-toast";

interface MatchWithCandidate {
  match: Match;
  candidate: CandidateAnonymized;
}

export default function CandidateBrowsePage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState<string | null>(null);
  const [matches, setMatches] = useState<MatchWithCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"grid" | "list">("grid");
  const [filters, setFilters] = useState<FilterState>({
    skills: [],
    seniority: null,
    availability: null,
    location: "",
  });
  const [dismissTarget, setDismissTarget] = useState<string | null>(null);
  const notify = useNotify();

  // Load roles on mount, then load matches for the first active role
  useEffect(() => {
    let cancelled = false;
    async function init() {
      const data = await apiClient.roles.list();
      if (cancelled) return;
      const activeRoles = data.filter((r) => r.status === "active");
      setRoles(activeRoles);
      if (activeRoles.length > 0) {
        const firstId = activeRoles[0].id;
        setSelectedRoleId(firstId);
        const matchData = await apiClient.matches.forRoleAnonymized(firstId);
        if (cancelled) return;
        setMatches(matchData);
      }
      setLoading(false);
    }
    init();
    return () => { cancelled = true; };
  }, []);

  const handleSelectRole = useCallback(async (roleId: string) => {
    setSelectedRoleId(roleId);
    setLoading(true);
    const data = await apiClient.matches.forRoleAnonymized(roleId);
    setMatches(data);
    setLoading(false);
  }, []);

  // Apply filters
  const filteredMatches = useMemo(() => {
    return matches.filter(({ candidate }) => {
      if (filters.seniority && candidate.seniority !== filters.seniority) return false;
      if (filters.availability && candidate.availability !== filters.availability) return false;
      if (filters.location && candidate.location &&
          !candidate.location.toLowerCase().includes(filters.location.toLowerCase())) return false;
      if (filters.skills.length > 0) {
        const candidateSkillNames = candidate.skills.map((s) => s.name.toLowerCase());
        const hasAllSkills = filters.skills.every((skill) =>
          candidateSkillNames.some((cs) => cs.includes(skill.toLowerCase()))
        );
        if (!hasAllSkills) return false;
      }
      return true;
    });
  }, [matches, filters]);

  // Sort by score descending
  const sortedMatches = useMemo(() => {
    return [...filteredMatches].sort((a, b) => b.match.overall_score - a.match.overall_score);
  }, [filteredMatches]);

  const handleShortlist = async (matchId: string) => {
    try {
      await apiClient.matches.updateStatus(matchId, "shortlisted");
      setMatches((prev) =>
        prev.map((m) =>
          m.match.id === matchId ? { ...m, match: { ...m.match, status: "shortlisted" } } : m
        )
      );
      notify({ title: "Candidate shortlisted", variant: "success" });
    } catch {
      notify({ title: "Failed to shortlist", variant: "error" });
    }
  };

  const handleDismiss = async (matchId: string, reason?: string) => {
    try {
      await apiClient.matches.updateStatus(matchId, "dismissed", reason);
      setMatches((prev) =>
        prev.map((m) =>
          m.match.id === matchId ? { ...m, match: { ...m.match, status: "dismissed" } } : m
        )
      );
      setDismissTarget(null);
      notify({ title: "Candidate dismissed", variant: "info" });
    } catch {
      notify({ title: "Failed to dismiss", variant: "error" });
    }
  };

  const handleRequestIntro = async (matchId: string) => {
    try {
      await apiClient.matches.updateStatus(matchId, "intro_requested");
      setMatches((prev) =>
        prev.map((m) =>
          m.match.id === matchId ? { ...m, match: { ...m.match, status: "intro_requested" } } : m
        )
      );
      notify({
        title: "Introduction requested",
        description: "We will prepare a quote and connect you shortly.",
        variant: "success",
      });
    } catch {
      notify({ title: "Failed to request introduction", variant: "error" });
    }
  };

  // Collect all unique skills from current matches for filter suggestions
  const availableSkills = useMemo(() => {
    const skillSet = new Set<string>();
    matches.forEach(({ candidate }) => {
      candidate.skills.forEach((s) => skillSet.add(s.name));
    });
    return Array.from(skillSet).sort();
  }, [matches]);

  const selectedRole = roles.find((r) => r.id === selectedRoleId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Matched Candidates</h1>
          <p className="text-sm text-muted-foreground mt-1">
            AI-matched candidates for your active roles
          </p>
        </div>

        {/* Role Selector */}
        <Select
          value={selectedRoleId ?? ""}
          onValueChange={(val) => val && handleSelectRole(val)}
        >
          <SelectTrigger className="w-full md:w-72">
            <SelectValue placeholder="Select a role" />
          </SelectTrigger>
          <SelectContent>
            {roles.map((role) => (
              <SelectItem key={role.id} value={role.id}>
                <div className="flex items-center gap-2">
                  <Briefcase className="h-4 w-4 text-muted-foreground/60" />
                  {role.title}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Summary bar */}
      {selectedRole && !loading && (
        <div className="flex flex-wrap items-center gap-2 md:gap-4 text-sm text-muted-foreground">
          <span>{sortedMatches.length} candidates matched</span>
          <span className="text-muted-foreground/40">|</span>
          <span className="text-emerald-400">
            {sortedMatches.filter((m) => m.match.confidence === "strong").length} strong
          </span>
          <span className="text-amber-400">
            {sortedMatches.filter((m) => m.match.confidence === "good").length} good
          </span>
          <span className="text-muted-foreground/60">
            {sortedMatches.filter((m) => m.match.confidence === "possible").length} possible
          </span>
        </div>
      )}

      {/* Filter Bar + View Toggle */}
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <CandidateFilterBar
          filters={filters}
          onChange={setFilters}
          availableSkills={availableSkills}
        />
        <ViewToggle view={view} onChange={setView} />
      </div>

      {/* Content */}
      {loading ? (
        <LoadingSkeleton variant="card" count={3} />
      ) : sortedMatches.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No candidates found"
          description={
            matches.length > 0
              ? "Try adjusting your filters to see more candidates."
              : "No matches have been generated for this role yet. Check back soon."
          }
        />
      ) : view === "grid" ? (
        <CandidateGrid
          matches={sortedMatches}
          onShortlist={handleShortlist}
          onDismiss={(id) => setDismissTarget(id)}
          onRequestIntro={handleRequestIntro}
        />
      ) : (
        <CandidateList
          matches={sortedMatches}
          onShortlist={handleShortlist}
          onDismiss={(id) => setDismissTarget(id)}
          onRequestIntro={handleRequestIntro}
        />
      )}

      {/* Dismiss Dialog */}
      {dismissTarget && (
        <DismissDialog
          onConfirm={(reason) => handleDismiss(dismissTarget, reason)}
          onCancel={() => setDismissTarget(null)}
        />
      )}
    </div>
  );
}
