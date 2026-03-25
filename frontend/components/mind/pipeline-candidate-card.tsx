"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import type { ConfidenceLevel, AvailabilityStatus } from "@/contracts/canonical";
import { confidenceColor } from "@/lib/utils";
import { MessageSquare, StickyNote } from "lucide-react";

interface PipelineCandidateItem {
  id: string;
  stage: string;
  candidateId: string;
  name: string;
  location: string | null;
  skills: string[];
  confidence: ConfidenceLevel;
  availability: AvailabilityStatus | null;
  stageNotes: string;
}

interface PipelineCandidateCardProps {
  item: PipelineCandidateItem;
  onUpdateNotes: (itemId: string, notes: string) => void;
}

export function PipelineCandidateCard({ item, onUpdateNotes }: PipelineCandidateCardProps) {
  const [showNotes, setShowNotes] = useState(false);
  const [notes, setNotes] = useState(item.stageNotes);

  return (
    <Card className="shadow-sm hover:shadow transition-shadow">
      <CardContent className="p-3">
        <div className="flex items-start justify-between">
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{item.name}</p>
            {item.location && (
              <p className="text-xs text-muted-foreground">{item.location}</p>
            )}
          </div>
          <Badge
            variant="outline"
            className={`text-[10px] shrink-0 ${confidenceColor(item.confidence)}`}
          >
            {item.confidence}
          </Badge>
        </div>

        {/* Skills */}
        <div className="flex flex-wrap gap-1 mt-2">
          {item.skills.slice(0, 3).map((skill) => (
            <Badge key={skill} variant="secondary" className="text-[10px] py-0 px-1.5">
              {skill}
            </Badge>
          ))}
          {item.skills.length > 3 && (
            <span className="text-[10px] text-muted-foreground">
              +{item.skills.length - 3}
            </span>
          )}
        </div>

        {/* Availability */}
        {item.availability && (
          <p className="text-[10px] text-muted-foreground mt-1.5 capitalize">
            {item.availability.replace("_", " ")}
          </p>
        )}

        {/* Notes toggle */}
        <div className="mt-2 pt-2 border-t">
          <button
            onClick={(e) => { e.stopPropagation(); setShowNotes(!showNotes); }}
            className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
          >
            {item.stageNotes ? (
              <StickyNote className="h-3 w-3 text-amber-500" />
            ) : (
              <MessageSquare className="h-3 w-3" />
            )}
            {item.stageNotes ? "View notes" : "Add notes"}
          </button>

          {showNotes && (
            <div className="mt-2" onClick={(e) => e.stopPropagation()}>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                onBlur={() => onUpdateNotes(item.id, notes)}
                placeholder="Add stage notes..."
                rows={2}
                className="text-xs"
              />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export type { PipelineCandidateItem };
