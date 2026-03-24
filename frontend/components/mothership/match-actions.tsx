"use client";

import { Button } from "@/components/ui/button";
import { Star, FolderPlus, Send } from "lucide-react";

interface MatchActionsProps {
  onShortlist: () => void;
  onAddToCollection: () => void;
  onRefer: () => void;
}

export function MatchActions({ onShortlist, onAddToCollection, onRefer }: MatchActionsProps) {
  return (
    <div className="flex items-center gap-1">
      <Button size="sm" variant="ghost" onClick={onShortlist} title="Shortlist">
        <Star className="h-4 w-4" />
      </Button>
      <Button size="sm" variant="ghost" onClick={onAddToCollection} title="Add to collection">
        <FolderPlus className="h-4 w-4" />
      </Button>
      <Button size="sm" variant="ghost" onClick={onRefer} title="Send as handoff">
        <Send className="h-4 w-4" />
      </Button>
    </div>
  );
}
