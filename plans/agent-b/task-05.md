# Agent B — Task 05: Mothership — Candidate Ingestion

## Mission
Build the candidate ingestion page for talent partners: drag-and-drop CV upload (PDF/DOCX), paste text alternative, adapter sync buttons, real-time extraction animation, low-confidence field highlighting, and dedup comparison modal.

## Context
Day 2. This is a core talent partner workflow — the first time a candidate enters the system. The experience must feel modern and intelligent: upload a CV, watch the AI extract structured data in real-time, review and correct, then save. The extraction animation is a key "wow" moment for the demo.

## Prerequisites
- Agent B Task 01 complete (project scaffold, types)
- Agent B Task 02 complete (Mothership layout with sidebar)
- Agent B Task 03 complete (shared components — candidate-card, skill-chips, loading-skeleton)
- Agent B Task 04 complete (API client with mock layer)

## Checklist
- [ ] Create `app/mothership/candidates/new/page.tsx` — ingestion page with upload/paste/sync tabs
- [ ] Create `components/mothership/cv-upload-zone.tsx` — drag-and-drop file upload component
- [ ] Create `components/mothership/text-paste-input.tsx` — paste profile/CV text alternative
- [ ] Create `components/mothership/adapter-sync-buttons.tsx` — Bullhorn/HubSpot/LinkedIn sync triggers
- [ ] Create `components/mothership/extraction-viewer.tsx` — real-time extraction animation
- [ ] Create `components/mothership/extraction-field.tsx` — single field with confidence indicator + edit
- [ ] Create `components/mothership/dedup-comparison.tsx` — side-by-side comparison modal
- [ ] Create `components/mothership/source-badge.tsx` — source origin badge
- [ ] Verify: full upload flow works with mock data, extraction animation plays, dedup modal opens
- [ ] Commit: "Agent B Task 05: Mothership candidate ingestion"

## Implementation Details

### Ingestion Page (`app/mothership/candidates/new/page.tsx`)

```tsx
"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Upload, Type, RefreshCw } from "lucide-react";
import { CVUploadZone } from "@/components/mothership/cv-upload-zone";
import { TextPasteInput } from "@/components/mothership/text-paste-input";
import { AdapterSyncButtons } from "@/components/mothership/adapter-sync-buttons";
import { ExtractionViewer } from "@/components/mothership/extraction-viewer";
import { DedupComparison } from "@/components/mothership/dedup-comparison";
import type { Candidate } from "@/contracts/canonical";

type IngestionState = "idle" | "uploading" | "extracting" | "review" | "dedup" | "saved";

export default function CandidateIngestionPage() {
  const [state, setState] = useState<IngestionState>("idle");
  const [extractedCandidate, setExtractedCandidate] = useState<Candidate | null>(null);
  const [dedupMatch, setDedupMatch] = useState<Candidate | null>(null);

  const handleExtractionComplete = (candidate: Candidate) => {
    setExtractedCandidate(candidate);
    // Simulate dedup check — in production this comes from the API
    // For demo, 30% chance of finding a duplicate
    if (Math.random() > 0.7) {
      setDedupMatch(candidate); // Would be a different candidate in real usage
      setState("dedup");
    } else {
      setState("review");
    }
  };

  const handleSave = () => {
    setState("saved");
  };

  const handleReset = () => {
    setState("idle");
    setExtractedCandidate(null);
    setDedupMatch(null);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Add Candidate</h1>
        <p className="text-sm text-slate-500 mt-1">
          Upload a CV, paste profile text, or sync from an adapter
        </p>
      </div>

      {/* Input Phase */}
      {state === "idle" && (
        <Tabs defaultValue="upload" className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-3">
            <TabsTrigger value="upload" className="gap-2">
              <Upload className="h-4 w-4" /> Upload CV
            </TabsTrigger>
            <TabsTrigger value="paste" className="gap-2">
              <Type className="h-4 w-4" /> Paste Text
            </TabsTrigger>
            <TabsTrigger value="sync" className="gap-2">
              <RefreshCw className="h-4 w-4" /> Adapter Sync
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="mt-6">
            <CVUploadZone
              onUploadStart={() => setState("uploading")}
              onExtractionStart={() => setState("extracting")}
              onExtractionComplete={handleExtractionComplete}
            />
          </TabsContent>

          <TabsContent value="paste" className="mt-6">
            <TextPasteInput
              onExtractionStart={() => setState("extracting")}
              onExtractionComplete={handleExtractionComplete}
            />
          </TabsContent>

          <TabsContent value="sync" className="mt-6">
            <AdapterSyncButtons
              onSyncStart={() => setState("uploading")}
              onExtractionComplete={handleExtractionComplete}
            />
          </TabsContent>
        </Tabs>
      )}

      {/* Extraction Animation Phase */}
      {(state === "uploading" || state === "extracting") && (
        <ExtractionViewer
          state={state}
          onComplete={handleExtractionComplete}
        />
      )}

      {/* Review Phase (reuses ExtractionViewer in review mode) */}
      {state === "review" && extractedCandidate && (
        <ExtractionViewer
          state="review"
          candidate={extractedCandidate}
          onSave={handleSave}
          onReset={handleReset}
        />
      )}

      {/* Dedup Comparison Phase */}
      {state === "dedup" && extractedCandidate && dedupMatch && (
        <DedupComparison
          newCandidate={extractedCandidate}
          existingCandidate={dedupMatch}
          onMerge={() => setState("review")}
          onKeepBoth={() => setState("review")}
          onCancel={handleReset}
        />
      )}

      {/* Saved Confirmation */}
      {state === "saved" && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-8 text-center">
          <h2 className="text-lg font-semibold text-green-800">Candidate saved successfully</h2>
          <p className="text-sm text-green-600 mt-1">The profile has been added to the system.</p>
          <button
            onClick={handleReset}
            className="mt-4 text-sm font-medium text-green-700 underline hover:no-underline"
          >
            Add another candidate
          </button>
        </div>
      )}
    </div>
  );
}
```

