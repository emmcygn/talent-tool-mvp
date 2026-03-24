import { Badge } from "@/components/ui/badge";
import type { ConfidenceLevel } from "@/contracts/canonical";
import { cn, confidenceColor } from "@/lib/utils";

interface ConfidenceBadgeProps {
  confidence: ConfidenceLevel;
  className?: string;
}

const LABELS: Record<ConfidenceLevel, string> = {
  strong: "Strong Match",
  good: "Good Match",
  possible: "Worth Considering",
};

export function ConfidenceBadge({ confidence, className }: ConfidenceBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "text-xs font-medium border",
        confidenceColor(confidence),
        className
      )}
    >
      {LABELS[confidence]}
    </Badge>
  );
}
