# Agent B — Task 16: Polish — Demo Mode + Final Pass

## Mission
Add demo mode walkthrough overlay, dark mode, animations, accessibility, responsive refinements, and final visual QA across all pages. This is the final polish pass that makes the PoC feel like a real product.

## Context
Days 7-8. All features are built. This task is about making everything feel finished. The audience is non-technical recruitment partners — rough edges, janky transitions, or confusing empty states will undermine the demo. Agent A is completing seed data and integration testing (Task 16) in parallel.

## Prerequisites
- All B-01 through B-15 complete
- Agent A seed data loaded (A-16) for realistic demo content
- All pages rendering with real or mock data

## Checklist
- [ ] Create `frontend/components/shared/demo-overlay.tsx` — guided tour component
- [ ] Create `frontend/app/demo/page.tsx` — demo mode entry point
- [ ] Add demo tour steps for each persona (talent partner, client, admin)
- [ ] Add dark mode support (CSS variables + Tailwind dark: classes)
- [ ] Add theme toggle to layouts
- [ ] Add page transition animations (subtle fade/slide)
- [ ] Add card hover effects across all card components
- [ ] Add loading skeleton states to any pages that don't have them
- [ ] Create `frontend/components/shared/notification-toast.tsx` — toast notification system
- [ ] Wire toast notifications to key actions (shortlist, handoff sent, quote requested)
- [ ] Add keyboard shortcuts: `/` for search, `?` for help, `Esc` to close modals
- [ ] Responsive pass: test at 1024px, 1280px, 1440px breakpoints
- [ ] Accessibility: focus rings, aria-labels on icon buttons, skip-to-content link, color contrast check
- [ ] Final QA: visit every page, check for visual glitches, broken layouts, missing states
- [ ] Verify: `cd frontend && npm run build && npm run lint` passes
- [ ] Commit: "Agent B Task 16: Polish — demo mode, dark mode, animations, accessibility"

## Implementation Details

### Demo Overlay (`components/shared/demo-overlay.tsx`)

```tsx
"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { X, ChevronRight, ChevronLeft, Play } from "lucide-react";

interface DemoStep {
  title: string;
  description: string;
  target: string;        // CSS selector to highlight
  position: "top" | "bottom" | "left" | "right";
  persona: "talent_partner" | "client" | "admin";
}

const DEMO_STEPS: DemoStep[] = [
  // Talent Partner flow
  {
    title: "Candidate Ingestion",
    description: "Upload CVs or sync from CRMs like Bullhorn. Our AI extracts skills, experience, and seniority in real-time.",
    target: "[data-demo='candidate-upload']",
    position: "right",
    persona: "talent_partner",
  },
  {
    title: "AI-Powered Matching",
    description: "Select a role and instantly see ranked candidates with plain-English explanations of why they fit.",
    target: "[data-demo='match-results']",
    position: "bottom",
    persona: "talent_partner",
  },
  {
    title: "Copilot",
    description: "Ask questions in natural language: 'Who are my best Python candidates in London?' The system shows its working.",
    target: "[data-demo='copilot']",
    position: "left",
    persona: "talent_partner",
  },
  {
    title: "Handoff",
    description: "Refer candidates to other partners with context. Full attribution tracking through to placement.",
    target: "[data-demo='handoff']",
    position: "bottom",
    persona: "talent_partner",
  },
  // Client flow
  {
    title: "Post a Role",
    description: "Describe what you're looking for. AI extracts requirements as you type — confirm and publish.",
    target: "[data-demo='role-wizard']",
    position: "bottom",
    persona: "client",
  },
  {
    title: "Browse Candidates",
    description: "Matched candidates ranked by fit. Pre-vetted candidates from our talent pool come at a reduced placement fee.",
    target: "[data-demo='candidate-browse']",
    position: "bottom",
    persona: "client",
  },
  {
    title: "Request Introduction",
    description: "See a transparent fee breakdown. Pre-vetted candidates mean savings for you.",
    target: "[data-demo='quote']",
    position: "right",
    persona: "client",
  },
  // Admin flow
  {
    title: "Platform Analytics",
    description: "Full pipeline funnel, trending skills, partner performance — all powered by the signal layer.",
    target: "[data-demo='analytics']",
    position: "bottom",
    persona: "admin",
  },
  {
    title: "Data Quality",
    description: "Identity resolution catches duplicates across sources. Review and merge with confidence scores.",
    target: "[data-demo='dedup']",
    position: "bottom",
    persona: "admin",
  },
];

interface DemoOverlayProps {
  onClose: () => void;
}

export function DemoOverlay({ onClose }: DemoOverlayProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const step = DEMO_STEPS[currentStep];

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50 z-50" />

      {/* Tooltip card positioned near target element */}
      <Card className="fixed z-50 w-96 shadow-xl animate-in fade-in slide-in-from-bottom-4"
            style={/* position based on step.target and step.position */{}}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground">
              Step {currentStep + 1} of {DEMO_STEPS.length}
            </span>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <h3 className="font-semibold">{step.title}</h3>
          <p className="text-sm text-muted-foreground mt-1">{step.description}</p>
          <div className="flex justify-between mt-4">
            <Button
              variant="outline" size="sm"
              onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
              disabled={currentStep === 0}
            >
              <ChevronLeft className="mr-1 h-4 w-4" /> Back
            </Button>
            {currentStep < DEMO_STEPS.length - 1 ? (
              <Button size="sm" onClick={() => setCurrentStep(currentStep + 1)}>
                Next <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
            ) : (
              <Button size="sm" onClick={onClose}>
                Finish Tour
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </>
  );
}
```