### CV Upload Zone (`components/mothership/cv-upload-zone.tsx`)

```tsx
"use client";

import { useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, FileText, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { apiClient } from "@/lib/api-client";
import type { Candidate } from "@/contracts/canonical";

interface CVUploadZoneProps {
  onUploadStart: () => void;
  onExtractionStart: () => void;
  onExtractionComplete: (candidate: Candidate) => void;
}

export function CVUploadZone({
  onUploadStart,
  onExtractionStart,
  onExtractionComplete,
}: CVUploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.type === "application/pdf" || file.name.endsWith(".docx"))) {
      setSelectedFile(file);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    onUploadStart();
    try {
      // Simulate brief upload, then extraction
      await new Promise((r) => setTimeout(r, 500));
      onExtractionStart();
      const candidate = await apiClient.candidates.uploadCV(selectedFile);
      onExtractionComplete(candidate);
    } catch (err) {
      console.error("Upload failed:", err);
    }
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors",
          isDragOver
            ? "border-blue-400 bg-blue-50"
            : "border-slate-200 bg-slate-50 hover:border-slate-300"
        )}
      >
        <Upload className="h-10 w-10 text-slate-400 mb-4" />
        <p className="text-sm font-medium text-slate-700 mb-1">
          Drop a CV here, or click to browse
        </p>
        <p className="text-xs text-slate-400">PDF or DOCX, up to 10MB</p>
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileSelect}
          className="hidden"
          id="cv-upload"
        />
        <label htmlFor="cv-upload">
          <Button variant="outline" size="sm" className="mt-4" asChild>
            <span>Choose file</span>
          </Button>
        </label>
      </div>

      {/* Selected File Preview */}
      {selectedFile && (
        <Card>
          <CardContent className="flex items-center gap-3 py-3">
            <FileText className="h-8 w-8 text-blue-500" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 truncate">
                {selectedFile.name}
              </p>
              <p className="text-xs text-slate-400">
                {(selectedFile.size / 1024).toFixed(0)} KB
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setSelectedFile(null)}
            >
              <X className="h-4 w-4" />
            </Button>
            <Button onClick={handleUpload}>
              Extract Profile
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

### Text Paste Input (`components/mothership/text-paste-input.tsx`)

```tsx
"use client";

