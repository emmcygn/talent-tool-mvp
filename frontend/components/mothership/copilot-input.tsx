"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { SendHorizontal, Sparkles } from "lucide-react";

interface CopilotInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  suggestions: string[];
}

export function CopilotInput({ onSend, isLoading, suggestions }: CopilotInputProps) {
  const [value, setValue] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(true);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function handleSubmit() {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setValue("");
    setShowSuggestions(false);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  function handleSuggestionClick(suggestion: string) {
    onSend(suggestion);
    setShowSuggestions(false);
  }

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 120) + "px";
    }
  }, [value]);

  return (
    <div className="space-y-2">
      {showSuggestions && suggestions.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {suggestions.map((s, i) => (
            <button
              key={i}
              onClick={() => handleSuggestionClick(s)}
              className="text-xs rounded-full border border-violet-200 bg-violet-50 text-violet-700 px-2.5 py-1 hover:bg-violet-100 transition-colors"
            >
              <Sparkles className="h-3 w-3 inline mr-1" />
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2 rounded-lg border bg-white p-2">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => { setValue(e.target.value); setShowSuggestions(false); }}
          onKeyDown={handleKeyDown}
          placeholder="Ask about candidates, roles, matches..."
          className="min-h-[36px] max-h-[120px] resize-none border-0 focus-visible:ring-0 p-1 text-sm"
          rows={1}
        />
        <Button
          size="icon"
          onClick={handleSubmit}
          disabled={!value.trim() || isLoading}
          className="shrink-0 h-8 w-8"
        >
          <SendHorizontal className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
