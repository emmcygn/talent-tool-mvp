"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Loader2, Save, RotateCcw, Sparkles } from "lucide-react";
import { ExtractionField } from "./extraction-field";
import { SourceBadge } from "./source-badge";
import type { Candidate } from "@/contracts/canonical";
import { MOCK_CANDIDATES } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

interface ExtractionViewerProps {
  state: "uploading" | "extracting" | "review";
  candidate?: Candidate;
  onComplete?: (candidate: Candidate) => void;
  onSave?: () => void;
  onReset?: () => void;
}

const EXTRACTION_FIELDS = [
  { key: "name", label: "Name", delay: 400 },
  { key: "location", label: "Location", delay: 700 },
  { key: "seniority", label: "Seniority", delay: 1100 },
  { key: "skills", label: "Skills", delay: 1600 },
  { key: "experience", label: "Experience", delay: 2200 },
  { key: "availability", label: "Availability", delay: 2800 },
  { key: "salary", label: "Salary Expectation", delay: 3200 },
  { key: "industries", label: "Industries", delay: 3600 },
] as const;

export function ExtractionViewer({
  state,
  candidate: providedCandidate,
  onComplete,
  onSave,
  onReset,
}: ExtractionViewerProps) {
  const allFieldKeys = new Set(EXTRACTION_FIELDS.map((f) => f.key));
  const initialCandidate = providedCandidate ?? (state === "extracting" ? MOCK_CANDIDATES[0] : null);
  const [visibleFields, setVisibleFields] = useState<Set<string>>(
    state === "review" ? allFieldKeys : new Set()
  );
  const candidate = initialCandidate;

  const stableOnComplete = useCallback((c: Candidate) => {
    onComplete?.(c);
  }, [onComplete]);

  useEffect(() => {
    if (state !== "extracting") return;

    const timers: ReturnType<typeof setTimeout>[] = [];
    EXTRACTION_FIELDS.forEach((field) => {
      const timer = setTimeout(() => {
        setVisibleFields((prev) => new Set([...prev, field.key]));
      }, field.delay);
      timers.push(timer);
    });

    const completeTimer = setTimeout(() => {
      stableOnComplete(MOCK_CANDIDATES[0]);
    }, 4200);
    timers.push(completeTimer);

    return () => timers.forEach(clearTimeout);
  }, [state, stableOnComplete]);

  if (state === "uploading") {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500 mb-4" />
          <p className="text-sm font-medium text-slate-700">Uploading document...</p>
        </CardContent>
      </Card>
    );
  }

  if (!candidate) return null;

  const lowConfidenceThreshold = 0.8;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100">
            <Sparkles className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <CardTitle className="text-lg">
              {state === "extracting" ? "Extracting profile..." : "Review extracted profile"}
            </CardTitle>
            <p className="text-sm text-slate-500">
              {state === "extracting"
                ? "AI is reading the document and extracting structured data"
                : "Review and correct any fields before saving"}
            </p>
          </div>
        </div>
        {candidate.sources.length > 0 && (
          <SourceBadge source={candidate.sources[0]} />
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        <ExtractionField
          label="Name"
          value={`${candidate.first_name} ${candidate.last_name}`}
          visible={visibleFields.has("name")}
          confidence={candidate.extraction_confidence}
          editable={state === "review"}
        />

        <ExtractionField
          label="Location"
          value={candidate.location ?? "Not specified"}
          visible={visibleFields.has("location")}
          confidence={candidate.extraction_confidence}
          editable={state === "review"}
        />

        <ExtractionField
          label="Seniority"
          value={candidate.seniority ?? "Unknown"}
          visible={visibleFields.has("seniority")}
          confidence={
            candidate.extraction_flags.includes("seniority") ? 0.65 : candidate.extraction_confidence
          }
          lowConfidence={candidate.extraction_flags.includes("seniority")}
          editable={state === "review"}
        />

        {visibleFields.has("skills") && (
          <div className={cn("transition-all duration-500", visibleFields.has("skills") ? "opacity-100" : "opacity-0")}>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Skills</p>
            <div className="flex flex-wrap gap-1.5">
              {candidate.skills.map((skill) => (
                <span
                  key={skill.name}
                  className={cn(
                    "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-all",
                    skill.confidence >= lowConfidenceThreshold
                      ? "bg-slate-100 text-slate-800 border-slate-200"
                      : "bg-amber-50 text-amber-800 border-amber-200"
                  )}
                >
                  {skill.name}
                  {skill.years && <span className="ml-1 text-slate-400">{skill.years}y</span>}
                  {skill.confidence < lowConfidenceThreshold && (
                    <span className="ml-1 text-amber-500 text-[10px]">?</span>
                  )}
                </span>
              ))}
            </div>
          </div>
        )}

        {visibleFields.has("experience") && (
          <div className="transition-all duration-500">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Experience</p>
            <div className="space-y-2">
              {candidate.experience.map((exp, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <span className="font-medium text-slate-900">{exp.title}</span>
                  <span className="text-slate-400">at</span>
                  <span className="text-slate-700">{exp.company}</span>
                  {exp.duration_months && (
                    <span className="text-xs text-slate-400">
                      ({Math.round(exp.duration_months / 12)}y {exp.duration_months % 12}m)
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <ExtractionField
          label="Availability"
          value={candidate.availability?.replace("_", " ") ?? "Unknown"}
          visible={visibleFields.has("availability")}
          confidence={candidate.extraction_confidence}
          editable={state === "review"}
        />

        <ExtractionField
          label="Salary Expectation"
          value={
            candidate.salary_expectation
              ? `${candidate.salary_expectation.currency} ${candidate.salary_expectation.min_amount?.toLocaleString()} - ${candidate.salary_expectation.max_amount?.toLocaleString()}`
              : "Not specified"
          }
          visible={visibleFields.has("salary")}
          confidence={
            candidate.extraction_flags.includes("salary_expectation") ? 0.6 : candidate.extraction_confidence
          }
          lowConfidence={candidate.extraction_flags.includes("salary_expectation")}
          editable={state === "review"}
        />

        <ExtractionField
          label="Industries"
          value={candidate.industries.join(", ") || "None detected"}
          visible={visibleFields.has("industries")}
          confidence={candidate.extraction_confidence}
          editable={state === "review"}
        />

        {state === "review" && (
          <>
            <Separator />
            <div className="flex items-center justify-between">
              <Button variant="outline" onClick={onReset} className="gap-2">
                <RotateCcw className="h-4 w-4" />
                Start Over
              </Button>
              <Button onClick={onSave} className="gap-2">
                <Save className="h-4 w-4" />
                Save Candidate
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
