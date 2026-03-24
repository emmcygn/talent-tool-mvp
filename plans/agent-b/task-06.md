# Agent B — Task 06: Mind — Role Posting Wizard

## Mission
Build a multi-step guided role posting wizard for clients: title + department, description with rich text area, real-time requirement extraction (skills appear as editable tags as they type), salary + location + remote policy, and a review/confirm/publish step. Includes progress indicator, back/forward navigation, and draft saving.

## Context
Day 3. This is the primary client workflow in Mind — how a hiring manager posts a new role. The "AI with guardrails" is the star here: as the client types a job description, the system extracts requirements in real-time and shows them as editable tags. The client confirms what the AI found. This is a demo differentiator.

## Prerequisites
- Agent B Task 01 complete (project scaffold, types)
- Agent B Task 02 complete (Mind layout with top nav)
- Agent B Task 03 complete (shared components — skill-chips, confidence-badge)
- Agent B Task 04 complete (API client with mock layer — `roles.extractRequirements`)

## Checklist
- [ ] Create `app/mind/roles/new/page.tsx` — wizard container with step routing
- [ ] Create `components/mind/role-wizard.tsx` — main wizard state machine
- [ ] Create `components/mind/wizard-step-title.tsx` — Step 1: title + department
- [ ] Create `components/mind/wizard-step-description.tsx` — Step 2: description textarea
- [ ] Create `components/mind/wizard-step-requirements.tsx` — Step 3: real-time extraction with editable tags
- [ ] Create `components/mind/wizard-step-details.tsx` — Step 4: salary + location + remote
- [ ] Create `components/mind/wizard-step-review.tsx` — Step 5: review all + confirm + publish
- [ ] Create `components/mind/wizard-progress.tsx` — progress indicator
- [ ] Verify: full wizard flow works with mock extraction, draft saves to localStorage
- [ ] Commit: "Agent B Task 06: Mind role posting wizard"

## Implementation Details

### Wizard Page (`app/mind/roles/new/page.tsx`)

```tsx
import { RoleWizard } from "@/components/mind/role-wizard";

export default function NewRolePage() {
  return (
    <div className="mx-auto max-w-2xl py-4">
      <RoleWizard />
    </div>
  );
}
```

### Wizard Progress (`components/mind/wizard-progress.tsx`)

```tsx
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
                  !isCompleted && !isCurrent && "bg-slate-100 text-slate-400"
                )}
              >
                {isCompleted ? <Check className="h-4 w-4" /> : index + 1}
              </div>
              <span
                className={cn(
                  "text-sm font-medium hidden sm:block",
                  isCurrent ? "text-slate-900" : "text-slate-400"
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
```

### Role Wizard (`components/mind/role-wizard.tsx`)

```tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ArrowRight, Save } from "lucide-react";
import { WizardProgress } from "./wizard-progress";
import { WizardStepTitle } from "./wizard-step-title";
import { WizardStepDescription } from "./wizard-step-description";
import { WizardStepRequirements } from "./wizard-step-requirements";
import { WizardStepDetails } from "./wizard-step-details";
import { WizardStepReview } from "./wizard-step-review";
import type { RequiredSkill, SeniorityLevel, RemotePolicy, SalaryRange } from "@/contracts/canonical";

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

export function RoleWizard() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState<WizardFormData>(DEFAULT_FORM_DATA);
  const [publishing, setPublishing] = useState(false);

  // Load draft from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(DRAFT_KEY);
    if (saved) {
      try {
        setFormData(JSON.parse(saved));
      } catch {
        // Ignore corrupt drafts
      }
    }
  }, []);

  // Auto-save draft on every change
  useEffect(() => {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(formData));
  }, [formData]);

  const updateForm = useCallback((updates: Partial<WizardFormData>) => {
    setFormData((prev) => ({ ...prev, ...updates }));
  }, []);

  const canAdvance = (): boolean => {
    switch (step) {
      case 0: return formData.title.trim().length > 0;
      case 1: return formData.description.trim().length > 20;
      case 2: return formData.required_skills.length > 0;
      case 3: return true; // Details are all optional
      case 4: return true;
      default: return false;
    }
  };

  const handlePublish = async () => {
    setPublishing(true);
    try {
      // In production, this calls apiClient.roles.create(...)
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
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Post a New Role</h1>
        <p className="text-sm text-slate-500 mt-1">
          Describe the role and we will find the best candidates for you
        </p>
      </div>

      {/* Progress */}
      <WizardProgress steps={STEPS} currentStep={step} />

      {/* Step Content */}
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

      {/* Navigation */}
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
          {/* Draft indicator */}
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
```

