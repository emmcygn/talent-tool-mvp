import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

interface ActionCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  actionLabel: string;
  onClick: () => void;
  variant?: "default" | "highlight";
}

export function ActionCard({
  icon, title, description, actionLabel, onClick, variant = "default",
}: ActionCardProps) {
  return (
    <Card className={`p-4 transition-all hover:shadow-md ${
      variant === "highlight"
        ? "border-blue-500/20 bg-blue-500/10/50"
        : ""
    }`}>
      <div className="flex items-start gap-3">
        <div className={`shrink-0 rounded-lg p-2 ${
          variant === "highlight"
            ? "bg-blue-500/10 text-blue-400"
            : "bg-muted text-muted-foreground"
        }`}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold">{title}</h3>
          <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
          <Button
            variant="ghost"
            size="sm"
            className="mt-2 h-7 px-2 text-xs -ml-2"
            onClick={onClick}
          >
            {actionLabel}
            <ArrowRight className="h-3 w-3 ml-1" />
          </Button>
        </div>
      </div>
    </Card>
  );
}
