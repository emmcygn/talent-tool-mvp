"use client";

import { Button } from "@/components/ui/button";
import { Star, FolderPlus, Send } from "lucide-react";
import { toast } from "sonner";

interface MatchActionsProps {
  onShortlist: () => void;
  onAddToCollection: () => void;
  onRefer: () => void;
}

export function MatchActions({ onShortlist, onAddToCollection, onRefer }: MatchActionsProps) {
  const handleShortlist = () => {
    onShortlist();
    toast.success("Candidate shortlisted");
  };

  const handleAddToCollection = () => {
    onAddToCollection();
    toast.success("Added to collection");
  };

  const handleRefer = () => {
    onRefer();
    toast.success("Handoff initiated");
  };

  return (
    <div className="flex items-center gap-1">
      <Button size="sm" variant="ghost" onClick={handleShortlist} title="Shortlist">
        <Star className="h-4 w-4" />
      </Button>
      <Button size="sm" variant="ghost" onClick={handleAddToCollection} title="Add to collection">
        <FolderPlus className="h-4 w-4" />
      </Button>
      <Button size="sm" variant="ghost" onClick={handleRefer} title="Send as handoff">
        <Send className="h-4 w-4" />
      </Button>
    </div>
  );
}
