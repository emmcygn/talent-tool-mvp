import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface MetricTileProps {
  label: string;
  value: string | number;
  subtitle?: string;
  trend?: { value: number; label: string };
  icon?: React.ReactNode;
  loading?: boolean;
  className?: string;
}

export function MetricTile({
  label, value, subtitle, trend, icon, loading, className,
}: MetricTileProps) {
  if (loading) {
    return (
      <Card className={cn("p-4", className)}>
        <Skeleton className="h-4 w-24 mb-2" />
        <Skeleton className="h-8 w-16 mb-1" />
        <Skeleton className="h-3 w-32" />
      </Card>
    );
  }

  return (
    <Card className={cn("p-4", className)}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
          {label}
        </span>
        {icon && <span className="text-muted-foreground">{icon}</span>}
      </div>
      <div className="text-2xl font-bold tracking-tight">{value}</div>
      <div className="flex items-center gap-2 mt-1">
        {subtitle && (
          <span className="text-xs text-muted-foreground">{subtitle}</span>
        )}
        {trend && (
          <span className={cn(
            "flex items-center gap-0.5 text-xs font-medium",
            trend.value > 0 && "text-green-600",
            trend.value < 0 && "text-red-600",
            trend.value === 0 && "text-muted-foreground"
          )}>
            {trend.value > 0 && <TrendingUp className="h-3 w-3" />}
            {trend.value < 0 && <TrendingDown className="h-3 w-3" />}
            {trend.value === 0 && <Minus className="h-3 w-3" />}
            {trend.label}
          </span>
        )}
      </div>
    </Card>
  );
}
