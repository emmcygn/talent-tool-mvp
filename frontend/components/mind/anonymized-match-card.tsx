"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  MapPin, Clock, Heart, X, Send, ChevronDown, ChevronUp,
  ShieldCheck, CheckCircle2,
} from "lucide-react";
import { SkillChips } from "@/components/shared/skill-chips";
import { ConfidenceBadge } from "@/components/shared/confidence-badge";
import type { Match, CandidateAnonymized } from "@/contracts/canonical";
import { cn } from "@/lib/utils";

interface AnonymizedMatchCardProps {
  match: Match;
  candidate: CandidateAnonymized;
  layout?: "vertical" | "horizontal";
  onShortlist: (matchId: string) => void;
  onDismiss: (matchId: string) => void;
  onRequestIntro: (matchId: string) => void;
}

const AVAILABILITY_LABELS: Record<string, string> = {
  immediate: "Available now",
  "1_month": "1 month notice",
  "3_months": "3 months notice",
  not_looking: "Not looking",
};

const STATUS_BADGES: Record<string, { label: string; className: string }> = {
  shortlisted: { label: "Shortlisted", className: "bg-pink-50 text-pink-700 border-pink-200" },
  intro_requested: { label: "Intro Requested", className: "bg-blue-50 text-blue-700 border-blue-200" },
  dismissed: { label: "Dismissed", className: "bg-slate-100 text-slate-400 border-slate-200" },
};

export function AnonymizedMatchCard({
  match,
  candidate,
  onShortlist,
  onDismiss,
  onRequestIntro,
}: AnonymizedMatchCardProps) {
  const [expanded, setExpanded] = useState(false);

  const displayName = `${candidate.first_name} ${candidate.last_initial}.`;
  const statusBadge = STATUS_BADGES[match.status];
  const isActioned = match.status !== "generated";

  return (
    <Card className={cn(
      "transition-all",
      isActioned && match.status === "dismissed" && "opacity-60",
    )}>
      <CardHeader className="flex flex-row items-start gap-4 pb-3">
        <Avatar className="h-11 w-11">
          <AvatarFallback className="bg-gradient-to-br from-slate-100 to-slate-200 text-sm font-semibold text-slate-600">
            {candidate.first_name.charAt(0)}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-slate-900">{displayName}</h3>
            <ConfidenceBadge confidence={match.confidence} />
            {candidate.is_pool_candidate && (
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 gap-1 text-xs">
                <ShieldCheck className="h-3 w-3" />
                Pre-vetted
              </Badge>
            )}
            {statusBadge && (
              <Badge variant="outline" className={cn("gap-1 text-xs", statusBadge.className)}>
                <CheckCircle2 className="h-3 w-3" />
                {statusBadge.label}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-3 mt-1 text-sm text-slate-500">
            {candidate.seniority && (
              <span className="capitalize">{candidate.seniority}</span>
            )}
            {candidate.experience_years != null && (
              <span>{Math.round(candidate.experience_years)} years experience</span>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pt-0">
        {/* Explanation — plain English */}
        <p className="text-sm text-slate-600 leading-relaxed">{match.explanation}</p>

        {/* Skill Chips */}
        <SkillChips skills={match.skill_overlap} maxDisplay={6} />

        {/* Meta */}
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-500">
          {candidate.location && (
            <span className="flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {candidate.location}
            </span>
          )}
          {candidate.availability && (
            <span className={cn(
              "flex items-center gap-1",
              candidate.availability === "immediate" ? "text-green-600" : ""
            )}>
              <Clock className="h-3.5 w-3.5" />
              {AVAILABILITY_LABELS[candidate.availability] ?? candidate.availability}
            </span>
          )}
        </div>

        {/* Expanded — strengths + gaps */}
        {expanded && (
          <div className="mt-3 space-y-3 rounded-lg bg-slate-50 p-4 text-sm">
            {match.strengths.length > 0 && (
              <div>
                <p className="font-medium text-slate-700 mb-1">Why they are a great fit:</p>
                <ul className="space-y-1">
                  {match.strengths.map((s, i) => (
                    <li key={i} className="text-slate-600 flex items-start gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-green-400 shrink-0" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {match.gaps.length > 0 && (
              <div>
                <p className="font-medium text-slate-700 mb-1">Things to consider:</p>
                <ul className="space-y-1">
                  {match.gaps.map((g, i) => (
                    <li key={i} className="text-slate-600 flex items-start gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-amber-400 shrink-0" />
                      {g}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {match.recommendation && (
              <p className="text-slate-700 font-medium border-t border-slate-200 pt-2">
                {match.recommendation}
              </p>
            )}
          </div>
        )}
      </CardContent>

      <CardFooter className="flex items-center justify-between pt-0">
        <div className="flex gap-2">
          {!isActioned && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onShortlist(match.id)}
                className="gap-1.5 text-pink-600 hover:text-pink-700 hover:bg-pink-50"
              >
                <Heart className="h-3.5 w-3.5" />
                Shortlist
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDismiss(match.id)}
                className="gap-1.5 text-slate-400 hover:text-slate-600"
              >
                <X className="h-3.5 w-3.5" />
              </Button>
              <Button
                size="sm"
                onClick={() => onRequestIntro(match.id)}
                className="gap-1.5"
              >
                <Send className="h-3.5 w-3.5" />
                Request Intro
              </Button>
            </>
          )}
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => setExpanded(!expanded)}
          className="gap-1 text-slate-400"
        >
          {expanded ? (
            <>Less <ChevronUp className="h-3.5 w-3.5" /></>
          ) : (
            <>Details <ChevronDown className="h-3.5 w-3.5" /></>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}
