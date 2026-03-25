"use client";

import { userFullName } from "@/contracts/canonical";
import type { Handoff, User } from "@/contracts/canonical";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { HandoffStatusBadge } from "./handoff-status-badge";
import { Users, ArrowRight, MessageSquare, LinkIcon } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

interface HandoffCardProps {
  handoff: Handoff;
  sender?: User;
  receiver?: User;
  direction: "inbox" | "outbox";
  onAccept?: () => void;
  onDecline?: () => void;
  onViewDetail?: () => void;
}

export function HandoffCard({
  handoff, sender, receiver, direction, onAccept, onDecline, onViewDetail,
}: HandoffCardProps) {
  const otherParty = direction === "inbox" ? sender : receiver;
  const initials = otherParty
    ? `${otherParty.first_name[0]}${otherParty.last_name[0]}`.toUpperCase()
    : "??";

  return (
    <Card className="hover:shadow-sm transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          {/* Left: sender info + context */}
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <Avatar className="h-9 w-9 shrink-0">
              <AvatarFallback className="text-xs bg-muted">
                {initials}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-medium text-sm">
                  {direction === "inbox" ? (sender ? userFullName(sender) : "Unknown") : (receiver ? userFullName(receiver) : "Unknown")}
                </span>
                <ArrowRight className="h-3 w-3 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  {direction === "inbox" ? "you" : (receiver ? userFullName(receiver) : "Unknown")}
                </span>
                <HandoffStatusBadge status={handoff.status} />
              </div>

              {/* Candidate count */}
              <div className="flex items-center gap-1 text-sm text-muted-foreground mt-1">
                <Users className="h-3.5 w-3.5" />
                <span>
                  {handoff.candidate_ids.length} candidate{handoff.candidate_ids.length !== 1 ? "s" : ""}
                </span>
                {handoff.target_role_id && (
                  <>
                    <span className="mx-1">&middot;</span>
                    <LinkIcon className="h-3.5 w-3.5" />
                    <span>Linked to role</span>
                  </>
                )}
                <span className="mx-1">&middot;</span>
                <span>{formatRelativeTime(handoff.created_at)}</span>
              </div>

              {/* Context notes */}
              {handoff.context_notes && (
                <div className="mt-2 flex items-start gap-1.5">
                  <MessageSquare className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {handoff.context_notes}
                  </p>
                </div>
              )}

              {/* Response notes */}
              {handoff.response_notes && (
                <div className="mt-1.5 rounded-md bg-muted px-3 py-2">
                  <p className="text-sm text-muted-foreground italic">
                    &ldquo;{handoff.response_notes}&rdquo;
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Right: actions */}
          <div className="flex items-center gap-2 ml-4 shrink-0">
            {direction === "inbox" && handoff.status === "pending" && (
              <>
                <Button size="sm" onClick={onAccept}>
                  Accept
                </Button>
                <Button size="sm" variant="outline" onClick={onDecline}>
                  Decline
                </Button>
              </>
            )}
            <Button size="sm" variant="ghost" onClick={onViewDetail}>
              View
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
