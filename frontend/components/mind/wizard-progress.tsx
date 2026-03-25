import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

interface WizardProgressProps {
  steps: string[];
  currentStep: number;
}

export function WizardProgress({ steps, currentStep }: WizardProgressProps) {
  return (
    <nav className="flex items-center justify-between mb-8">
      {steps.map((label, index) => {
        const isCompleted = index < currentStep;
        const isCurrent = index === currentStep;
        return (
          <div key={label} className="flex items-center flex-1 last:flex-initial">
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors",
                  isCompleted && "bg-slate-900 text-white",
                  isCurrent && "bg-slate-900 text-white ring-4 ring-slate-100",
                  !isCompleted && !isCurrent && "bg-muted text-muted-foreground/60"
                )}
              >
                {isCompleted ? <Check className="h-4 w-4" /> : index + 1}
              </div>
              <span
                className={cn(
                  "text-sm font-medium hidden sm:block",
                  isCurrent ? "text-foreground" : "text-muted-foreground/60"
                )}
              >
                {label}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div
                className={cn(
                  "flex-1 mx-4 h-px",
                  isCompleted ? "bg-slate-900" : "bg-slate-200"
                )}
              />
            )}
          </div>
        );
      })}
    </nav>
  );
}
