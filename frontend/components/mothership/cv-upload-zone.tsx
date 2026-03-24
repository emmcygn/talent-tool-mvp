"use client";

import { useState, useCallback, useRef } from "react";
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
  const inputRef = useRef<HTMLInputElement>(null);

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
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors cursor-pointer",
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
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

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