### Step 1: Title + Department (`components/mind/wizard-step-title.tsx`)

```tsx
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
```

### Step 2: Description (`components/mind/wizard-step-description.tsx`)

```tsx
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
```

### Step 3: Requirements Extraction (`components/mind/wizard-step-requirements.tsx`)

This is the key differentiator — real-time extraction of requirements from the description text.

```tsx
"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Sparkles, X, Plus, Loader2, Pencil, Check } from "lucide-react";
import type { RequiredSkill, SeniorityLevel } from "@/contracts/canonical";
import type { WizardFormData } from "./role-wizard";
import { apiClient } from "@/lib/api-client";
import { cn } from "@/lib/utils";

interface WizardStepRequirementsProps {
  description: string;
  requiredSkills: RequiredSkill[];
  preferredSkills: RequiredSkill[];
  seniority: SeniorityLevel | null;
  onChange: (updates: Partial<WizardFormData>) => void;
}

const SENIORITY_OPTIONS: { value: SeniorityLevel; label: string }[] = [
  { value: "junior", label: "Junior" },
  { value: "mid", label: "Mid-level" },
  { value: "senior", label: "Senior" },
  { value: "lead", label: "Lead" },
  { value: "principal", label: "Principal" },
];

export function WizardStepRequirements({
  description,
  requiredSkills,
  preferredSkills,
  seniority,
  onChange,
}: WizardStepRequirementsProps) {
  const [extracting, setExtracting] = useState(false);
  const [extracted, setExtracted] = useState(false);
  const [newSkillName, setNewSkillName] = useState("");
  const [editingSkill, setEditingSkill] = useState<string | null>(null);
  const hasExtracted = useRef(false);

  // Auto-extract on mount if description exists and skills empty
  useEffect(() => {
    if (description.length > 20 && requiredSkills.length === 0 && !hasExtracted.current) {
      hasExtracted.current = true;
      extractRequirements();
    }
  }, [description]);

  const extractRequirements = async () => {
    setExtracting(true);
    try {
      const result = await apiClient.roles.extractRequirements(description);
      onChange({
        required_skills: result.required_skills,
        preferred_skills: result.preferred_skills,
        seniority: result.seniority,
      });
      setExtracted(true);
    } catch (err) {
      console.error("Extraction failed:", err);
    } finally {
      setExtracting(false);
    }
  };

  const removeSkill = (skillName: string, type: "required" | "preferred") => {
    if (type === "required") {
      onChange({ required_skills: requiredSkills.filter((s) => s.name !== skillName) });
    } else {
      onChange({ preferred_skills: preferredSkills.filter((s) => s.name !== skillName) });
    }
  };

  const addSkill = (type: "required" | "preferred") => {
    if (!newSkillName.trim()) return;
    const skill: RequiredSkill = {
      name: newSkillName.trim(),
      min_years: null,
      importance: type,
    };
    if (type === "required") {
      onChange({ required_skills: [...requiredSkills, skill] });
    } else {
      onChange({ preferred_skills: [...preferredSkills, skill] });
    }
    setNewSkillName("");
  };

  const toggleImportance = (skillName: string) => {
    const fromRequired = requiredSkills.find((s) => s.name === skillName);
    if (fromRequired) {
      onChange({
        required_skills: requiredSkills.filter((s) => s.name !== skillName),
        preferred_skills: [...preferredSkills, { ...fromRequired, importance: "preferred" }],
      });
    } else {
      const fromPreferred = preferredSkills.find((s) => s.name === skillName);
      if (fromPreferred) {
        onChange({
          preferred_skills: preferredSkills.filter((s) => s.name !== skillName),
          required_skills: [...requiredSkills, { ...fromPreferred, importance: "required" }],
        });
      }
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-slate-900 mb-1">Review extracted requirements</h2>
        <p className="text-sm text-slate-500">
          We analysed your description and extracted these requirements. Edit, add, or remove as needed.
        </p>
      </div>

      {/* Extraction Status */}
      {extracting && (
        <div className="flex items-center gap-3 rounded-lg bg-purple-50 border border-purple-100 p-4">
          <Loader2 className="h-5 w-5 animate-spin text-purple-600" />
          <div>
            <p className="text-sm font-medium text-purple-800">Extracting requirements...</p>
            <p className="text-xs text-purple-600">Reading your description and identifying key skills</p>
          </div>
        </div>
      )}

      {extracted && !extracting && (
        <div className="flex items-center gap-3 rounded-lg bg-green-50 border border-green-100 p-4">
          <Sparkles className="h-5 w-5 text-green-600" />
          <p className="text-sm text-green-800">
            Found {requiredSkills.length} required and {preferredSkills.length} preferred skills.
            Review and adjust below.
          </p>
          <Button variant="ghost" size="sm" onClick={extractRequirements} className="ml-auto text-green-700">
            Re-extract
          </Button>
        </div>
      )}

      {/* Seniority */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-700">Seniority Level</label>
        <Select
          value={seniority ?? ""}
          onValueChange={(val) => onChange({ seniority: val as SeniorityLevel })}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Select level" />
          </SelectTrigger>
          <SelectContent>
            {SENIORITY_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Required Skills */}
      <div className="space-y-3">
        <label className="text-sm font-medium text-slate-700">Required Skills</label>
        <div className="flex flex-wrap gap-2">
          {requiredSkills.map((skill) => (
            <Badge
              key={skill.name}
              variant="outline"
              className="bg-slate-100 text-slate-800 border-slate-300 gap-1 pr-1 py-1 text-sm cursor-default"
            >
              {skill.name}
              {skill.min_years && (
                <span className="text-slate-400 ml-1">{skill.min_years}+ yr</span>
              )}
              <button
                onClick={() => toggleImportance(skill.name)}
                className="ml-1 px-1 text-xs text-slate-400 hover:text-amber-600"
                title="Move to preferred"
              >
                <Pencil className="h-3 w-3" />
              </button>
              <button
                onClick={() => removeSkill(skill.name, "required")}
                className="ml-0.5 rounded-full hover:bg-slate-200 p-0.5"
              >
                <X className="h-3 w-3 text-slate-400" />
              </button>
            </Badge>
          ))}
        </div>
      </div>

      {/* Preferred Skills */}
      <div className="space-y-3">
        <label className="text-sm font-medium text-slate-700">Preferred Skills</label>
        <div className="flex flex-wrap gap-2">
          {preferredSkills.map((skill) => (
            <Badge
              key={skill.name}
              variant="outline"
              className="bg-amber-50 text-amber-800 border-amber-200 gap-1 pr-1 py-1 text-sm cursor-default"
            >
              {skill.name}
              {skill.min_years && (
                <span className="text-amber-400 ml-1">{skill.min_years}+ yr</span>
              )}
              <button
                onClick={() => toggleImportance(skill.name)}
                className="ml-1 px-1 text-xs text-amber-400 hover:text-slate-600"
                title="Move to required"
              >
                <Pencil className="h-3 w-3" />
              </button>
              <button
                onClick={() => removeSkill(skill.name, "preferred")}
                className="ml-0.5 rounded-full hover:bg-amber-100 p-0.5"
              >
                <X className="h-3 w-3 text-amber-400" />
              </button>
            </Badge>
          ))}
        </div>
      </div>

      {/* Add Skill */}
      <div className="flex items-center gap-2">
        <Input
          value={newSkillName}
          onChange={(e) => setNewSkillName(e.target.value)}
          placeholder="Add a skill..."
          className="max-w-xs"
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addSkill("required");
            }
          }}
        />
        <Button variant="outline" size="sm" onClick={() => addSkill("required")} className="gap-1">
          <Plus className="h-3.5 w-3.5" /> Required
        </Button>
        <Button variant="outline" size="sm" onClick={() => addSkill("preferred")} className="gap-1">
          <Plus className="h-3.5 w-3.5" /> Preferred
        </Button>
      </div>
    </div>
  );
}
```

