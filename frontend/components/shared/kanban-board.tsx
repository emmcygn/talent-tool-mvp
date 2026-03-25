"use client";

import { useState, useCallback } from "react";
import { cn } from "@/lib/utils";

export interface KanbanStage {
  id: string;
  label: string;
  color: string; // Tailwind color class for header
}

export interface KanbanItem {
  id: string;
  stage: string;
}

interface KanbanBoardProps<T extends KanbanItem> {
  stages: KanbanStage[];
  items: T[];
  onMoveItem: (itemId: string, toStage: string) => void;
  renderItem: (item: T) => React.ReactNode;
  renderStageHeader?: (stage: KanbanStage, count: number) => React.ReactNode;
}

export function KanbanBoard<T extends KanbanItem>({
  stages, items, onMoveItem, renderItem, renderStageHeader,
}: KanbanBoardProps<T>) {
  const [dragItem, setDragItem] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState<string | null>(null);

  const handleDragStart = useCallback((itemId: string) => {
    setDragItem(itemId);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent, stageId: string) => {
    e.preventDefault();
    setDragOver(stageId);
  }, []);

  const handleDrop = useCallback((stageId: string) => {
    if (dragItem) {
      onMoveItem(dragItem, stageId);
    }
    setDragItem(null);
    setDragOver(null);
  }, [dragItem, onMoveItem]);

  const handleDragEnd = useCallback(() => {
    setDragItem(null);
    setDragOver(null);
  }, []);

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {stages.map((stage) => {
        const stageItems = items.filter((item) => item.stage === stage.id);
        const isOver = dragOver === stage.id;

        return (
          <div
            key={stage.id}
            className={cn(
              "flex-shrink-0 w-72 rounded-lg border bg-muted/50 transition-colors",
              isOver && "border-blue-300 bg-blue-500/10/30"
            )}
            onDragOver={(e) => handleDragOver(e, stage.id)}
            onDrop={() => handleDrop(stage.id)}
            onDragLeave={() => setDragOver(null)}
          >
            {/* Stage header */}
            <div className="p-3 border-b">
              {renderStageHeader ? (
                renderStageHeader(stage, stageItems.length)
              ) : (
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={cn("w-2 h-2 rounded-full", stage.color)} />
                    <span className="text-sm font-medium">{stage.label}</span>
                  </div>
                  <span className="text-xs text-muted-foreground bg-card rounded-full px-2 py-0.5 border">
                    {stageItems.length}
                  </span>
                </div>
              )}
            </div>

            {/* Items */}
            <div className="p-2 space-y-2 min-h-[200px]">
              {stageItems.map((item) => (
                <div
                  key={item.id}
                  draggable
                  onDragStart={() => handleDragStart(item.id)}
                  onDragEnd={handleDragEnd}
                  className={cn(
                    "cursor-grab active:cursor-grabbing transition-opacity",
                    dragItem === item.id && "opacity-50"
                  )}
                >
                  {renderItem(item)}
                </div>
              ))}
              {stageItems.length === 0 && (
                <div className="flex items-center justify-center h-24 text-xs text-muted-foreground border border-dashed rounded-md">
                  Drop here
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
