"use client";

import { useState } from "react";
import type { Candidate, HandoffCreate, Role, User } from "@/contracts/canonical";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Search, X, Send } from "lucide-react";

interface HandoffSendDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: HandoffCreate) => void;
  candidates: Candidate[];
  partners: User[];
  roles: Role[];
  preselectedCandidateIds?: string[];
}

export function HandoffSendDialog({
  open, onOpenChange, onSubmit,
  candidates, partners, roles,
  preselectedCandidateIds = [],
}: HandoffSendDialogProps) {
  const [selectedCandidates, setSelectedCandidates] = useState<string[]>(preselectedCandidateIds);
  const [toPartnerId, setToPartnerId] = useState<string>("");
  const [contextNotes, setContextNotes] = useState("");
  const [targetRoleId, setTargetRoleId] = useState<string | null>(null);
  const [candidateSearch, setCandidateSearch] = useState("");

  const filteredCandidates = candidates.filter(
    (c) =>
      `${c.first_name} ${c.last_name}`.toLowerCase().includes(candidateSearch.toLowerCase()) ||
      c.skills.some((s) => s.name.toLowerCase().includes(candidateSearch.toLowerCase()))
  );

  function toggleCandidate(id: string) {
    setSelectedCandidates((prev) =>
      prev.includes(id) ? prev.filter((cid) => cid !== id) : [...prev, id]
    );
  }

  function handleSubmit() {
    onSubmit({
      to_partner_id: toPartnerId,
      candidate_ids: selectedCandidates,
      context_notes: contextNotes,
      target_role_id: targetRoleId,
    });
    onOpenChange(false);
    // Reset
    setSelectedCandidates([]);
    setToPartnerId("");
    setContextNotes("");
    setTargetRoleId(null);
  }

  const canSubmit = selectedCandidates.length > 0 && toPartnerId && contextNotes.trim();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Send className="h-5 w-5" />
            Send Handoff
          </DialogTitle>
          <DialogDescription>
            Share candidates with another talent partner. Add context to help them understand why.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-2">
          {/* Step 1: Select candidates */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">
              1. Select Candidates
              {selectedCandidates.length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {selectedCandidates.length} selected
                </Badge>
              )}
            </Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                value={candidateSearch}
                onChange={(e) => setCandidateSearch(e.target.value)}
                placeholder="Search by name or skill..."
                className="pl-9"
              />
            </div>
            {/* Selected chips */}
            {selectedCandidates.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {selectedCandidates.map((id) => {
                  const candidate = candidates.find((item) => item.id === id);
                  return (
                    <Badge key={id} variant="secondary" className="gap-1 pr-1">
                      {candidate ? `${candidate.first_name} ${candidate.last_name}` : id}
                      <button
                        type="button"
                        onClick={() => toggleCandidate(id)}
                        className="ml-0.5 rounded-full p-0.5 hover:bg-slate-200"
                        aria-label="Remove candidate"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  );
                })}
              </div>
            )}
            <div className="max-h-40 overflow-y-auto rounded-md border">
              {filteredCandidates.slice(0, 15).map((c) => (
                <label
                  key={c.id}
                  className="flex items-center gap-3 px-3 py-2 hover:bg-slate-50 cursor-pointer border-b last:border-0"
                >
                  <input
                    type="checkbox"
                    checked={selectedCandidates.includes(c.id)}
                    onChange={() => toggleCandidate(c.id)}
                    className="rounded border-slate-300"
                  />
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium">
                      {c.first_name} {c.last_name}
                    </span>
                    <span className="text-xs text-muted-foreground ml-2">
                      {c.seniority} &middot; {c.location}
                    </span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Step 2: Pick partner */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">2. Send to Partner</Label>
            <Select value={toPartnerId} onValueChange={(val) => val && setToPartnerId(val)}>
              <SelectTrigger>
                <SelectValue placeholder="Select a partner..." />
              </SelectTrigger>
              <SelectContent>
                {partners.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Step 3: Context notes */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">3. Add Context</Label>
            <Textarea
              value={contextNotes}
              onChange={(e) => setContextNotes(e.target.value)}
              placeholder="Why are you sharing these candidates? Any relevant context for the receiving partner..."
              rows={3}
            />
          </div>

          {/* Step 4 (optional): Link role */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">
              4. Link to Role <span className="text-muted-foreground font-normal">(optional)</span>
            </Label>
            <Select
              value={targetRoleId ?? "none"}
              onValueChange={(val) => val && setTargetRoleId(val === "none" ? null : val)}
            >
              <SelectTrigger>
                <SelectValue placeholder="No role linked" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No role linked</SelectItem>
                {roles.map((r) => (
                  <SelectItem key={r.id} value={r.id}>
                    {r.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={!canSubmit}>
            <Send className="h-4 w-4 mr-1.5" />
            Send Handoff
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
