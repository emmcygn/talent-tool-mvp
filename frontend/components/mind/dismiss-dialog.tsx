"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { X } from "lucide-react";

interface DismissDialogProps {
  onConfirm: (reason?: string) => void;
  onCancel: () => void;
}

const QUICK_REASONS = [
  "Not the right skill set",
  "Seniority mismatch",
  "Location does not work",
  "Already in process with this person",
  "Budget does not align",
];

export function DismissDialog({ onConfirm, onCancel }: DismissDialogProps) {
  const [reason, setReason] = useState("");

  return (
    <Dialog open onOpenChange={(open) => !open && onCancel()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Dismiss candidate</DialogTitle>
          <DialogDescription>
            Optionally share why this candidate is not a fit. This helps us improve future matches.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Quick reasons */}
          <div className="flex flex-wrap gap-2">
            {QUICK_REASONS.map((r) => (
              <Button
                key={r}
                variant={reason === r ? "default" : "outline"}
                size="sm"
                onClick={() => setReason(reason === r ? "" : r)}
                className="text-xs"
              >
                {r}
              </Button>
            ))}
          </div>

          {/* Custom reason */}
          <Textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Or type your own reason..."
            className="min-h-[80px]"
          />

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onCancel}>Cancel</Button>
            <Button
              variant="default"
              onClick={() => onConfirm(reason || undefined)}
              className="gap-1.5"
            >
              <X className="h-3.5 w-3.5" />
              Dismiss
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
