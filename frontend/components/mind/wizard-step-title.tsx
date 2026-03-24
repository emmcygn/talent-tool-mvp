"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { WizardFormData } from "./role-wizard";

interface WizardStepTitleProps {
  title: string;
  department: string;
  onChange: (updates: Partial<WizardFormData>) => void;
}

export function WizardStepTitle({ title, department, onChange }: WizardStepTitleProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-slate-900 mb-1">What role are you hiring for?</h2>
        <p className="text-sm text-slate-500">Start with the basics.</p>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="title">Role Title</Label>
          <Input
            id="title"
            value={title}
            onChange={(e) => onChange({ title: e.target.value })}
            placeholder="e.g. Senior Backend Engineer"
            className="text-lg h-12"
            autoFocus
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="department">Department (optional)</Label>
          <Input
            id="department"
            value={department}
            onChange={(e) => onChange({ department: e.target.value })}
            placeholder="e.g. Engineering, Product, Data"
          />
        </div>
      </div>
    </div>
  );
}
