import { Badge } from "@/components/ui/badge";
import type { CandidateSource } from "@/contracts/canonical";
import { formatRelativeTime } from "@/lib/utils";

interface SourceBadgeProps {
  source: CandidateSource;
}

const ADAPTER_COLORS: Record<string, string> = {
  bullhorn: "bg-orange-50 text-orange-700 border-orange-200",
  hubspot: "bg-rose-50 text-rose-700 border-rose-200",
  linkedin: "bg-blue-50 text-blue-700 border-blue-200",
  manual: "bg-slate-50 text-slate-700 border-slate-200",
};

const ADAPTER_LABELS: Record<string, string> = {
  bullhorn: "Bullhorn",
  hubspot: "HubSpot",
  linkedin: "LinkedIn",
  manual: "Manual Upload",
};

export function SourceBadge({ source }: SourceBadgeProps) {
  const colorClass = ADAPTER_COLORS[source.adapter_name] ?? ADAPTER_COLORS.manual;
  const label = ADAPTER_LABELS[source.adapter_name] ?? source.adapter_name;

  return (
    <Badge variant="outline" className={`text-xs ${colorClass}`}>
      {label} &middot; {formatRelativeTime(source.ingested_at)}
    </Badge>
  );
}
