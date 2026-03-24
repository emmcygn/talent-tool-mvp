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
    className: "border-amber-300 bg-amber-50 text-amber-700",
    icon: Clock,
  },
  accepted: {
    label: "Accepted",
    variant: "outline",
    className: "border-green-300 bg-green-50 text-green-700",
    icon: CheckCircle2,
  },
  declined: {
    label: "Declined",
    variant: "outline",
    className: "border-red-300 bg-red-50 text-red-700",
    icon: XCircle,
  },
  expired: {
    label: "Expired",
    variant: "outline",
    className: "border-slate-300 bg-slate-50 text-slate-500",
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
