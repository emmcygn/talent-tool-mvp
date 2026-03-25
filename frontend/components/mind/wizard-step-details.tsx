"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { RemotePolicy } from "@/contracts/canonical";
import type { WizardFormData } from "./role-wizard";

interface WizardStepDetailsProps {
  salaryMin: number | null;
  salaryMax: number | null;
  currency: string;
  location: string;
  remotePolicy: RemotePolicy;
  onChange: (updates: Partial<WizardFormData>) => void;
}

const REMOTE_OPTIONS: { value: RemotePolicy; label: string; description: string }[] = [
  { value: "onsite", label: "On-site", description: "Full-time in the office" },
  { value: "hybrid", label: "Hybrid", description: "Mix of office and remote" },
  { value: "remote", label: "Remote", description: "Fully remote, work from anywhere" },
];

export function WizardStepDetails({
  salaryMin,
  salaryMax,
  currency,
  location,
  remotePolicy,
  onChange,
}: WizardStepDetailsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-foreground mb-1">Role details</h2>
        <p className="text-sm text-muted-foreground">
          Add salary, location, and work arrangement. All fields are optional.
        </p>
      </div>

      <div className="space-y-3">
        <Label>Salary Band</Label>
        <div className="flex items-center gap-3">
          <Select value={currency} onValueChange={(val) => val && onChange({ currency: val })}>
            <SelectTrigger className="w-24">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="GBP">GBP</SelectItem>
              <SelectItem value="USD">USD</SelectItem>
              <SelectItem value="EUR">EUR</SelectItem>
            </SelectContent>
          </Select>
          <Input
            type="number"
            placeholder="Min"
            value={salaryMin ?? ""}
            onChange={(e) => onChange({ salary_min: e.target.value ? Number(e.target.value) : null })}
            className="w-32"
          />
          <span className="text-muted-foreground/60">to</span>
          <Input
            type="number"
            placeholder="Max"
            value={salaryMax ?? ""}
            onChange={(e) => onChange({ salary_max: e.target.value ? Number(e.target.value) : null })}
            className="w-32"
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="location">Location</Label>
        <Input
          id="location"
          value={location}
          onChange={(e) => onChange({ location: e.target.value })}
          placeholder="e.g. London, Manchester, or Remote"
        />
      </div>

      <div className="space-y-3">
        <Label>Work Arrangement</Label>
        <div className="grid grid-cols-3 gap-3">
          {REMOTE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange({ remote_policy: opt.value })}
              className={`rounded-lg border p-4 text-left transition-all ${
                remotePolicy === opt.value
                  ? "border-slate-900 bg-muted ring-1 ring-slate-900"
                  : "border-border hover:border-border"
              }`}
            >
              <p className="text-sm font-medium text-foreground">{opt.label}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{opt.description}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
