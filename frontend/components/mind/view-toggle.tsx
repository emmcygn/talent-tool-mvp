"use client";

import { Button } from "@/components/ui/button";
import { LayoutGrid, List } from "lucide-react";
import { cn } from "@/lib/utils";

interface ViewToggleProps {
  view: "grid" | "list";
  onChange: (view: "grid" | "list") => void;
}

export function ViewToggle({ view, onChange }: ViewToggleProps) {
  return (
    <div className="flex items-center rounded-lg border border-slate-200 p-0.5">
      <Button
        variant="ghost"
        size="icon"
        className={cn("h-8 w-8 rounded-md", view === "grid" && "bg-slate-100")}
        onClick={() => onChange("grid")}
      >
        <LayoutGrid className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className={cn("h-8 w-8 rounded-md", view === "list" && "bg-slate-100")}
        onClick={() => onChange("list")}
      >
        <List className="h-4 w-4" />
      </Button>
    </div>
  );
}
