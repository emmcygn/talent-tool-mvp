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
    if (Math.random() > 0.7) {
      setDedupMatch(candidate);
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
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Add Candidate</h1>
        <p className="text-sm text-slate-500 mt-1">
          Upload a CV, paste profile text, or sync from an adapter
        </p>
      </div>

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
              onExtractionComplete={() => {}}
            />
          </TabsContent>
        </Tabs>
      )}

      {(state === "uploading" || state === "extracting") && (
        <ExtractionViewer
          state={state}
          onComplete={handleExtractionComplete}
        />
      )}

      {state === "review" && extractedCandidate && (
        <ExtractionViewer
          state="review"
          candidate={extractedCandidate}
          onSave={handleSave}
          onReset={handleReset}
        />
      )}

      {state === "dedup" && extractedCandidate && dedupMatch && (
        <DedupComparison
          newCandidate={extractedCandidate}
          existingCandidate={dedupMatch}
          onMerge={() => setState("review")}
          onKeepBoth={() => setState("review")}
          onCancel={handleReset}
        />
      )}

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
