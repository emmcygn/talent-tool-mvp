"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ArrowRight, Save } from "lucide-react";
import { WizardProgress } from "./wizard-progress";
import { WizardStepTitle } from "./wizard-step-title";
import { WizardStepDescription } from "./wizard-step-description";
import { WizardStepRequirements } from "./wizard-step-requirements";
import { WizardStepDetails } from "./wizard-step-details";
import { WizardStepReview } from "./wizard-step-review";
import type { RequiredSkill, SeniorityLevel, RemotePolicy } from "@/contracts/canonical";

const STEPS = ["Basics", "Description", "Requirements", "Details", "Review"];
const DRAFT_KEY = "role-wizard-draft";

export interface WizardFormData {
  title: string;
  department: string;
  description: string;
  required_skills: RequiredSkill[];
  preferred_skills: RequiredSkill[];
  seniority: SeniorityLevel | null;
  salary_min: number | null;
  salary_max: number | null;
  currency: string;
  location: string;
  remote_policy: RemotePolicy;
}

const DEFAULT_FORM_DATA: WizardFormData = {
  title: "",
  department: "",
  description: "",
  required_skills: [],
  preferred_skills: [],
  seniority: null,
  salary_min: null,
  salary_max: null,
  currency: "GBP",
  location: "",
  remote_policy: "hybrid",
};

function loadDraft(): WizardFormData {
  if (typeof window === "undefined") return DEFAULT_FORM_DATA;
  try {
    const saved = localStorage.getItem(DRAFT_KEY);
    if (saved) return JSON.parse(saved);
  } catch {
    // Ignore corrupt drafts
  }
  return DEFAULT_FORM_DATA;
}

function saveDraft(data: WizardFormData) {
  try {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(data));
  } catch {
    // Ignore storage errors
  }
}

export function RoleWizard() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState<WizardFormData>(loadDraft);
  const [publishing, setPublishing] = useState(false);

  const updateForm = useCallback((updates: Partial<WizardFormData>) => {
    setFormData((prev) => {
      const next = { ...prev, ...updates };
      saveDraft(next);
      return next;
    });
  }, []);

  const canAdvance = (): boolean => {
    switch (step) {
      case 0: return formData.title.trim().length > 0;
      case 1: return formData.description.trim().length > 20;
      case 2: return formData.required_skills.length > 0;
      case 3: return true;
      case 4: return true;
      default: return false;
    }
  };

  const handlePublish = async () => {
    setPublishing(true);
    try {
      await new Promise((r) => setTimeout(r, 1000));
      localStorage.removeItem(DRAFT_KEY);
      router.push("/mind/roles");
    } catch (err) {
      console.error("Publish failed:", err);
      setPublishing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Post a New Role</h1>
        <p className="text-sm text-slate-500 mt-1">
          Describe the role and we will find the best candidates for you
        </p>
      </div>

      <WizardProgress steps={STEPS} currentStep={step} />

      <div className="min-h-[300px]">
        {step === 0 && (
          <WizardStepTitle
            title={formData.title}
            department={formData.department}
            onChange={updateForm}
          />
        )}
        {step === 1 && (
          <WizardStepDescription
            description={formData.description}
            onChange={updateForm}
          />
        )}
        {step === 2 && (
          <WizardStepRequirements
            description={formData.description}
            requiredSkills={formData.required_skills}
            preferredSkills={formData.preferred_skills}
            seniority={formData.seniority}
            onChange={updateForm}
          />
        )}
        {step === 3 && (
          <WizardStepDetails
            salaryMin={formData.salary_min}
            salaryMax={formData.salary_max}
            currency={formData.currency}
            location={formData.location}
            remotePolicy={formData.remote_policy}
            onChange={updateForm}
          />
        )}
        {step === 4 && (
          <WizardStepReview
            formData={formData}
            onPublish={handlePublish}
            publishing={publishing}
          />
        )}
      </div>

      <div className="flex items-center justify-between border-t border-slate-100 pt-4">
        <Button
          variant="ghost"
          onClick={() => setStep((s) => s - 1)}
          disabled={step === 0}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 flex items-center gap-1">
            <Save className="h-3 w-3" />
            Draft saved
          </span>

          {step < STEPS.length - 1 && (
            <Button
              onClick={() => setStep((s) => s + 1)}
              disabled={!canAdvance()}
              className="gap-2"
            >
              Next
              <ArrowRight className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
