"use client";

import { useState } from "react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { CheckCircle2, XCircle } from "lucide-react";

interface HandoffRespondDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onRespond: (accept: boolean, notes: string) => void;
  action: "accept" | "decline";
}

export function HandoffRespondDialog({
  open, onOpenChange, onRespond, action,
}: HandoffRespondDialogProps) {
  const [notes, setNotes] = useState("");
  const isAccept = action === "accept";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isAccept ? (
              <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            ) : (
              <XCircle className="h-5 w-5 text-red-500" />
            )}
            {isAccept ? "Accept Handoff" : "Decline Handoff"}
          </DialogTitle>
          <DialogDescription>
            {isAccept
              ? "Accept these candidates into your pipeline. Add a note for the sender."
              : "Decline this handoff. Let the sender know why."}
          </DialogDescription>
        </DialogHeader>
        <div className="py-2">
          <Label htmlFor="respond-notes">
            {isAccept ? "Notes (optional)" : "Reason for declining"}
          </Label>
          <Textarea
            id="respond-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder={
              isAccept
                ? "Thanks! I'll review these candidates..."
                : "These don't match what I'm looking for because..."
            }
            rows={3}
            className="mt-1.5"
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button
            onClick={() => { onRespond(isAccept, notes); onOpenChange(false); }}
            variant={isAccept ? "default" : "destructive"}
          >
            {isAccept ? "Accept" : "Decline"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
