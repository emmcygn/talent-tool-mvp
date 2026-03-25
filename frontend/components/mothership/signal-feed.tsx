"use client";

import type { Signal } from "@/contracts/canonical";
import { Skeleton } from "@/components/ui/skeleton";
import { formatRelativeTime } from "@/lib/utils";
import {
  UserPlus, Eye, Star, XCircle, Zap, Send, CheckCircle2,
  DollarSign, Briefcase, MessageSquare,
} from "lucide-react";

const signalConfig: Record<string, {
  icon: React.ElementType;
  color: string;
  format: (s: Signal) => string;
}> = {
  candidate_ingested: {
    icon: UserPlus,
    color: "text-blue-500 bg-blue-500/10",
    format: () => "New candidate ingested",
  },
  candidate_viewed: {
    icon: Eye,
    color: "text-muted-foreground bg-muted",
    format: () => "Candidate profile viewed",
  },
  candidate_shortlisted: {
    icon: Star,
    color: "text-amber-500 bg-amber-500/10",
    format: () => "Candidate shortlisted",
  },
  candidate_dismissed: {
    icon: XCircle,
    color: "text-red-400 bg-red-500/10",
    format: () => "Candidate dismissed",
  },
  match_generated: {
    icon: Zap,
    color: "text-purple-500 bg-purple-50",
    format: () => "New matches generated",
  },
  intro_requested: {
    icon: UserPlus,
    color: "text-green-500 bg-emerald-500/10",
    format: () => "Introduction requested",
  },
  handoff_sent: {
    icon: Send,
    color: "text-blue-500 bg-blue-500/10",
    format: () => "Handoff sent",
  },
  handoff_accepted: {
    icon: CheckCircle2,
    color: "text-green-500 bg-emerald-500/10",
    format: () => "Handoff accepted",
  },
  handoff_declined: {
    icon: XCircle,
    color: "text-red-400 bg-red-500/10",
    format: () => "Handoff declined",
  },
  quote_generated: {
    icon: DollarSign,
    color: "text-emerald-400 bg-emerald-500/10",
    format: () => "Quote generated",
  },
  placement_made: {
    icon: Briefcase,
    color: "text-emerald-400 bg-emerald-500/10",
    format: () => "Placement confirmed",
  },
  copilot_query: {
    icon: MessageSquare,
    color: "text-violet-500 bg-violet-50",
    format: () => "Copilot query",
  },
};

interface SignalFeedProps {
  signals: Signal[];
  loading?: boolean;
  maxItems?: number;
}

export function SignalFeed({ signals, loading, maxItems = 10 }: SignalFeedProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-8 w-8 rounded-full" />
            <div className="flex-1">
              <Skeleton className="h-4 w-48 mb-1" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (signals.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-6">
        No recent activity.
      </p>
    );
  }

  return (
    <div className="space-y-1">
      {signals.slice(0, maxItems).map((signal) => {
        const config = signalConfig[signal.event_type] || {
          icon: Zap,
          color: "text-muted-foreground bg-muted",
          format: () => signal.event_type.replace(/_/g, " "),
        };
        const Icon = config.icon;

        return (
          <div
            key={signal.id}
            className="flex items-center gap-3 rounded-md px-2 py-2 hover:bg-muted transition-colors"
          >
            <div className={`shrink-0 rounded-full p-1.5 ${config.color}`}>
              <Icon className="h-3.5 w-3.5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm truncate">{config.format(signal)}</p>
            </div>
            <span className="text-[11px] text-muted-foreground shrink-0">
              {formatRelativeTime(signal.created_at)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
