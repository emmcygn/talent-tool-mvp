"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { X, ChevronRight, ChevronLeft, Play } from "lucide-react";

interface DemoStep {
  title: string;
  description: string;
  persona: "talent_partner" | "client" | "admin";
  href: string;
}

const DEMO_STEPS: DemoStep[] = [
  {
    title: "Talent Partner Dashboard",
    description: "The command centre for talent partners. See pipeline metrics, pending handoffs, recent activity, and quick actions.",
    persona: "talent_partner",
    href: "/mothership/dashboard",
  },
  {
    title: "AI-Powered Matching",
    description: "Select a role and see AI-ranked candidates with scoring breakdowns, skill overlap analysis, and confidence levels.",
    persona: "talent_partner",
    href: "/mothership/matching",
  },
  {
    title: "Collections",
    description: "Organize candidates into themed groups. Share with partners or keep private. Track availability and match quality.",
    persona: "talent_partner",
    href: "/mothership/collections",
  },
  {
    title: "Handoff Inbox",
    description: "Receive candidate referrals from other talent partners. Accept or decline with notes. Full attribution tracking.",
    persona: "talent_partner",
    href: "/mothership/handoffs",
  },
  {
    title: "Copilot",
    description: "Natural language queries across the entire platform. Ask about candidates, matches, or analytics in plain English.",
    persona: "talent_partner",
    href: "/mothership/copilot",
  },
  {
    title: "Client Dashboard",
    description: "A clean, guided experience for hiring managers. See active roles, matched candidates, and quote status.",
    persona: "client",
    href: "/mind/dashboard",
  },
  {
    title: "Candidate Browse",
    description: "Review AI-matched candidates with anonymized profiles, skill chips, and one-click introduction requests.",
    persona: "client",
    href: "/mind/candidates",
  },
  {
    title: "Hiring Pipeline",
    description: "Kanban board tracking candidates from Matched through Placed. Drag and drop between stages.",
    persona: "client",
    href: "/mind/pipeline",
  },
  {
    title: "Platform Analytics",
    description: "Admin view with pipeline funnel, trending skills, partner performance, and client engagement metrics.",
    persona: "admin",
    href: "/mothership/admin/analytics",
  },
  {
    title: "Data Quality",
    description: "Review auto-detected duplicates with side-by-side comparison. Merge, keep separate, or bulk approve.",
    persona: "admin",
    href: "/mothership/admin/quality",
  },
];

const PERSONA_LABELS: Record<string, { label: string; color: string }> = {
  talent_partner: { label: "Talent Partner", color: "bg-blue-100 text-blue-700" },
  client: { label: "Client", color: "bg-green-100 text-green-700" },
  admin: { label: "Admin", color: "bg-purple-100 text-purple-700" },
};

interface DemoOverlayProps {
  onClose: () => void;
}

export function DemoOverlay({ onClose }: DemoOverlayProps) {
  const [currentStep, setCurrentStep] = useState(0);

  const step = DEMO_STEPS[currentStep];
  const persona = PERSONA_LABELS[step.persona];

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
      <Card className="w-full max-w-lg shadow-2xl">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${persona.color}`}>
                {persona.label}
              </span>
              <span className="text-xs text-muted-foreground">
                {currentStep + 1} of {DEMO_STEPS.length}
              </span>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose} className="h-7 w-7">
              <X className="h-4 w-4" />
            </Button>
          </div>

          <h2 className="text-xl font-semibold mb-2">{step.title}</h2>
          <p className="text-sm text-muted-foreground mb-6">{step.description}</p>

          <div className="w-full bg-slate-100 rounded-full h-1 mb-4">
            <div
              className="bg-primary h-1 rounded-full transition-all duration-300"
              style={{ width: `${((currentStep + 1) / DEMO_STEPS.length) * 100}%` }}
            />
          </div>

          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
              disabled={currentStep === 0}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </Button>
            <a href={step.href}>
              <Button variant="ghost" size="sm">
                <Play className="h-4 w-4 mr-1" />
                Visit Page
              </Button>
            </a>
            {currentStep < DEMO_STEPS.length - 1 ? (
              <Button
                size="sm"
                onClick={() => setCurrentStep(currentStep + 1)}
              >
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            ) : (
              <Button size="sm" onClick={onClose}>
                Finish Tour
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
