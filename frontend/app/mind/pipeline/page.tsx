"use client";

import { useState, useEffect } from "react";
import { KanbanBoard } from "@/components/shared/kanban-board";
import type { KanbanStage } from "@/components/shared/kanban-board";
import {
  PipelineCandidateCard,
} from "@/components/mind/pipeline-candidate-card";
import type { PipelineCandidateItem } from "@/components/mind/pipeline-candidate-card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import type { Role } from "@/contracts/canonical";
import { apiClient } from "@/lib/api-client";
import { MOCK_MATCHES, getCandidateById } from "@/lib/mock-data";
import { Columns3, Filter } from "lucide-react";

const PIPELINE_STAGES: KanbanStage[] = [
  { id: "matched", label: "Matched", color: "bg-slate-400" },
  { id: "shortlisted", label: "Shortlisted", color: "bg-blue-500" },
  { id: "intro_requested", label: "Intro Requested", color: "bg-purple-500" },
  { id: "interviewing", label: "Interviewing", color: "bg-amber-500" },
  { id: "offer", label: "Offer", color: "bg-orange-500" },
  { id: "placed", label: "Placed", color: "bg-green-500" },
];

export default function PipelinePage() {
  const [items, setItems] = useState<PipelineCandidateItem[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedRole, setSelectedRole] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const rolesData = await apiClient.roles.list();
        setRoles(rolesData);

        // Populate pipeline from mock matches
        const pipelineItems: PipelineCandidateItem[] = MOCK_MATCHES
          .filter((m) => m.overall_score >= 0.7)
          .map((m, idx) => {
            const candidate = getCandidateById(m.candidate_id);
            const stages = ["matched", "shortlisted", "intro_requested"] as const;
            return {
              id: m.id,
              stage: stages[idx % stages.length],
              candidateId: m.candidate_id,
              name: candidate
                ? `${candidate.first_name} ${candidate.last_name.charAt(0)}.`
                : "Unknown",
              location: candidate?.location ?? null,
              skills: candidate?.skills.slice(0, 4).map((s) => s.name) ?? [],
              confidence: m.confidence,
              availability: candidate?.availability ?? null,
              stageNotes: "",
            };
          });
        setItems(pipelineItems);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function handleMoveItem(itemId: string, toStage: string) {
    setItems((prev) =>
      prev.map((item) =>
        item.id === itemId ? { ...item, stage: toStage } : item
      )
    );
    // Also call API to update match status / pipeline stage
  }

  function handleUpdateNotes(itemId: string, notes: string) {
    setItems((prev) =>
      prev.map((item) =>
        item.id === itemId ? { ...item, stageNotes: notes } : item
      )
    );
    // Also persist via API
  }

  const filteredItems =
    selectedRole === "all"
      ? items
      : items; // Filter by role when data model supports it

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
            <Columns3 className="h-6 w-6" />
            Hiring Pipeline
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Track candidates through your hiring process. Drag cards between stages.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <Select value={selectedRole} onValueChange={(val) => val && setSelectedRole(val)}>
            <SelectTrigger className="w-[220px]">
              <SelectValue placeholder="All roles" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All roles</SelectItem>
              {roles.map((role) => (
                <SelectItem key={role.id} value={role.id}>
                  {role.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Kanban */}
      {loading ? (
        <div className="flex gap-4">
          {PIPELINE_STAGES.map((stage) => (
            <Skeleton key={stage.id} className="h-96 w-72 rounded-lg" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="text-center py-16 border rounded-lg border-dashed">
          <Columns3 className="h-10 w-10 mx-auto text-muted-foreground/50 mb-3" />
          <p className="text-muted-foreground">No candidates in your pipeline yet.</p>
          <p className="text-sm text-muted-foreground mt-1">
            Review matched candidates and shortlist them to build your pipeline.
          </p>
        </div>
      ) : (
        <KanbanBoard
          stages={PIPELINE_STAGES}
          items={filteredItems}
          onMoveItem={handleMoveItem}
          renderItem={(item) => (
            <PipelineCandidateCard
              item={item}
              onUpdateNotes={handleUpdateNotes}
            />
          )}
        />
      )}
    </div>
  );
}
