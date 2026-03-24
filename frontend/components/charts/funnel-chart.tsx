"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";

interface FunnelStage {
  label: string;
  value: number;
  color: string;
}

interface FunnelChartProps {
  stages: FunnelStage[];
  className?: string;
}

export function FunnelChart({ stages, className }: FunnelChartProps) {
  const maxValue = Math.max(...stages.map((s) => s.value));

  const withDropoff = useMemo(() => {
    return stages.map((stage, i) => ({
      ...stage,
      percentage: maxValue > 0 ? (stage.value / maxValue) * 100 : 0,
      dropoff: i > 0
        ? Math.round(((stages[i - 1].value - stage.value) / stages[i - 1].value) * 100)
        : null,
    }));
  }, [stages, maxValue]);

  return (
    <div className={cn("space-y-2", className)}>
      {withDropoff.map((stage, i) => (
        <div key={stage.label}>
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium">{stage.label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold">{stage.value.toLocaleString()}</span>
                  {stage.dropoff !== null && stage.dropoff > 0 && (
                    <span className="text-xs text-red-500">-{stage.dropoff}%</span>
                  )}
                </div>
              </div>
              <div className="h-8 rounded-md bg-slate-100 overflow-hidden">
                <div
                  className="h-full rounded-md transition-all duration-500"
                  style={{
                    width: `${stage.percentage}%`,
                    backgroundColor: stage.color,
                  }}
                />
              </div>
            </div>
          </div>
          {i < withDropoff.length - 1 && (
            <div className="flex justify-center py-0.5">
              <div className="w-px h-3 bg-slate-200" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
