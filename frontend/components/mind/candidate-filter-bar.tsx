"use client";

import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Search, X } from "lucide-react";
import type { SeniorityLevel, AvailabilityStatus } from "@/contracts/canonical";
import { useState } from "react";

export interface FilterState {
  skills: string[];
  seniority: SeniorityLevel | null;
  availability: AvailabilityStatus | null;
  location: string;
}

interface CandidateFilterBarProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  availableSkills: string[];
}

export function CandidateFilterBar({ filters, onChange }: CandidateFilterBarProps) {
  const [skillInput, setSkillInput] = useState("");

  const addSkillFilter = (skill: string) => {
    if (!skill.trim() || filters.skills.includes(skill)) return;
    onChange({ ...filters, skills: [...filters.skills, skill.trim()] });
    setSkillInput("");
  };

  const removeSkillFilter = (skill: string) => {
    onChange({ ...filters, skills: filters.skills.filter((s) => s !== skill) });
  };

  const clearAll = () => {
    onChange({ skills: [], seniority: null, availability: null, location: "" });
  };

  const hasFilters = filters.skills.length > 0 || filters.seniority || filters.availability || filters.location;

  return (
    <div className="space-y-3 flex-1">
      <div className="flex items-center gap-3 flex-wrap">
        {/* Skill Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            value={skillInput}
            onChange={(e) => setSkillInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addSkillFilter(skillInput);
              }
            }}
            placeholder="Filter by skill..."
            className="pl-9 w-48"
          />
        </div>

        {/* Seniority */}
        <Select
          value={filters.seniority ?? "all"}
          onValueChange={(val) =>
            val && onChange({ ...filters, seniority: val === "all" ? null : (val as SeniorityLevel) })
          }
        >
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Seniority" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Any seniority</SelectItem>
            <SelectItem value="junior">Junior</SelectItem>
            <SelectItem value="mid">Mid-level</SelectItem>
            <SelectItem value="senior">Senior</SelectItem>
            <SelectItem value="lead">Lead</SelectItem>
            <SelectItem value="principal">Principal</SelectItem>
          </SelectContent>
        </Select>

        {/* Availability */}
        <Select
          value={filters.availability ?? "all"}
          onValueChange={(val) =>
            val && onChange({ ...filters, availability: val === "all" ? null : (val as AvailabilityStatus) })
          }
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Availability" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Any availability</SelectItem>
            <SelectItem value="immediate">Available now</SelectItem>
            <SelectItem value="1_month">1 month</SelectItem>
            <SelectItem value="3_months">3 months</SelectItem>
          </SelectContent>
        </Select>

        {/* Location */}
        <Input
          value={filters.location}
          onChange={(e) => onChange({ ...filters, location: e.target.value })}
          placeholder="Location..."
          className="w-36"
        />

        {/* Clear */}
        {hasFilters && (
          <Button variant="ghost" size="sm" onClick={clearAll} className="text-slate-400 gap-1">
            <X className="h-3.5 w-3.5" />
            Clear
          </Button>
        )}
      </div>

      {/* Active Skill Filters */}
      {filters.skills.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {filters.skills.map((skill) => (
            <Badge
              key={skill}
              variant="secondary"
              className="gap-1 pr-1"
            >
              {skill}
              <button
                onClick={() => removeSkillFilter(skill)}
                className="rounded-full hover:bg-slate-300 p-0.5"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
