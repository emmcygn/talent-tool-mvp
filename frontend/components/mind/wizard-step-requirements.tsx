"use client";

import { useState, useEffect, useRef } from "react";
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
import { Sparkles, X, Plus, Loader2, Pencil } from "lucide-react";
import type { RequiredSkill, SeniorityLevel } from "@/contracts/canonical";
import type { WizardFormData } from "./role-wizard";
import { apiClient } from "@/lib/api-client";

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
  const [extracted, setExtracted] = useState(requiredSkills.length > 0);
  const [newSkillName, setNewSkillName] = useState("");
  const hasExtracted = useRef(requiredSkills.length > 0);

  useEffect(() => {
    if (description.length > 20 && requiredSkills.length === 0 && !hasExtracted.current) {
      hasExtracted.current = true;
      extractRequirements();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
