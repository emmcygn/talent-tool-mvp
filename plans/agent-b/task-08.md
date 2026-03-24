# Agent B — Task 08: Mothership — Match Results View

## Mission
Build the full match results exploration view for talent partners — ranked matches with expandable traceability, skill overlap visualization, and one-click actions.

## Context
Day 3. Shared components (Task 03) and API client with mock layer (Task 04) exist. This is the talent partner's primary matching interface — they see full candidate details (not anonymized like in Mind). Agent A is building the matching engine (Tasks 09-10) in parallel.

## Prerequisites
- Shared UI components from B-03 (match-card, skill-chips, confidence-badge)
- API client + mock layer from B-04
- Mothership layout from B-02
- Canonical types from B-01

## Checklist
- [ ] Create `frontend/app/mothership/matching/page.tsx` — match results page
- [ ] Create `frontend/components/mothership/match-detail-card.tsx` — expandable match card with traceability
- [ ] Create `frontend/components/mothership/scoring-breakdown.tsx` — visual scoring breakdown
- [ ] Create `frontend/components/mothership/match-actions.tsx` — action buttons (shortlist, add to collection, refer)
- [ ] Create filter/sort bar for match results (by confidence, score, skills, seniority)
- [ ] Add bulk actions (select multiple → add to collection, send as handoff)
- [ ] Wire to API client (matches.forRole endpoint)
- [ ] Add skeleton loading states
- [ ] Add empty state ("No matches yet — select a role to see matches")
- [ ] Verify: `cd frontend && npm run build` passes
- [ ] Commit: "Agent B Task 08: Mothership match results view"

## Implementation Details

### Match Results Page (`app/mothership/matching/page.tsx`)

```tsx
"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Match, Role, ConfidenceLevel } from "@/contracts/canonical";
import { MatchDetailCard } from "@/components/mothership/match-detail-card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { LoadingSkeleton } from "@/components/shared/loading-skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { Search, SlidersHorizontal, Users, Send } from "lucide-react";

export default function MatchingPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedRoleId, setSelectedRoleId] = useState<string | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState<"score" | "confidence">("score");
  const [filterConfidence, setFilterConfidence] = useState<ConfidenceLevel | "all">("all");

  // Fetch roles on mount, fetch matches when role selected
  // Sort and filter logic
  // Bulk action handlers

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Match Results</h1>
          <p className="text-muted-foreground">AI-matched candidates ranked by fit</p>
        </div>
        {selectedIds.size > 0 && (
          <div className="flex items-center gap-2">
            <Badge variant="secondary">{selectedIds.size} selected</Badge>
            <Button size="sm" variant="outline">
              <Users className="mr-2 h-4 w-4" /> Add to Collection
            </Button>
            <Button size="sm" variant="outline">
              <Send className="mr-2 h-4 w-4" /> Send as Handoff
            </Button>
          </div>
        )}
      </div>

      {/* Role selector + Filter bar */}
      <div className="flex gap-4 items-center">
        <Select onValueChange={setSelectedRoleId}>
          <SelectTrigger className="w-[300px]">
            <SelectValue placeholder="Select a role..." />
          </SelectTrigger>
          <SelectContent>
            {roles.map((role) => (
              <SelectItem key={role.id} value={role.id}>{role.title}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={filterConfidence} onValueChange={(v) => setFilterConfidence(v as any)}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Confidence" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All matches</SelectItem>
            <SelectItem value="strong">Strong only</SelectItem>
            <SelectItem value="good">Good+</SelectItem>
            <SelectItem value="possible">All levels</SelectItem>
          </SelectContent>
        </Select>

        <Select value={sortBy} onValueChange={(v) => setSortBy(v as any)}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="score">Highest score</SelectItem>
            <SelectItem value="confidence">Confidence level</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Match results */}
      {loading ? (
        <div className="space-y-4">
          {[1,2,3,4,5].map(i => <LoadingSkeleton key={i} variant="card" />)}
        </div>
      ) : !selectedRoleId ? (
        <EmptyState
          icon={Search}
          title="Select a role"
          description="Choose a role above to see matched candidates"
        />
      ) : matches.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No matches found"
          description="No candidates match the requirements for this role yet"
        />
      ) : (
        <div className="space-y-3">
          {matches.map((match) => (
            <MatchDetailCard
              key={match.id}
              match={match}
              selected={selectedIds.has(match.id)}
              onToggleSelect={() => toggleSelect(match.id)}
              onShortlist={() => handleShortlist(match.id)}
              onAddToCollection={() => handleAddToCollection(match.id)}
              onRefer={() => handleRefer(match.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
```

### Match Detail Card (`components/mothership/match-detail-card.tsx`)

