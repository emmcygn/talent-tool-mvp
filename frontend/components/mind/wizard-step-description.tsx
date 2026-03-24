"use client";

import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import type { WizardFormData } from "./role-wizard";

interface WizardStepDescriptionProps {
  description: string;
  onChange: (updates: Partial<WizardFormData>) => void;
}

export function WizardStepDescription({ description, onChange }: WizardStepDescriptionProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-slate-900 mb-1">Describe the role</h2>
        <p className="text-sm text-slate-500">
          Write or paste the job description. Our AI will extract the key requirements automatically.
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Role Description</Label>
        <Textarea
          id="description"
          value={description}
          onChange={(e) => onChange({ description: e.target.value })}
          placeholder="We are looking for an experienced engineer to join our team. The ideal candidate will have strong experience in..."
          className="min-h-[250px] resize-y text-sm leading-relaxed"
          autoFocus
        />
        <div className="flex justify-between text-xs text-slate-400">
          <span>
            {description.length > 0
              ? `${description.length} characters`
              : "Tip: the more detail you provide, the better our matching will be"}
          </span>
          {description.length > 0 && description.length < 50 && (
            <span className="text-amber-500">Add more detail for better matching</span>
          )}
        </div>
      </div>
    </div>
  );
}
