"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { GitMerge, Copy, X } from "lucide-react";
import type { Candidate } from "@/contracts/canonical";
import { SourceBadge } from "./source-badge";
import { cn } from "@/lib/utils";

interface DedupComparisonProps {
  newCandidate: Candidate;
  existingCandidate: Candidate;
  onMerge: () => void;
  onKeepBoth: () => void;
  onCancel: () => void;
}

interface FieldRowProps {
  label: string;
  newValue: string | null;
  existingValue: string | null;
}

function FieldRow({ label, newValue, existingValue }: FieldRowProps) {
  const match = newValue === existingValue;
  return (
    <div className="grid grid-cols-[140px_1fr_1fr] gap-4 py-2 items-center">
      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{label}</span>
      <span className={cn("text-sm", match ? "text-muted-foreground" : "text-blue-400 font-medium")}>
        {newValue ?? "—"}
      </span>
      <span className={cn("text-sm", match ? "text-muted-foreground" : "text-purple-400 font-medium")}>
        {existingValue ?? "—"}
      </span>
    </div>
  );
}

export function DedupComparison({
  newCandidate,
  existingCandidate,
  onMerge,
  onKeepBoth,
  onCancel,
}: DedupComparisonProps) {
  return (
    <Dialog open onOpenChange={(open) => !open && onCancel()}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitMerge className="h-5 w-5 text-amber-500" />
            Potential Duplicate Detected
          </DialogTitle>
          <DialogDescription>
            This candidate may already exist in the system. Compare the records below and decide how to proceed.
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-[140px_1fr_1fr] gap-4 py-2">
          <span />
          <div className="space-y-1">
            <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20">New Record</Badge>
            {newCandidate.sources.length > 0 && (
              <div><SourceBadge source={newCandidate.sources[0]} /></div>
            )}
          </div>
          <div className="space-y-1">
            <Badge variant="outline" className="bg-purple-50 text-purple-400 border-purple-200">Existing Record</Badge>
            {existingCandidate.sources.length > 0 && (
              <div><SourceBadge source={existingCandidate.sources[0]} /></div>
            )}
          </div>
        </div>

        <Separator />

        <div className="space-y-1">
          <FieldRow
            label="Name"
            newValue={`${newCandidate.first_name} ${newCandidate.last_name}`}
            existingValue={`${existingCandidate.first_name} ${existingCandidate.last_name}`}
          />
          <FieldRow label="Email" newValue={newCandidate.email} existingValue={existingCandidate.email} />
          <FieldRow label="Phone" newValue={newCandidate.phone} existingValue={existingCandidate.phone} />
          <FieldRow label="Location" newValue={newCandidate.location} existingValue={existingCandidate.location} />
          <FieldRow
            label="Seniority"
            newValue={newCandidate.seniority}
            existingValue={existingCandidate.seniority}
          />
          <FieldRow
            label="Skills"
            newValue={newCandidate.skills.map((s) => s.name).join(", ")}
            existingValue={existingCandidate.skills.map((s) => s.name).join(", ")}
          />
          <FieldRow
            label="Availability"
            newValue={newCandidate.availability?.replace("_", " ") ?? null}
            existingValue={existingCandidate.availability?.replace("_", " ") ?? null}
          />
        </div>

        <Separator />

        <div className="flex items-center justify-end gap-3">
          <Button variant="outline" onClick={onCancel} className="gap-2">
            <X className="h-4 w-4" />
            Cancel
          </Button>
          <Button variant="outline" onClick={onKeepBoth} className="gap-2">
            <Copy className="h-4 w-4" />
            Keep Both
          </Button>
          <Button onClick={onMerge} className="gap-2">
            <GitMerge className="h-4 w-4" />
            Merge Records
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
