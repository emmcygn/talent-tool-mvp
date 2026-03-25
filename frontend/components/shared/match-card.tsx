"use client";

import { Card, CardContent, CardHeader, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { MapPin, Clock, Heart, X, Send, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { SkillChips } from "./skill-chips";
import { ConfidenceBadge } from "./confidence-badge";
import type { Match, Candidate, CandidateAnonymized } from "@/contracts/canonical";
import { cn } from "@/lib/utils";

interface MatchCardProps {
  match: Match;
  candidate: Candidate | CandidateAnonymized;
  anonymized?: boolean;
  isPoolCandidate?: boolean;
  onShortlist?: (matchId: string) => void;
  onDismiss?: (matchId: string) => void;
  onRequestIntro?: (matchId: string) => void;
  onAddToCollection?: (matchId: string) => void;
  expandable?: boolean;
  className?: string;
}

export function MatchCard({
  match,
  candidate,
  anonymized = false,
  isPoolCandidate = false,
  onShortlist,
  onDismiss,
  onRequestIntro,
  expandable = true,
  className,
}: MatchCardProps) {
  const [expanded, setExpanded] = useState(false);

  const displayName = anonymized && "last_initial" in candidate
    ? `${candidate.first_name} ${candidate.last_initial}.`
    : "last_name" in candidate
      ? `${candidate.first_name} ${candidate.last_name}`
      : candidate.first_name;

  return (
    <Card className={cn("transition-all", className)}>
      <CardHeader className="flex flex-row items-start gap-4 pb-3">
        <Avatar className="h-10 w-10">
          <AvatarFallback className="bg-muted text-sm font-medium">
            {candidate.first_name.charAt(0)}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-foreground truncate">{displayName}</h3>
            <ConfidenceBadge confidence={match.confidence} />
            {isPoolCandidate && (
              <Badge variant="secondary" className="bg-blue-500/10 text-blue-400 text-xs">
                Pre-vetted
              </Badge>
            )}
          </div>
          {candidate.seniority && (
            <p className="text-sm text-muted-foreground capitalize">{candidate.seniority}</p>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pt-0">
        <p className="text-sm text-muted-foreground leading-relaxed">{match.explanation}</p>

        <SkillChips skills={match.skill_overlap} />

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
          {candidate.location && (
            <span className="flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {candidate.location}
            </span>
          )}
          {candidate.availability && (
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {candidate.availability.replace("_", " ")}
            </span>
          )}
        </div>

        {expanded && (
          <div className="mt-4 space-y-3 rounded-lg bg-muted p-4">
            {match.strengths.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-1">
                  Strengths
                </h4>
                <ul className="space-y-1">
                  {match.strengths.map((s, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-green-400 shrink-0" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {match.gaps.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-400 mb-1">
                  Gaps
                </h4>
                <ul className="space-y-1">
                  {match.gaps.map((g, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-amber-400 shrink-0" />
                      {g}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <p className="text-sm font-medium text-foreground/80 border-t border-border pt-3">
              {match.recommendation}
            </p>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex items-center justify-between pt-0">
        <div className="flex gap-2">
          {onShortlist && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onShortlist(match.id)}
              className="gap-1.5 text-pink-600 hover:text-pink-700 hover:bg-pink-50"
            >
              <Heart className="h-3.5 w-3.5" />
              Shortlist
            </Button>
          )}
          {onDismiss && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onDismiss(match.id)}
              className="gap-1.5 text-muted-foreground hover:text-foreground/80"
            >
              <X className="h-3.5 w-3.5" />
              Dismiss
            </Button>
          )}
          {onRequestIntro && (
            <Button
              variant="default"
              size="sm"
              onClick={() => onRequestIntro(match.id)}
              className="gap-1.5"
            >
              <Send className="h-3.5 w-3.5" />
              Request Intro
            </Button>
          )}
        </div>

        {expandable && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="gap-1 text-muted-foreground/60"
          >
            {expanded ? (
              <>Less <ChevronUp className="h-3.5 w-3.5" /></>
            ) : (
              <>More <ChevronDown className="h-3.5 w-3.5" /></>
            )}
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