```tsx
"use client";

import { useState } from "react";
import { Match } from "@/contracts/canonical";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { ConfidenceBadge } from "@/components/shared/confidence-badge";
import { SkillChips } from "@/components/shared/skill-chips";
import { ScoringBreakdown } from "./scoring-breakdown";
import { ChevronDown, ChevronUp, Star, FolderPlus, Send } from "lucide-react";

interface MatchDetailCardProps {
  match: Match;
  selected: boolean;
  onToggleSelect: () => void;
  onShortlist: () => void;
  onAddToCollection: () => void;
  onRefer: () => void;
}

export function MatchDetailCard({ match, selected, onToggleSelect, onShortlist, onAddToCollection, onRefer }: MatchDetailCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card className={`transition-all ${selected ? "ring-2 ring-primary" : ""}`}>
      <CardContent className="p-4">
        {/* Collapsed: candidate name, confidence badge, explanation, skill chips, actions */}
        <div className="flex items-start gap-3">
          <Checkbox checked={selected} onCheckedChange={onToggleSelect} className="mt-1" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-medium">{/* Candidate name from joined data */}</span>
                <ConfidenceBadge confidence={match.confidence} />
              </div>
              <div className="flex items-center gap-1">
                <Button size="sm" variant="ghost" onClick={onShortlist}><Star className="h-4 w-4" /></Button>
                <Button size="sm" variant="ghost" onClick={onAddToCollection}><FolderPlus className="h-4 w-4" /></Button>
                <Button size="sm" variant="ghost" onClick={onRefer}><Send className="h-4 w-4" /></Button>
              </div>
            </div>

            <p className="text-sm text-muted-foreground mt-1">{match.explanation}</p>

            <div className="mt-2">
              <SkillChips skills={match.skill_overlap} />
            </div>

            {/* Strengths + Gaps as badges */}
            <div className="flex gap-4 mt-2 text-xs">
              <div className="flex gap-1 flex-wrap">
                {match.strengths.map((s, i) => (
                  <Badge key={i} variant="outline" className="bg-green-50 text-green-700 text-xs">{s}</Badge>
                ))}
              </div>
              <div className="flex gap-1 flex-wrap">
                {match.gaps.map((g, i) => (
                  <Badge key={i} variant="outline" className="bg-amber-50 text-amber-700 text-xs">{g}</Badge>
                ))}
              </div>
            </div>

            {/* Expand toggle */}
            <Button
              variant="ghost" size="sm"
              className="mt-2 text-xs"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? <ChevronUp className="mr-1 h-3 w-3" /> : <ChevronDown className="mr-1 h-3 w-3" />}
              {expanded ? "Hide details" : "Show scoring breakdown"}
            </Button>

            {/* Expanded: full traceability */}
            {expanded && (
              <div className="mt-3 pt-3 border-t">
                <ScoringBreakdown match={match} />
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Scoring Breakdown (`components/mothership/scoring-breakdown.tsx`)

```tsx
import { Match } from "@/contracts/canonical";
import { Progress } from "@/components/ui/progress";

interface ScoringBreakdownProps {
  match: Match;
}

export function ScoringBreakdown({ match }: ScoringBreakdownProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <div>
          <p className="text-xs text-muted-foreground mb-1">Skill Overlap (40%)</p>
          <Progress value={match.structured_score * 100} className="h-2" />
          <p className="text-xs font-medium mt-1">{(match.structured_score * 100).toFixed(0)}%</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground mb-1">Semantic Match (35%)</p>
          <Progress value={match.semantic_score * 100} className="h-2" />
          <p className="text-xs font-medium mt-1">{(match.semantic_score * 100).toFixed(0)}%</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground mb-1">Experience Fit (25%)</p>
          <Progress value={match.overall_score * 100} className="h-2" />
          <p className="text-xs font-medium mt-1">{(match.overall_score * 100).toFixed(0)}%</p>
        </div>
      </div>

      <div>
        <p className="text-xs text-muted-foreground mb-1">Recommendation</p>
        <p className="text-sm">{match.recommendation}</p>
      </div>

      <div className="text-xs text-muted-foreground">
        Model: {match.model_version} · Generated: {new Date(match.created_at).toLocaleDateString("en-GB")}
      </div>
    </div>
  );
}
```

## Outputs
- `frontend/app/mothership/matching/page.tsx`
- `frontend/components/mothership/match-detail-card.tsx`
- `frontend/components/mothership/scoring-breakdown.tsx`
- `frontend/components/mothership/match-actions.tsx`

## Acceptance Criteria
1. `cd frontend && npm run build` — builds successfully
2. Match results page renders with mock data
3. Expanding a match shows full scoring breakdown
4. Filter by confidence level works
5. Bulk selection + action buttons appear when items selected

## Handoff Notes
- **To Agent A:** Match results consume the `Match` contract. Ensure the `skill_overlap` field is populated with `SkillMatch` objects for the chips to render correctly.
- **To Task 09:** Collections UI can reuse the match card pattern for displaying candidates within collections.
- **Decision:** Scoring breakdown shows percentages for talent partners (unlike Mind which hides raw numbers). This is intentional — talent partners are semi-technical and want to understand the matching logic.
