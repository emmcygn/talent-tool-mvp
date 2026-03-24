"use client";

import type { Handoff, Signal } from "@/contracts/canonical";
import { formatRelativeTime } from "@/lib/utils";
import { UserPlus, Send, CheckCircle2, XCircle, Briefcase, Star } from "lucide-react";

interface TimelineEvent {
  type: string;
  label: string;
  description: string;
  timestamp: string;
  icon: React.ElementType;
  color: string;
}

interface HandoffTimelineProps {
  handoff: Handoff;
  relatedSignals?: Signal[];
}

export function HandoffTimeline({ handoff, relatedSignals = [] }: HandoffTimelineProps) {
  const events: TimelineEvent[] = [
    {
      type: "created",
      label: "Handoff Sent",
      description: `${handoff.candidate_ids.length} candidate(s) shared`,
      timestamp: handoff.created_at,
      icon: Send,
      color: "text-blue-500 bg-blue-50",
    },
  ];

  if (handoff.responded_at) {
    events.push({
      type: handoff.status,
      label: handoff.status === "accepted" ? "Handoff Accepted" : "Handoff Declined",
      description: handoff.response_notes ?? "",
      timestamp: handoff.responded_at,
      icon: handoff.status === "accepted" ? CheckCircle2 : XCircle,
      color: handoff.status === "accepted"
        ? "text-green-500 bg-green-50"
        : "text-red-500 bg-red-50",
    });
  }

  // Add signals as timeline events
  relatedSignals.forEach((signal) => {
    let icon: React.ElementType = Star;
    let label = signal.event_type.replace(/_/g, " ");
    let color = "text-slate-500 bg-slate-50";

    if (signal.event_type === "candidate_shortlisted") {
      icon = Star;
      label = "Candidate Shortlisted";
      color = "text-amber-500 bg-amber-50";
    } else if (signal.event_type === "placement_made") {
      icon = Briefcase;
      label = "Placement Made";
      color = "text-green-600 bg-green-50";
    } else if (signal.event_type === "intro_requested") {
      icon = UserPlus;
      label = "Intro Requested";
      color = "text-purple-500 bg-purple-50";
    }

    events.push({
      type: signal.event_type,
      label,
      description: "",
      timestamp: signal.created_at,
      icon,
      color,
    });
  });

  // Sort chronologically
  events.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  return (
    <div className="relative space-y-0">
      {events.map((event, i) => {
        const Icon = event.icon;
        return (
          <div key={`${event.type}-${event.timestamp}-${i}`} className="flex gap-3 pb-6 last:pb-0">
            {/* Timeline line */}
            <div className="flex flex-col items-center">
              <div className={`rounded-full p-1.5 ${event.color}`}>
                <Icon className="h-3.5 w-3.5" />
              </div>
              {i < events.length - 1 && (
                <div className="w-px flex-1 bg-slate-200 mt-1" />
              )}
            </div>
            {/* Content */}
            <div className="flex-1 min-w-0 pt-0.5">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{event.label}</span>
                <span className="text-xs text-muted-foreground">
                  {formatRelativeTime(event.timestamp)}
                </span>
              </div>
              {event.description && (
                <p className="text-sm text-muted-foreground mt-0.5">{event.description}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