### Dark Mode

Add to `frontend/app/layout.tsx`:
```tsx
import { ThemeProvider } from "next-themes";

// Wrap children in:
<ThemeProvider attribute="class" defaultTheme="light" enableSystem>
  {children}
</ThemeProvider>
```

Install: `npm install next-themes`

Add theme toggle component:
```tsx
"use client";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  return (
    <Button variant="ghost" size="icon"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
    </Button>
  );
}
```

### Page Transitions

Add to globals.css:
```css
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

main > * {
  animation: fadeIn 0.2s ease-out;
}
```

### Card Hover Effects

Update shared card components with:
```tsx
<Card className="transition-all duration-200 hover:shadow-md hover:border-border/80">
```

### Toast Notification System

Use shadcn/ui toast (already installed). Create hook:
```tsx
import { useToast } from "@/components/ui/use-toast";

// Usage in action handlers:
const { toast } = useToast();
toast({
  title: "Candidate shortlisted",
  description: "Added to your shortlist for Senior Backend Engineer",
});
```

### Keyboard Shortcuts

```tsx
"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export function useKeyboardShortcuts() {
  const router = useRouter();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Don't trigger in input fields
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      if (e.key === "/" && !e.metaKey) {
        e.preventDefault();
        // Focus search input
        document.querySelector<HTMLInputElement>("[data-search]")?.focus();
      }
      if (e.key === "Escape") {
        // Close any open modals/sheets
        document.querySelector<HTMLButtonElement>("[data-close-modal]")?.click();
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [router]);
}
```

### Accessibility Checklist

- [ ] All icon-only buttons have `aria-label`
- [ ] Focus visible rings on all interactive elements (Tailwind `focus-visible:ring-2`)
- [ ] Skip-to-content link at top of each layout
- [ ] Proper heading hierarchy (h1 → h2 → h3, no skips)
- [ ] Color contrast: all text meets WCAG AA (4.5:1 for normal text)
- [ ] Form inputs have associated labels
- [ ] Modal focus trap (shadcn Dialog handles this)
- [ ] Screen reader text for status badges

## Outputs
- `frontend/components/shared/demo-overlay.tsx`
- `frontend/app/demo/page.tsx`
- `frontend/components/shared/theme-toggle.tsx`
- `frontend/components/shared/notification-toast.tsx`
- Updated: all layout files (dark mode, keyboard shortcuts)
- Updated: all card components (hover effects)
- Updated: `globals.css` (animations)

## Acceptance Criteria
1. `cd frontend && npm run build && npm run lint` — passes
2. Demo mode launches and walks through all steps
3. Dark mode toggles cleanly across all pages
4. Page transitions are smooth (no flicker)
5. Toast notifications appear on key actions
6. Keyboard shortcuts work (/, Esc)
7. No visual glitches at 1024px, 1280px, 1440px
8. All icon buttons have aria-labels

## Handoff Notes
- **To Agent A:** Demo mode relies on `data-demo` attributes on key elements. These were added during feature tasks. If new elements need highlighting, add the attribute.
- **Final:** This is the last task. After completion, both agents should verify STATE.md shows all tasks complete and run the full success condition checks.
