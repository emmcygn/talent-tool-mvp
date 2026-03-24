"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { MapPin, Clock, Briefcase } from "lucide-react";
import type { Candidate, CandidateAnonymized, SeniorityLevel, AvailabilityStatus } from "@/contracts/canonical";
import { cn } from "@/lib/utils";

interface CandidateCardProps {
  candidate: Candidate | CandidateAnonymized;
  anonymized?: boolean;
  isPoolCandidate?: boolean;
  onClick?: () => void;
  className?: string;
}

const SENIORITY_LABELS: Record<SeniorityLevel, string> = {
  junior: "Junior",
  mid: "Mid-level",
  senior: "Senior",
  lead: "Lead",
  principal: "Principal",
};

const AVAILABILITY_LABELS: Record<AvailabilityStatus, string> = {
  immediate: "Available now",
  "1_month": "1 month notice",
  "3_months": "3 months notice",
  not_looking: "Not looking",
};

const AVAILABILITY_COLORS: Record<AvailabilityStatus, string> = {
  immediate: "text-green-600",
  "1_month": "text-amber-600",
  "3_months": "text-slate-500",
  not_looking: "text-slate-400",
};

export function CandidateCard({
  candidate,
  anonymized = false,
  isPoolCandidate = false,
  onClick,
  className,
}: CandidateCardProps) {
  const displayName = anonymized && "last_initial" in candidate
    ? `${candidate.first_name} ${candidate.last_initial}.`
    : "last_name" in candidate
      ? `${candidate.first_name} ${candidate.last_name}`
      : candidate.first_name;

  const initials = candidate.first_name.charAt(0).toUpperCase();

  return (
    <Card
      className={cn(
        "transition-all hover:shadow-md",
        onClick && "cursor-pointer",
        className
      )}
      onClick={onClick}
    >
      <CardHeader className="flex flex-row items-start gap-4 pb-3">
        <Avatar className="h-10 w-10">
          <AvatarFallback className="bg-slate-100 text-sm font-medium">
            {initials}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-slate-900 truncate">{displayName}</h3>
            {isPoolCandidate && (
              <Badge variant="secondary" className="bg-blue-50 text-blue-700 text-xs shrink-0">
                Pre-vetted
              </Badge>
            )}
          </div>
          {candidate.seniority && (
            <p className="text-sm text-slate-500">{SENIORITY_LABELS[candidate.seniority]}</p>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pt-0">
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
          {candidate.location && (
            <span className="flex items-center gap-1 text-slate-500">
              <MapPin className="h-3.5 w-3.5" />
              {candidate.location}
            </span>
          )}
          {candidate.availability && (
            <span className={cn("flex items-center gap-1", AVAILABILITY_COLORS[candidate.availability])}>
              <Clock className="h-3.5 w-3.5" />
              {AVAILABILITY_LABELS[candidate.availability]}
            </span>
          )}
          {candidate.industries.length > 0 && (
            <span className="flex items-center gap-1 text-slate-500">
              <Briefcase className="h-3.5 w-3.5" />
              {candidate.industries.slice(0, 2).join(", ")}
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-1.5">
          {candidate.skills.slice(0, 5).map((skill) => (
            <Badge key={skill.name} variant="outline" className="text-xs font-normal">
              {skill.name}
              {skill.years && <span className="ml-1 text-slate-400">{skill.years}y</span>}
            </Badge>
          ))}
          {candidate.skills.length > 5 && (
            <Badge variant="outline" className="text-xs font-normal text-slate-400">
              +{candidate.skills.length - 5}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