### Step 4: Details (`components/mind/wizard-step-details.tsx`)

```tsx
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
        <h2 className="text-lg font-medium text-slate-900 mb-1">Role details</h2>
        <p className="text-sm text-slate-500">
          Add salary, location, and work arrangement. All fields are optional.
        </p>
      </div>

      {/* Salary Band */}
      <div className="space-y-3">
        <Label>Salary Band</Label>
        <div className="flex items-center gap-3">
          <Select value={currency} onValueChange={(val) => onChange({ currency: val })}>
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
          <span className="text-slate-400">to</span>
          <Input
            type="number"
            placeholder="Max"
            value={salaryMax ?? ""}
            onChange={(e) => onChange({ salary_max: e.target.value ? Number(e.target.value) : null })}
            className="w-32"
          />
        </div>
      </div>

      {/* Location */}
      <div className="space-y-2">
        <Label htmlFor="location">Location</Label>
        <Input
          id="location"
          value={location}
          onChange={(e) => onChange({ location: e.target.value })}
          placeholder="e.g. London, Manchester, or Remote"
        />
      </div>

      {/* Remote Policy */}
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
                  ? "border-slate-900 bg-slate-50 ring-1 ring-slate-900"
                  : "border-slate-200 hover:border-slate-300"
              }`}
            >
              <p className="text-sm font-medium text-slate-900">{opt.label}</p>
              <p className="text-xs text-slate-500 mt-0.5">{opt.description}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### Step 5: Review (`components/mind/wizard-step-review.tsx`)