import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Sparkles } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import type { Candidate } from "@/contracts/canonical";

interface TextPasteInputProps {
  onExtractionStart: () => void;
  onExtractionComplete: (candidate: Candidate) => void;
}

export function TextPasteInput({ onExtractionStart, onExtractionComplete }: TextPasteInputProps) {
  const [text, setText] = useState("");

  const handleExtract = async () => {
    if (!text.trim()) return;
    onExtractionStart();
    try {
      const candidate = await apiClient.candidates.extractFromText(text);
      onExtractionComplete(candidate);
    } catch (err) {
      console.error("Extraction failed:", err);
    }
  };

  return (
    <div className="space-y-4">
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste a candidate's CV text, LinkedIn profile summary, or any profile information here..."
        className="min-h-[200px] resize-y"
      />
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-400">
          {text.length > 0 ? `${text.length} characters` : "Paste any unstructured candidate text"}
        </p>
        <Button onClick={handleExtract} disabled={!text.trim()} className="gap-2">
          <Sparkles className="h-4 w-4" />
          Extract Profile
        </Button>
      </div>
    </div>
  );
}
```

### Adapter Sync Buttons (`components/mothership/adapter-sync-buttons.tsx`)

```tsx
"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, Loader2, CheckCircle2 } from "lucide-react";
import type { Candidate } from "@/contracts/canonical";

interface AdapterSyncButtonsProps {
  onSyncStart: () => void;
  onExtractionComplete: (candidate: Candidate) => void;
}

const ADAPTERS = [
  {
    id: "bullhorn",
    name: "Bullhorn",
    description: "ATS — sync candidates from your Bullhorn instance",
    lastSync: "2h ago",
    status: "connected" as const,
  },
  {
    id: "hubspot",
    name: "HubSpot",
    description: "CRM — import contacts tagged as candidates",
    lastSync: "4h ago",
    status: "connected" as const,
  },
  {
    id: "linkedin",
    name: "LinkedIn Recruiter",
    description: "Import profiles from LinkedIn Recruiter exports",
    lastSync: "1d ago",
    status: "degraded" as const,
  },
];

