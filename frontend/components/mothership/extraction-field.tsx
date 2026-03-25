"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Pencil, Check, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ExtractionFieldProps {
  label: string;
  value: string;
  visible: boolean;
  confidence: number | null;
  lowConfidence?: boolean;
  editable?: boolean;
  onEdit?: () => void;
}

export function ExtractionField({
  label,
  value,
  visible,
  lowConfidence = false,
  editable = false,
  onEdit,
}: ExtractionFieldProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);

  if (!visible) return null;

  return (
    <div
      className={cn(
        "group flex items-center gap-4 py-2 transition-all duration-500 animate-in fade-in slide-in-from-left-2",
        lowConfidence && "bg-amber-500/10 -mx-4 px-4 rounded-md border border-amber-100"
      )}
    >
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider w-32 shrink-0">
        {label}
      </p>

      {isEditing ? (
        <div className="flex items-center gap-2 flex-1">
          <Input
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            className="h-8 text-sm"
          />
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setIsEditing(false)}
          >
            <Check className="h-4 w-4 text-emerald-400" />
          </Button>
        </div>
      ) : (
        <div className="flex items-center gap-2 flex-1">
          <span className={cn("text-sm", lowConfidence ? "text-amber-400" : "text-foreground")}>
            {value}
          </span>
          {lowConfidence && (
            <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0" />
          )}
          {editable && (
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 opacity-0 group-hover:opacity-100"
              onClick={() => {
                setIsEditing(true);
                onEdit?.();
              }}
            >
              <Pencil className="h-3 w-3 text-muted-foreground/60" />
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