```tsx
"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
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
      <span className="text-sm text-slate-500 w-36 shrink-0">{label}</span>
      <span className="text-sm text-slate-900">{value}</span>
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
        <h2 className="text-lg font-medium text-slate-900 mb-1">Review and publish</h2>
        <p className="text-sm text-slate-500">
          Double-check everything looks right. Once published, we will start matching candidates immediately.
        </p>
      </div>

      <div className="rounded-lg border border-slate-200 divide-y divide-slate-100">
        <div className="p-4">
          <ReviewRow label="Role Title" value={formData.title} />
          {formData.department && <ReviewRow label="Department" value={formData.department} />}
        </div>

        <div className="p-4">
          <ReviewRow
            label="Description"
            value={
              <p className="text-sm text-slate-700 leading-relaxed line-clamp-4">
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
                  <Badge key={s.name} variant="outline" className="bg-slate-100 text-slate-800">
                    {s.name}
                    {s.min_years && <span className="text-slate-400 ml-1">{s.min_years}+ yr</span>}
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
                  <Badge key={s.name} variant="outline" className="bg-amber-50 text-amber-800 border-amber-200">
                    {s.name}
                  </Badge>
                ))}
                {formData.preferred_skills.length === 0 && (
                  <span className="text-slate-400">None</span>
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

      {/* Publish Button */}
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

      <p className="text-xs text-slate-400 text-center">
        After publishing, our AI will begin matching candidates from our talent network. You will receive notifications as matches are found.
      </p>
    </div>
  );
}
```

## Outputs
- `app/mind/roles/new/page.tsx` — wizard page wrapper
- `components/mind/role-wizard.tsx` — wizard state machine with 5 steps
- `components/mind/wizard-progress.tsx` — step progress indicator
- `components/mind/wizard-step-title.tsx` — Step 1: title + department
- `components/mind/wizard-step-description.tsx` — Step 2: description textarea
- `components/mind/wizard-step-requirements.tsx` — Step 3: AI extraction + editable skill tags
- `components/mind/wizard-step-details.tsx` — Step 4: salary + location + remote policy
- `components/mind/wizard-step-review.tsx` — Step 5: review all + publish

## Acceptance Criteria
1. `npm run build` passes with no errors
2. Progress indicator shows 5 steps with correct active/completed/upcoming states
3. Step 1: title field is required to advance, department is optional
4. Step 2: description must be > 20 characters to advance
5. Step 3: on mount, auto-extracts requirements from description and shows them as editable tags
6. Step 3: required skills shown in dark tags, preferred in amber tags
7. Step 3: skills can be removed (X button), toggled between required/preferred, and new ones added
8. Step 3: at least one required skill needed to advance
9. Step 4: salary, location, remote policy — all optional
10. Step 4: remote policy uses card-style selector (onsite/hybrid/remote)
11. Step 5: review shows all entered data in a clean summary layout
12. Step 5: "Publish Role" button with loading state, redirects to `/mind/roles` on success
13. Draft auto-saves to localStorage on every change
14. Draft auto-loads from localStorage on page mount
15. Back/forward navigation works across all steps

## Handoff Notes
- **To Agent A:** The frontend calls `POST /api/roles/extract-requirements` with `{ description: string }` and expects `{ required_skills: RequiredSkill[], preferred_skills: RequiredSkill[], seniority: SeniorityLevel | null }` in response. This endpoint should use the LLM to extract structured requirements from the role description text.
- **To Task 07:** Roles created via this wizard will appear in the roles list and will need matches generated. The wizard stores form data in the `WizardFormData` shape and converts to `RoleCreate` on publish.
- **Decision:** Using localStorage for draft saving rather than server-side drafts — simpler for PoC. The auto-extraction triggers once when entering Step 3 (not on every keystroke) to avoid excessive API calls. Skills are editable inline — the client has full control over what the AI extracted.
