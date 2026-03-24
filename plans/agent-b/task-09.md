# Agent B — Task 09: Mothership — Collections UI

## Mission
Build the full collections management interface for talent partners: create/edit collections, visibility controls, browsable grid with aggregate stats, candidate list within collections, and shared collection browsing.

## Context
Day 4. Collections let talent partners organize candidates into themed groups ("Senior Backend — London", "ML Engineers — Remote OK"). Collections can be private or shared with specific partners or all partners. This is a core collaboration feature — shared collections are how partners discover each other's curated talent pools.

## Prerequisites
- B-01: Next.js scaffold, TypeScript contracts, shadcn/ui installed
- B-03: Shared UI components (candidate-card, skill-chips, confidence-badge, loading-skeleton, empty-state)
- B-04: API client with `api.collections.*` methods

## Checklist
- [ ] Create `CollectionCard` component (`components/mothership/collection-card.tsx`)
- [ ] Create `CollectionForm` component (create + edit dialog)
- [ ] Create `CollectionDetail` view (candidate list within a collection)
- [ ] Create collections page (`app/mothership/collections/page.tsx`) with grid layout
- [ ] Implement visibility toggle (private / shared specific / shared all)
- [ ] Implement tag input for collection tags
- [ ] Implement add/remove candidates from a collection
- [ ] Add shared collections sidebar section
- [ ] Wire to API client with loading and empty states
- [ ] Commit: "Agent B Task 09: Mothership — Collections UI"

## Implementation Details

### Collection Card (`components/mothership/collection-card.tsx`)

```tsx
"use client";

import { Collection, AvailabilityStatus } from "@/contracts/canonical";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, Eye, EyeOff, Share2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface CollectionCardProps {
  collection: Collection;
  onClick?: () => void;
  isShared?: boolean;
}

function visibilityIcon(visibility: string) {
  switch (visibility) {
    case "private": return <EyeOff className="h-3.5 w-3.5 text-slate-400" />;
    case "shared_specific": return <Share2 className="h-3.5 w-3.5 text-blue-500" />;
    case "shared_all": return <Eye className="h-3.5 w-3.5 text-green-500" />;
    default: return null;
  }
}

function visibilityLabel(visibility: string) {
  switch (visibility) {
    case "private": return "Private";
    case "shared_specific": return "Shared with select";
    case "shared_all": return "Shared with all";
    default: return visibility;
  }
}

export function CollectionCard({ collection, onClick, isShared }: CollectionCardProps) {
  return (
    <Card
      className={cn(
        "cursor-pointer transition-all hover:shadow-md hover:border-slate-300",
        isShared && "border-blue-100 bg-blue-50/30"
      )}
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <CardTitle className="text-base font-semibold leading-tight">
            {collection.name}
          </CardTitle>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            {visibilityIcon(collection.visibility)}
            <span>{visibilityLabel(collection.visibility)}</span>
          </div>
        </div>
        {collection.description && (
          <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
            {collection.description}
          </p>
        )}
      </CardHeader>
      <CardContent className="pt-0">
        {/* Tags */}
        {collection.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {collection.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs font-normal">
                {tag}
              </Badge>
            ))}
          </div>
        )}

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="rounded-md bg-slate-50 px-2 py-1.5">
            <div className="text-lg font-semibold text-slate-900">
              {collection.candidate_count}
            </div>
            <div className="text-[11px] text-muted-foreground">Candidates</div>
          </div>
          <div className="rounded-md bg-green-50 px-2 py-1.5">
            <div className="text-lg font-semibold text-green-700">
              {collection.available_now_count}
            </div>
            <div className="text-[11px] text-muted-foreground">Available</div>
          </div>
          <div className="rounded-md bg-amber-50 px-2 py-1.5">
            <div className="text-lg font-semibold text-amber-700">
              {collection.avg_match_score
                ? `${Math.round(collection.avg_match_score * 100)}%`
                : "—"}
            </div>
            <div className="text-[11px] text-muted-foreground">Avg Match</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Collection Form Dialog (`components/mothership/collection-form.tsx`)

```tsx
"use client";

import { useState } from "react";
import { Collection, CollectionCreate, Visibility } from "@/contracts/canonical";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { X, Plus } from "lucide-react";

interface CollectionFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: CollectionCreate) => void;
  initial?: Collection | null;
  partners?: { id: string; full_name: string }[];
}