export function AdapterSyncButtons({ onSyncStart, onExtractionComplete }: AdapterSyncButtonsProps) {
  const [syncing, setSyncing] = useState<string | null>(null);

  const handleSync = async (adapterId: string) => {
    setSyncing(adapterId);
    onSyncStart();
    // Simulate sync — in production, this triggers a backend adapter sync
    await new Promise((r) => setTimeout(r, 2000));
    setSyncing(null);
  };

  return (
    <div className="grid gap-4">
      {ADAPTERS.map((adapter) => (
        <Card key={adapter.id}>
          <CardHeader className="flex flex-row items-center gap-4 pb-2">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <CardTitle className="text-base">{adapter.name}</CardTitle>
                <Badge
                  variant="outline"
                  className={
                    adapter.status === "connected"
                      ? "bg-green-50 text-green-700 border-green-200"
                      : "bg-amber-50 text-amber-700 border-amber-200"
                  }
                >
                  {adapter.status}
                </Badge>
              </div>
              <CardDescription className="mt-1">
                {adapter.description}
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="flex items-center justify-between pt-0">
            <span className="text-xs text-slate-400">
              Last synced: {adapter.lastSync}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={syncing !== null}
              onClick={() => handleSync(adapter.id)}
              className="gap-2"
            >
              {syncing === adapter.id ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              Sync Now
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
```

### Extraction Viewer (`components/mothership/extraction-viewer.tsx`)

This is the key "wow" component — it shows structured fields appearing progressively with a typing effect as if the AI is extracting them in real-time.

```tsx
"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Loader2, Save, RotateCcw, Sparkles } from "lucide-react";
import { ExtractionField } from "./extraction-field";
import { SourceBadge } from "./source-badge";
import { SkillChips } from "@/components/shared/skill-chips";
import type { Candidate, ExtractedSkill } from "@/contracts/canonical";
import { apiClient } from "@/lib/api-client";
import { MOCK_CANDIDATES } from "@/lib/mock-data";
import { cn } from "@/lib/utils";

interface ExtractionViewerProps {
  state: "uploading" | "extracting" | "review";
  candidate?: Candidate;
  onComplete?: (candidate: Candidate) => void;
  onSave?: () => void;
  onReset?: () => void;
}

// Fields to progressively reveal during extraction animation
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
  const [visibleFields, setVisibleFields] = useState<Set<string>>(new Set());
  const [candidate, setCandidate] = useState<Candidate | null>(providedCandidate ?? null);
  const [editingField, setEditingField] = useState<string | null>(null);

  // Progressive reveal animation during extraction
  useEffect(() => {
    if (state !== "extracting") {
      if (state === "review") {
        setVisibleFields(new Set(EXTRACTION_FIELDS.map((f) => f.key)));
      }
      return;
    }

    // Use first mock candidate for demo extraction
    const mockCandidate = MOCK_CANDIDATES[0];
    setCandidate(mockCandidate);

    const timers: NodeJS.Timeout[] = [];
    EXTRACTION_FIELDS.forEach((field) => {
      const timer = setTimeout(() => {
        setVisibleFields((prev) => new Set([...prev, field.key]));
      }, field.delay);
      timers.push(timer);
    });

    // Complete extraction after all fields revealed
    const completeTimer = setTimeout(() => {
      onComplete?.(mockCandidate);
    }, 4200);
    timers.push(completeTimer);

    return () => timers.forEach(clearTimeout);
  }, [state, onComplete]);

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
        {/* Name */}
        <ExtractionField
          label="Name"
          value={`${candidate.first_name} ${candidate.last_name}`}
          visible={visibleFields.has("name")}
          confidence={candidate.extraction_confidence}
          onEdit={() => setEditingField("name")}
          editable={state === "review"}
        />

        {/* Location */}
        <ExtractionField
          label="Location"
          value={candidate.location ?? "Not specified"}
          visible={visibleFields.has("location")}
          confidence={candidate.extraction_confidence}
          onEdit={() => setEditingField("location")}
          editable={state === "review"}
        />

        {/* Seniority */}
        <ExtractionField
          label="Seniority"
          value={candidate.seniority ?? "Unknown"}
          visible={visibleFields.has("seniority")}
          confidence={
            candidate.extraction_flags.includes("seniority") ? 0.65 : candidate.extraction_confidence
          }
          lowConfidence={candidate.extraction_flags.includes("seniority")}
          onEdit={() => setEditingField("seniority")}
          editable={state === "review"}
        />

        {/* Skills */}
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

        {/* Experience */}
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

        {/* Availability */}
        <ExtractionField
          label="Availability"
          value={candidate.availability?.replace("_", " ") ?? "Unknown"}
          visible={visibleFields.has("availability")}
          confidence={candidate.extraction_confidence}
          onEdit={() => setEditingField("availability")}
          editable={state === "review"}
        />

        {/* Salary */}
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
          onEdit={() => setEditingField("salary")}
          editable={state === "review"}
        />

        {/* Industries */}
        <ExtractionField
          label="Industries"
          value={candidate.industries.join(", ") || "None detected"}
          visible={visibleFields.has("industries")}
          confidence={candidate.extraction_confidence}
          onEdit={() => setEditingField("industries")}
          editable={state === "review"}
        />

        {/* Actions (review mode only) */}
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
```

### Extraction Field (`components/mothership/extraction-field.tsx`)

```tsx
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Pencil, Check, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ExtractionFieldProps {
  label: string;
  value: string;
  visible: boolean;
  confidence: number | null;
  lowConfidence?: boolean;
  editable?: boolean;
  onEdit?: () => void;
}

export function ExtractionField({
  label,
  value,
  visible,
  confidence,
  lowConfidence = false,
  editable = false,
  onEdit,
}: ExtractionFieldProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);

  if (!visible) return null;

  return (
    <div
      className={cn(
        "flex items-center gap-4 py-2 transition-all duration-500 animate-in fade-in slide-in-from-left-2",
        lowConfidence && "bg-amber-50 -mx-4 px-4 rounded-md border border-amber-100"
      )}
    >
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wider w-32 shrink-0">
        {label}
      </p>

      {isEditing ? (
        <div className="flex items-center gap-2 flex-1">
          <Input
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            className="h-8 text-sm"
          />
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setIsEditing(false)}
          >
            <Check className="h-4 w-4 text-green-600" />
          </Button>
        </div>
      ) : (
        <div className="flex items-center gap-2 flex-1">
          <span className={cn("text-sm", lowConfidence ? "text-amber-800" : "text-slate-900")}>
            {value}
          </span>
          {lowConfidence && (
            <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0" />
          )}
          {editable && (
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 opacity-0 group-hover:opacity-100 hover:opacity-100"
              onClick={() => {
                setIsEditing(true);
                onEdit?.();
              }}
            >
              <Pencil className="h-3 w-3 text-slate-400" />
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
```

### Source Badge (`components/mothership/source-badge.tsx`)

```tsx
import { Badge } from "@/components/ui/badge";
import type { CandidateSource } from "@/contracts/canonical";
import { formatRelativeTime } from "@/lib/utils";

interface SourceBadgeProps {
  source: CandidateSource;
}

const ADAPTER_COLORS: Record<string, string> = {
  bullhorn: "bg-orange-50 text-orange-700 border-orange-200",
  hubspot: "bg-rose-50 text-rose-700 border-rose-200",
  linkedin: "bg-blue-50 text-blue-700 border-blue-200",
  manual: "bg-slate-50 text-slate-700 border-slate-200",
};

const ADAPTER_LABELS: Record<string, string> = {
  bullhorn: "Bullhorn",
  hubspot: "HubSpot",
  linkedin: "LinkedIn",
  manual: "Manual Upload",
};

export function SourceBadge({ source }: SourceBadgeProps) {
  const colorClass = ADAPTER_COLORS[source.adapter_name] ?? ADAPTER_COLORS.manual;
  const label = ADAPTER_LABELS[source.adapter_name] ?? source.adapter_name;

  return (
    <Badge variant="outline" className={`text-xs ${colorClass}`}>
      {label} &middot; {formatRelativeTime(source.ingested_at)}
    </Badge>
  );
}
```

### Dedup Comparison Modal (`components/mothership/dedup-comparison.tsx`)

```tsx
"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { GitMerge, Copy, X } from "lucide-react";
import type { Candidate } from "@/contracts/canonical";
import { SourceBadge } from "./source-badge";
import { cn } from "@/lib/utils";

interface DedupComparisonProps {
  newCandidate: Candidate;
  existingCandidate: Candidate;
  onMerge: () => void;
  onKeepBoth: () => void;
  onCancel: () => void;
}

interface FieldRowProps {
  label: string;
  newValue: string | null;
  existingValue: string | null;
}

function FieldRow({ label, newValue, existingValue }: FieldRowProps) {
  const match = newValue === existingValue;
  return (
    <div className="grid grid-cols-[140px_1fr_1fr] gap-4 py-2 items-center">
      <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</span>
      <span className={cn("text-sm", match ? "text-slate-600" : "text-blue-700 font-medium")}>
        {newValue ?? "—"}
      </span>
      <span className={cn("text-sm", match ? "text-slate-600" : "text-purple-700 font-medium")}>
        {existingValue ?? "—"}
      </span>
    </div>
  );
}

export function DedupComparison({
  newCandidate,
  existingCandidate,
  onMerge,
  onKeepBoth,
  onCancel,
}: DedupComparisonProps) {
  return (
    <Dialog open onOpenChange={(open) => !open && onCancel()}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitMerge className="h-5 w-5 text-amber-500" />
            Potential Duplicate Detected
          </DialogTitle>
          <DialogDescription>
            This candidate may already exist in the system. Compare the records below and decide how to proceed.
          </DialogDescription>
        </DialogHeader>

        {/* Column Headers */}
        <div className="grid grid-cols-[140px_1fr_1fr] gap-4 py-2">
          <span />
          <div className="space-y-1">
            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">New Record</Badge>
            {newCandidate.sources.length > 0 && (
              <div><SourceBadge source={newCandidate.sources[0]} /></div>
            )}
          </div>
          <div className="space-y-1">
            <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">Existing Record</Badge>
            {existingCandidate.sources.length > 0 && (
              <div><SourceBadge source={existingCandidate.sources[0]} /></div>
            )}
          </div>
        </div>

        <Separator />

        {/* Field Comparisons */}
        <div className="space-y-1">
          <FieldRow
            label="Name"
            newValue={`${newCandidate.first_name} ${newCandidate.last_name}`}
            existingValue={`${existingCandidate.first_name} ${existingCandidate.last_name}`}
          />
          <FieldRow label="Email" newValue={newCandidate.email} existingValue={existingCandidate.email} />
          <FieldRow label="Phone" newValue={newCandidate.phone} existingValue={existingCandidate.phone} />
          <FieldRow label="Location" newValue={newCandidate.location} existingValue={existingCandidate.location} />
          <FieldRow
            label="Seniority"
            newValue={newCandidate.seniority}
            existingValue={existingCandidate.seniority}
          />
          <FieldRow
            label="Skills"
            newValue={newCandidate.skills.map((s) => s.name).join(", ")}
            existingValue={existingCandidate.skills.map((s) => s.name).join(", ")}
          />
          <FieldRow
            label="Availability"
            newValue={newCandidate.availability?.replace("_", " ") ?? null}
            existingValue={existingCandidate.availability?.replace("_", " ") ?? null}
          />
        </div>

        <Separator />

        {/* Actions */}
        <div className="flex items-center justify-end gap-3">
          <Button variant="outline" onClick={onCancel} className="gap-2">
            <X className="h-4 w-4" />
            Cancel
          </Button>
          <Button variant="outline" onClick={onKeepBoth} className="gap-2">
            <Copy className="h-4 w-4" />
            Keep Both
          </Button>
          <Button onClick={onMerge} className="gap-2">
            <GitMerge className="h-4 w-4" />
            Merge Records
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

## Outputs
- `app/mothership/candidates/new/page.tsx` — candidate ingestion page with state machine
- `components/mothership/cv-upload-zone.tsx` — drag-and-drop CV upload
- `components/mothership/text-paste-input.tsx` — paste text extraction
- `components/mothership/adapter-sync-buttons.tsx` — Bullhorn/HubSpot/LinkedIn sync buttons
- `components/mothership/extraction-viewer.tsx` — real-time extraction animation + review mode
- `components/mothership/extraction-field.tsx` — single field with confidence + edit
- `components/mothership/dedup-comparison.tsx` — side-by-side dedup comparison modal
- `components/mothership/source-badge.tsx` — adapter source badge

## Acceptance Criteria
1. `npm run build` passes with no errors
2. Upload tab: drag-and-drop zone accepts PDF/DOCX files, shows file preview, triggers extraction
3. Paste tab: text area accepts pasted text, triggers extraction with "Extract Profile" button
4. Adapter tab: three adapter cards with status badges and "Sync Now" buttons
5. Extraction animation: fields appear progressively over ~4 seconds with fade-in animation
6. Low-confidence fields are highlighted in amber with a warning icon
7. In review mode, fields have edit buttons that switch to inline editing
8. Dedup comparison modal shows side-by-side field comparison with color-coded differences
9. Dedup modal has three actions: Cancel, Keep Both, Merge Records
10. Source badge shows adapter name with correct color and relative time

## Handoff Notes
- **To Agent A:** The upload endpoint is `POST /api/candidates/upload` (multipart form data with `file` field). The text extraction endpoint is `POST /api/candidates/extract` (JSON with `text` field). Both should return a full `Candidate` object with extraction results. The frontend expects `extraction_flags` to contain field names that have low confidence (e.g., `["seniority", "salary_expectation"]`).
- **To Task 08:** The `SourceBadge` and `ExtractionField` components are reusable. Import from `@/components/mothership/`.
- **Decision:** The extraction animation uses fixed timing (not real server events) for the PoC. In production, this would use server-sent events or WebSocket to stream extraction progress. The dedup check is simulated client-side with a random probability — in production, the API response from upload/extract would include a `dedup_candidates` field.
