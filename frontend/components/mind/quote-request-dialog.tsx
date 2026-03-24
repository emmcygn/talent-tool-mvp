"use client";

import { useState, useEffect } from "react";
import type { Quote, CandidateAnonymized } from "@/contracts/canonical";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import { QuoteCard } from "./quote-card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api-client";

interface QuoteRequestDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  candidate: CandidateAnonymized | null;
  roleId: string;
  onQuoteAccepted?: (quote: Quote) => void;
}

export function QuoteRequestDialog({
  open, onOpenChange, candidate, roleId, onQuoteAccepted,
}: QuoteRequestDialogProps) {
  const [quote, setQuote] = useState<Quote | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && candidate && !quote) {
      generateQuote();
    }
    if (!open) {
      setQuote(null);
      setError(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, candidate]);

  async function generateQuote() {
    if (!candidate) return;
    setLoading(true);
    setError(null);
    try {
      const q = await apiClient.quotes.request({ candidate_id: candidate.id, role_id: roleId });
      setQuote(q);
    } catch {
      setError("Failed to generate quote. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleAccept() {
    if (!quote) return;
    onQuoteAccepted?.(quote);
    onOpenChange(false);
  }

  function handleDecline() {
    onOpenChange(false);
    setQuote(null);
  }

  const candidateName = candidate
    ? `${candidate.first_name} ${candidate.last_initial}.`
    : "Candidate";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>Request Introduction</DialogTitle>
          <DialogDescription>
            Review the placement fee for {candidateName} before requesting an introduction.
          </DialogDescription>
        </DialogHeader>

        <div className="py-2">
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-40 w-full rounded-lg" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : error ? (
            <div className="text-center py-6">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          ) : quote ? (
            <QuoteCard
              quote={quote}
              candidateName={candidateName}
              onAccept={handleAccept}
              onDecline={handleDecline}
            />
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
