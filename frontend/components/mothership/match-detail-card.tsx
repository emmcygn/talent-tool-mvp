"use client";

import { useState } from "react";
import type { Match, Candidate } from "@/contracts/canonical";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { ConfidenceBadge } from "@/components/shared/confidence-badge";
import { SkillChips } from "@/components/shared/skill-chips";
import { ScoringBreakdown } from "./scoring-breakdown";
import { MatchActions } from "./match-actions";
import { ChevronDown, ChevronUp } from "lucide-react";

interface MatchDetailCardProps {
  match: Match;
  candidate?: Candidate | null;
  selected: boolean;
  onToggleSelect: () => void;
  onShortlist: () => void;
  onAddToCollection: () => void;
  onRefer: () => void;
}

export function MatchDetailCard({
  match,
  candidate,
  selected,
  onToggleSelect,
  onShortlist,
  onAddToCollection,
  onRefer,
}: MatchDetailCardProps) {
  const [expanded, setExpanded] = useState(false);

  const candidateName = candidate
    ? `${candidate.first_name} ${candidate.last_name}`
    : `Candidate ${match.candidate_id.slice(0, 8)}`;

  const scorePercent = (match.overall_score * 100).toFixed(0);

  return (
    <Card className={`transition-all ${selected ? "ring-2 ring-primary" : ""}`}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <Checkbox
            checked={selected}
            onCheckedChange={onToggleSelect}
            className="mt-1"
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-medium">{candidateName}</span>
                <ConfidenceBadge confidence={match.confidence} />
                <Badge variant="outline" className="text-xs font-normal">
                  {scorePercent}%
                </Badge>
              </div>
              <MatchActions
                onShortlist={onShortlist}
                onAddToCollection={onAddToCollection}
                onRefer={onRefer}
              />
            </div>

            <p className="text-sm text-muted-foreground mt-1">{match.explanation}</p>

            <div className="mt-2">
              <SkillChips skills={match.skill_overlap} />
            </div>

            {/* Strengths + Gaps as badges */}
            <div className="flex gap-4 mt-2 text-xs">
              {match.strengths.length > 0 && (
                <div className="flex gap-1 flex-wrap">
                  {match.strengths.map((s, i) => (
                    <Badge key={i} variant="outline" className="bg-green-50 text-green-700 text-xs">
                      {s}
                    </Badge>
                  ))}
                </div>
              )}
              {match.gaps.length > 0 && (
                <div className="flex gap-1 flex-wrap">
                  {match.gaps.map((g, i) => (
                    <Badge key={i} variant="outline" className="bg-amber-50 text-amber-700 text-xs">
                      {g}
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            {/* Expand toggle */}
            <Button
              variant="ghost"
              size="sm"
              className="mt-2 text-xs"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? (
                <ChevronUp className="mr-1 h-3 w-3" />
              ) : (
                <ChevronDown className="mr-1 h-3 w-3" />
              )}
              {expanded ? "Hide details" : "Show scoring breakdown"}
            </Button>

            {/* Expanded: full traceability */}
            {expanded && (
              <div className="mt-3 pt-3 border-t">
                <ScoringBreakdown match={match} />
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
