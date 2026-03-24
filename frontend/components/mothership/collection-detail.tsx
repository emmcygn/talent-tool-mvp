"use client";

import { useState } from "react";
import type { Collection, Candidate } from "@/contracts/canonical";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  ArrowLeft, Edit, UserPlus, UserMinus, Search,
  Eye, EyeOff, Share2,
} from "lucide-react";

interface CollectionDetailProps {
  collection: Collection;
  candidates: Candidate[];
  allCandidates: Candidate[];
  onBack: () => void;
  onEdit: () => void;
  onRemoveCandidate: (candidateId: string) => void;
  onAddCandidate: (candidateId: string) => void;
}

export function CollectionDetail({
  collection, candidates, allCandidates,
  onBack, onEdit, onRemoveCandidate, onAddCandidate,
}: CollectionDetailProps) {
  const [addMode, setAddMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredAdd = allCandidates.filter(
    (c) =>
      !collection.candidate_ids.includes(c.id) &&
      `${c.first_name} ${c.last_name}`.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={onBack} aria-label="Back to collections">
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h2 className="text-xl font-semibold">{collection.name}</h2>
            {collection.description && (
              <p className="text-sm text-muted-foreground mt-0.5">{collection.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setAddMode(!addMode)}>
            <UserPlus className="h-4 w-4 mr-1.5" />
            Add Candidates
          </Button>
          <Button variant="outline" size="sm" onClick={onEdit}>
            <Edit className="h-4 w-4 mr-1.5" />
            Edit
          </Button>
        </div>
      </div>

      {/* Tags + stats */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-1 text-sm text-muted-foreground">
          {collection.visibility === "private" && <EyeOff className="h-3.5 w-3.5" />}
          {collection.visibility === "shared_specific" && <Share2 className="h-3.5 w-3.5 text-blue-500" />}
          {collection.visibility === "shared_all" && <Eye className="h-3.5 w-3.5 text-green-500" />}
          <span className="capitalize">{collection.visibility.replace("_", " ")}</span>
        </div>
        <span className="text-sm text-muted-foreground">
          {collection.candidate_count} candidate{collection.candidate_count !== 1 ? "s" : ""}
        </span>
        {collection.tags.map((tag) => (
          <Badge key={tag} variant="secondary" className="text-xs">{tag}</Badge>
        ))}
      </div>

      {/* Add candidates panel */}
      {addMode && (
        <div className="rounded-lg border border-dashed border-blue-300 bg-blue-50/50 p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-muted-foreground" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search candidates to add..."
              className="flex-1 bg-white"
            />
          </div>
          <div className="max-h-60 overflow-y-auto space-y-1">
            {filteredAdd.slice(0, 10).map((c) => (
              <div
                key={c.id}
                className="flex items-center justify-between rounded-md px-3 py-2 hover:bg-white transition-colors"
              >
                <span className="text-sm font-medium">
                  {c.first_name} {c.last_name}
                  <span className="text-muted-foreground ml-2">{c.location}</span>
                </span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onAddCandidate(c.id)}
                >
                  <UserPlus className="h-3.5 w-3.5" />
                </Button>
              </div>
            ))}
            {filteredAdd.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">
                No candidates available to add.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Candidate list */}
      <div className="space-y-3">
        {candidates.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No candidates in this collection yet.</p>
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => setAddMode(true)}
            >
              <UserPlus className="h-4 w-4 mr-1.5" />
              Add your first candidate
            </Button>
          </div>
        ) : (
          candidates.map((candidate) => (
            <div
              key={candidate.id}
              className="flex items-center justify-between rounded-lg border p-4 hover:bg-slate-50/50 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm">
                  {candidate.first_name} {candidate.last_name}
                </div>
                <div className="text-xs text-muted-foreground mt-0.5">
                  {candidate.location} · {candidate.seniority ?? "\u2014"} ·{" "}
                  {candidate.availability?.replace("_", " ") ?? "Unknown"}
                </div>
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {candidate.skills.slice(0, 5).map((s) => (
                    <Badge key={s.name} variant="outline" className="text-[11px] py-0">
                      {s.name}
                    </Badge>
                  ))}
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onRemoveCandidate(candidate.id)}
                className="text-red-400 hover:text-red-600 hover:bg-red-50"
                aria-label={`Remove ${candidate.first_name} from collection`}
              >
                <UserMinus className="h-4 w-4" />
              </Button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
