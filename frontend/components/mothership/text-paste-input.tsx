"use client";

import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Sparkles } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import type { Candidate } from "@/contracts/canonical";

interface TextPasteInputProps {
  onExtractionStart: () => void;
  onExtractionComplete: (candidate: Candidate) => void;
}

export function TextPasteInput({ onExtractionStart, onExtractionComplete }: TextPasteInputProps) {
  const [text, setText] = useState("");

  const handleExtract = async () => {
    if (!text.trim()) return;
    onExtractionStart();
    try {
      const candidate = await apiClient.candidates.extractFromText(text);
      onExtractionComplete(candidate);
    } catch (err) {
      console.error("Extraction failed:", err);
    }
  };

  return (
    <div className="space-y-4">
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste a candidate's CV text, LinkedIn profile summary, or any profile information here..."
        className="min-h-[200px] resize-y"
      />
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-400">
          {text.length > 0 ? `${text.length} characters` : "Paste any unstructured candidate text"}
        </p>
        <Button onClick={handleExtract} disabled={!text.trim()} className="gap-2">
          <Sparkles className="h-4 w-4" />
          Extract Profile
        </Button>
      </div>
    </div>
  );
}
