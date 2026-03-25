import type { HandoffStatus } from "@/contracts/canonical";
import { Badge } from "@/components/ui/badge";
import { Clock, CheckCircle2, XCircle, Timer } from "lucide-react";

const statusConfig: Record<HandoffStatus, {
  label: string;
  variant: "default" | "secondary" | "destructive" | "outline";
  className: string;
  icon: React.ElementType;
}> = {
  pending: {
    label: "Pending",
    variant: "outline",
    className: "border-amber-500/20 bg-amber-500/10 text-amber-400",
    icon: Clock,
  },
  accepted: {
    label: "Accepted",
    variant: "outline",
    className: "border-emerald-500/20 bg-emerald-500/10 text-emerald-400",
    icon: CheckCircle2,
  },
  declined: {
    label: "Declined",
    variant: "outline",
    className: "border-red-300 bg-red-500/10 text-red-400",
    icon: XCircle,
  },
  expired: {
    label: "Expired",
    variant: "outline",
    className: "border-border bg-muted text-muted-foreground",
    icon: Timer,
  },
};

interface HandoffStatusBadgeProps {
  status: HandoffStatus;
}

export function HandoffStatusBadge({ status }: HandoffStatusBadgeProps) {
  const config = statusConfig[status];
  const Icon = config.icon;
  return (
    <Badge variant={config.variant} className={config.className}>
      <Icon className="h-3 w-3 mr-1" />
      {config.label}
    </Badge>
  );
}