export function CollectionForm({
  open, onOpenChange, onSubmit, initial, partners = [],
}: CollectionFormProps) {
  const [name, setName] = useState(initial?.name ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [visibility, setVisibility] = useState<Visibility>(initial?.visibility ?? "private");
  const [sharedWith, setSharedWith] = useState<string[]>(initial?.shared_with ?? []);
  const [tags, setTags] = useState<string[]>(initial?.tags ?? []);
  const [tagInput, setTagInput] = useState("");

  function addTag() {
    const trimmed = tagInput.trim().toLowerCase();
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed]);
    }
    setTagInput("");
  }

  function removeTag(tag: string) {
    setTags(tags.filter((t) => t !== tag));
  }

  function handleSubmit() {
    onSubmit({
      name,
      description: description || null,
      visibility,
      shared_with: visibility === "shared_specific" ? sharedWith : null,
      tags,
    });
    onOpenChange(false);
  }

  const isEdit = !!initial;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Collection" : "New Collection"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update collection details and visibility settings."
              : "Create a themed collection to organize candidates."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Name */}
          <div className="space-y-1.5">
            <Label htmlFor="col-name">Name</Label>
            <Input
              id="col-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Senior Backend — London"
            />
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <Label htmlFor="col-desc">Description</Label>
            <Textarea
              id="col-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What is this collection for?"
              rows={2}
            />
          </div>

          {/* Tags */}
          <div className="space-y-1.5">
            <Label>Tags</Label>
            <div className="flex flex-wrap gap-1 mb-2">
              {tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="gap-1 pr-1">
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeTag(tag)}
                    className="ml-0.5 rounded-full p-0.5 hover:bg-slate-200"
                    aria-label={`Remove tag ${tag}`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
            </div>
            <div className="flex gap-2">
              <Input
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") { e.preventDefault(); addTag(); }
                }}
                placeholder="Add a tag..."
                className="flex-1"
              />
              <Button type="button" size="sm" variant="outline" onClick={addTag}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Visibility */}
          <div className="space-y-1.5">
            <Label>Visibility</Label>
            <Select
              value={visibility}
              onValueChange={(v) => setVisibility(v as Visibility)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="private">Private — only you</SelectItem>
                <SelectItem value="shared_specific">Shared — select partners</SelectItem>
                <SelectItem value="shared_all">Shared — all partners</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Shared with (conditional) */}
          {visibility === "shared_specific" && (
            <div className="space-y-1.5">
              <Label>Share with</Label>
              <div className="flex flex-wrap gap-2">
                {partners.map((p) => (
                  <label
                    key={p.id}
                    className={cn(
                      "flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm cursor-pointer transition-colors",
                      sharedWith.includes(p.id)
                        ? "border-blue-300 bg-blue-50 text-blue-800"
                        : "border-slate-200 hover:bg-slate-50"
                    )}
                  >
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={sharedWith.includes(p.id)}
                      onChange={(e) => {
                        setSharedWith(
                          e.target.checked
                            ? [...sharedWith, p.id]
                            : sharedWith.filter((id) => id !== p.id)
                        );
                      }}
                    />
                    {p.full_name}
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!name.trim()}>
            {isEdit ? "Update" : "Create Collection"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}
```

### Collection Detail View (`components/mothership/collection-detail.tsx`)

```tsx
"use client";

import { useState } from "react";
import { Collection, Candidate } from "@/contracts/canonical";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  ArrowLeft, Edit, Trash2, UserPlus, UserMinus, Search,
  Eye, EyeOff, Share2,
} from "lucide-react";
// import { CandidateCard } from "@/components/shared/candidate-card";

interface CollectionDetailProps {
  collection: Collection;
  candidates: Candidate[];
  allCandidates: Candidate[]; // for add-candidate search
  onBack: () => void;
  onEdit: () => void;
  onRemoveCandidate: (candidateId: string) => void;
  onAddCandidate: (candidateId: string) => void;
}

export function CollectionDetail({
  collection, candidates, allCandidates,
  onBack, onEdit, onRemoveCandidate, onAddCandidate,
}: CollectionDetailProps) {
  const [addMode, setAddMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredAdd = allCandidates.filter(
    (c) =>
      !collection.candidate_ids.includes(c.id) &&
      `${c.first_name} ${c.last_name}`.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={onBack} aria-label="Back to collections">
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h2 className="text-xl font-semibold">{collection.name}</h2>
            {collection.description && (
              <p className="text-sm text-muted-foreground mt-0.5">{collection.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setAddMode(!addMode)}>
            <UserPlus className="h-4 w-4 mr-1.5" />
            Add Candidates
          </Button>
          <Button variant="outline" size="sm" onClick={onEdit}>
            <Edit className="h-4 w-4 mr-1.5" />
            Edit
          </Button>
        </div>
      </div>

      {/* Tags + stats */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-1 text-sm text-muted-foreground">
          {collection.visibility === "private" && <EyeOff className="h-3.5 w-3.5" />}
          {collection.visibility === "shared_specific" && <Share2 className="h-3.5 w-3.5 text-blue-500" />}
          {collection.visibility === "shared_all" && <Eye className="h-3.5 w-3.5 text-green-500" />}
          <span className="capitalize">{collection.visibility.replace("_", " ")}</span>
        </div>
        <span className="text-sm text-muted-foreground">
          {collection.candidate_count} candidate{collection.candidate_count !== 1 ? "s" : ""}
        </span>
        {collection.tags.map((tag) => (
          <Badge key={tag} variant="secondary" className="text-xs">{tag}</Badge>
        ))}
      </div>

      {/* Add candidates panel */}
      {addMode && (
        <div className="rounded-lg border border-dashed border-blue-300 bg-blue-50/50 p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-muted-foreground" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search candidates to add..."
              className="flex-1 bg-white"
            />
          </div>
          <div className="max-h-60 overflow-y-auto space-y-1">
            {filteredAdd.slice(0, 10).map((c) => (
              <div
                key={c.id}
                className="flex items-center justify-between rounded-md px-3 py-2 hover:bg-white transition-colors"
              >
                <span className="text-sm font-medium">
                  {c.first_name} {c.last_name}
                  <span className="text-muted-foreground ml-2">{c.location}</span>
                </span>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onAddCandidate(c.id)}
                >
                  <UserPlus className="h-3.5 w-3.5" />
                </Button>
              </div>
            ))}
            {filteredAdd.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">
                No candidates available to add.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Candidate list */}
      <div className="space-y-3">
        {candidates.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No candidates in this collection yet.</p>
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => setAddMode(true)}
            >
              <UserPlus className="h-4 w-4 mr-1.5" />
              Add your first candidate
            </Button>
          </div>
        ) : (
          candidates.map((candidate) => (
            <div
              key={candidate.id}
              className="flex items-center justify-between rounded-lg border p-4 hover:bg-slate-50/50 transition-colors"
            >
              {/* Replace with <CandidateCard> when shared components are ready */}
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm">
                  {candidate.first_name} {candidate.last_name}
                </div>
                <div className="text-xs text-muted-foreground mt-0.5">
                  {candidate.location} · {candidate.seniority ?? "—"} ·{" "}
                  {candidate.availability?.replace("_", " ") ?? "Unknown"}
                </div>
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {candidate.skills.slice(0, 5).map((s) => (
                    <Badge key={s.name} variant="outline" className="text-[11px] py-0">
                      {s.name}
                    </Badge>
                  ))}
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onRemoveCandidate(candidate.id)}
                className="text-red-400 hover:text-red-600 hover:bg-red-50"
                aria-label={`Remove ${candidate.first_name} from collection`}
              >
                <UserMinus className="h-4 w-4" />
              </Button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
```

### Collections Page (`app/mothership/collections/page.tsx`)

```tsx
"use client";

import { useState, useEffect } from "react";
import { Collection, CollectionCreate, Candidate } from "@/contracts/canonical";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { CollectionCard } from "@/components/mothership/collection-card";
import { CollectionForm } from "@/components/mothership/collection-form";
import { CollectionDetail } from "@/components/mothership/collection-detail";
import { Plus, FolderOpen, Search, Users } from "lucide-react";

export default function CollectionsPage() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [sharedCollections, setSharedCollections] = useState<Collection[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Collection | null>(null);
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [ownCols, allCols, allCandidates] = await Promise.all([
          api.collections.list(),
          api.collections.list(), // API returns own + shared collections
          api.candidates.list(),
        ]);
        // Separate own vs shared (own = owner_id matches current user)
        setCollections(ownCols);
        setSharedCollections(allCols.filter((c) => c.visibility !== "private"));
        setCandidates(allCandidates);
      } catch {
        // Handle error
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleCreate(data: CollectionCreate) {
    const created = await api.collections.create(data);
    setCollections([created, ...collections]);
  }

  function handleEdit(col: Collection) {
    setEditTarget(col);
    setFormOpen(true);
  }

  const filtered = collections.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  // Detail view
  if (selectedCollection) {
    const collectionCandidates = candidates.filter((c) =>
      selectedCollection.candidate_ids.includes(c.id)
    );
    return (
      <div className="p-6 max-w-5xl">
        <CollectionDetail
          collection={selectedCollection}
          candidates={collectionCandidates}
          allCandidates={candidates}
          onBack={() => setSelectedCollection(null)}
          onEdit={() => handleEdit(selectedCollection)}
          onRemoveCandidate={(candidateId) => {
            // Remove from local state; call API
          }}
          onAddCandidate={(candidateId) => {
            // Add to local state; call API
          }}
        />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Collections</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Organize candidates into themed groups and share with your team.
          </p>
        </div>
        <Button onClick={() => { setEditTarget(null); setFormOpen(true); }}>
          <Plus className="h-4 w-4 mr-1.5" />
          New Collection
        </Button>
      </div>

      {/* Search */}
      <div className="relative mb-6 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search collections or tags..."
          className="pl-9"
        />
      </div>

      {/* My Collections */}
      <section>
        <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
          <FolderOpen className="h-4 w-4" />
          My Collections
        </h2>
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-48 rounded-lg" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-12 border rounded-lg border-dashed">
            <FolderOpen className="h-10 w-10 mx-auto text-muted-foreground/50 mb-3" />
            <p className="text-muted-foreground">No collections yet.</p>
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => { setEditTarget(null); setFormOpen(true); }}
            >
              Create your first collection
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((col) => (
              <CollectionCard
                key={col.id}
                collection={col}
                onClick={() => setSelectedCollection(col)}
              />
            ))}
          </div>
        )}
      </section>

      {/* Shared Collections */}
      <Separator className="my-8" />

      <section>
        <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-3 flex items-center gap-2">
          <Users className="h-4 w-4" />
          Shared by Partners
        </h2>
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-48 rounded-lg" />
            ))}
          </div>
        ) : sharedCollections.length === 0 ? (
          <p className="text-sm text-muted-foreground py-4">
            No shared collections from other partners yet.
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sharedCollections.map((col) => (
              <CollectionCard
                key={col.id}
                collection={col}
                onClick={() => setSelectedCollection(col)}
                isShared
              />
            ))}
          </div>
        )}
      </section>

      {/* Create/Edit Dialog */}
      <CollectionForm
        open={formOpen}
        onOpenChange={setFormOpen}
        onSubmit={handleCreate}
        initial={editTarget}
      />
    </div>
  );
}
```

## Outputs
- `frontend/components/mothership/collection-card.tsx` — Collection summary card with stats
- `frontend/components/mothership/collection-form.tsx` — Create/edit dialog with visibility + tags
- `frontend/components/mothership/collection-detail.tsx` — Candidate list within a collection
- `frontend/app/mothership/collections/page.tsx` — Main collections page with grid + shared section

## Acceptance Criteria
1. Collections display in a responsive grid showing name, candidate count, availability count, avg match quality
2. Create/edit dialog allows setting name, description, tags, and visibility
3. Visibility toggle correctly shows/hides the "shared with" partner selector
4. Clicking a collection card opens the detail view with candidate list
5. Add/remove candidate actions work within the detail view
6. Shared collections from other partners appear in a separate section
7. Loading skeletons display while data loads
8. Empty state shows when no collections exist

## Handoff Notes
- **To Agent A:** Frontend expects `GET /api/collections` to return both own and shared collections. Needs `POST /api/collections/{id}/candidates` for add and `DELETE /api/collections/{id}/candidates/{candidateId}` for remove.
- **To Task 13:** Collection count and recent collections can be surfaced on the talent partner dashboard.
- **Decision:** Using a flat grid view rather than sidebar navigation for collections — simpler and more visual. Shared collections use a blue tint to visually differentiate from own collections.
