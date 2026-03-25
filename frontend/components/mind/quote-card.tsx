"use client";

import type { Quote, QuoteStatus } from "@/contracts/canonical";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { formatCurrency, formatDate } from "@/lib/utils";
import { CheckCircle2, XCircle, Clock, Sparkles, Tag, ArrowDown } from "lucide-react";

const statusConfig: Record<QuoteStatus, {
  label: string;
  className: string;
  icon: React.ElementType;
}> = {
  generated: { label: "Ready", className: "border-blue-300 bg-blue-500/10 text-blue-400", icon: Sparkles },
  sent: { label: "Sent", className: "border-amber-500/20 bg-amber-500/10 text-amber-400", icon: Clock },
  accepted: { label: "Accepted", className: "border-emerald-500/20 bg-emerald-500/10 text-emerald-400", icon: CheckCircle2 },
  declined: { label: "Declined", className: "border-red-300 bg-red-500/10 text-red-400", icon: XCircle },
  expired: { label: "Expired", className: "border-border bg-muted text-muted-foreground", icon: Clock },
};

interface QuoteCardProps {
  quote: Quote;
  candidateName?: string;
  roleTitle?: string;
  onAccept?: () => void;
  onDecline?: () => void;
  compact?: boolean;
}

export function QuoteCard({
  quote, candidateName, roleTitle, onAccept, onDecline, compact,
}: QuoteCardProps) {
  const status = statusConfig[quote.status];
  const StatusIcon = status.icon;
  const hasDiscount = quote.is_pool_candidate && quote.pool_discount;
  const savingAmount = hasDiscount ? quote.base_fee - quote.final_fee : 0;

  if (compact) {
    return (
      <div className="flex items-center justify-between rounded-lg border p-3">
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium truncate">{candidateName ?? "Candidate"}</div>
          <div className="text-xs text-muted-foreground">{roleTitle ?? "Role"}</div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold">{formatCurrency(quote.final_fee)}</span>
          <Badge variant="outline" className={status.className}>
            <StatusIcon className="h-3 w-3 mr-1" />
            {status.label}
          </Badge>
        </div>
      </div>
    );
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{candidateName ?? "Candidate"}</CardTitle>
            <p className="text-sm text-muted-foreground mt-0.5">
              {roleTitle ?? "Role"} &middot; Quoted {formatDate(quote.created_at)}
            </p>
          </div>
          <Badge variant="outline" className={status.className}>
            <StatusIcon className="h-3 w-3 mr-1" />
            {status.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {/* Fee breakdown */}
        <div className="rounded-lg bg-muted p-4 space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Standard placement fee</span>
            <span className="font-medium">{formatCurrency(quote.base_fee)}</span>
          </div>

          {hasDiscount && (
            <>
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <Tag className="h-3.5 w-3.5" />
                  Pre-vetted talent network discount
                </span>
                <span className="font-medium text-emerald-400">
                  -{formatCurrency(savingAmount)}
                </span>
              </div>
              <div className="flex items-center justify-center">
                <ArrowDown className="h-4 w-4 text-muted-foreground" />
              </div>
            </>
          )}

          <Separator />

          <div className="flex items-center justify-between">
            <span className="font-semibold">
              {hasDiscount ? "Your fee" : "Placement fee"}
            </span>
            <span className="text-xl font-bold">{formatCurrency(quote.final_fee)}</span>
          </div>

          {hasDiscount && (
            <div className="rounded-md bg-emerald-500/10 border border-emerald-500/20 px-3 py-2 text-center">
              <p className="text-sm font-medium text-emerald-400">
                You save {formatCurrency(savingAmount)} with our pre-vetted talent network
              </p>
            </div>
          )}
        </div>

        {/* Expiry */}
        <p className="text-xs text-muted-foreground text-center mt-3">
          Quote valid until {formatDate(quote.expires_at)}
        </p>

        {/* Actions */}
        {(quote.status === "generated" || quote.status === "sent") && onAccept && onDecline && (
          <div className="flex gap-3 mt-4">
            <Button className="flex-1" onClick={onAccept}>
              <CheckCircle2 className="h-4 w-4 mr-1.5" />
              Accept &amp; Request Intro
            </Button>
            <Button variant="outline" className="flex-1" onClick={onDecline}>
              Decline
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
