"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Rocket, Loader2 } from "lucide-react";
import type { WizardFormData } from "./role-wizard";
import { formatCurrency } from "@/lib/utils";

interface WizardStepReviewProps {
  formData: WizardFormData;
  onPublish: () => void;
  publishing: boolean;
}

function ReviewRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start gap-4 py-3">
      <span className="text-sm text-muted-foreground w-36 shrink-0">{label}</span>
      <span className="text-sm text-foreground">{value}</span>
    </div>
  );
}

export function WizardStepReview({ formData, onPublish, publishing }: WizardStepReviewProps) {
  const salary =
    formData.salary_min || formData.salary_max
      ? `${formData.salary_min ? formatCurrency(formData.salary_min, formData.currency) : "?"} – ${formData.salary_max ? formatCurrency(formData.salary_max, formData.currency) : "?"}`
      : "Not specified";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-foreground mb-1">Review and publish</h2>
        <p className="text-sm text-muted-foreground">
          Double-check everything looks right. Once published, we will start matching candidates immediately.
        </p>
      </div>

      <div className="rounded-lg border border-border divide-y divide-border">
        <div className="p-4">
          <ReviewRow label="Role Title" value={formData.title} />
          {formData.department && <ReviewRow label="Department" value={formData.department} />}
        </div>

        <div className="p-4">
          <ReviewRow
            label="Description"
            value={
              <p className="text-sm text-foreground/80 leading-relaxed line-clamp-4">
                {formData.description}
              </p>
            }
          />
        </div>

        <div className="p-4">
          <ReviewRow
            label="Required Skills"
            value={
              <div className="flex flex-wrap gap-1.5">
                {formData.required_skills.map((s) => (
                  <Badge key={s.name} variant="outline" className="bg-muted text-foreground">
                    {s.name}
                    {s.min_years && <span className="text-muted-foreground/60 ml-1">{s.min_years}+ yr</span>}
                  </Badge>
                ))}
              </div>
            }
          />
          <ReviewRow
            label="Preferred Skills"
            value={
              <div className="flex flex-wrap gap-1.5">
                {formData.preferred_skills.map((s) => (
                  <Badge key={s.name} variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/20">
                    {s.name}
                  </Badge>
                ))}
                {formData.preferred_skills.length === 0 && (
                  <span className="text-muted-foreground/60">None</span>
                )}
              </div>
            }
          />
          {formData.seniority && (
            <ReviewRow label="Seniority" value={<span className="capitalize">{formData.seniority}</span>} />
          )}
        </div>

        <div className="p-4">
          <ReviewRow label="Salary Band" value={salary} />
          <ReviewRow label="Location" value={formData.location || "Not specified"} />
          <ReviewRow label="Work Arrangement" value={<span className="capitalize">{formData.remote_policy}</span>} />
        </div>
      </div>

      <div className="flex justify-end">
        <Button
          onClick={onPublish}
          disabled={publishing}
          size="lg"
          className="gap-2"
        >
          {publishing ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Publishing...
            </>
          ) : (
            <>
              <Rocket className="h-4 w-4" />
              Publish Role
            </>
          )}
        </Button>
      </div>

      <p className="text-xs text-muted-foreground/60 text-center">
        After publishing, our AI will begin matching candidates from our talent network. You will receive notifications as matches are found.
      </p>
    </div>
  );
}
