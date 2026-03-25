"use client";

import { useState, useEffect } from "react";
import type { Collection, CollectionCreate, Candidate } from "@/contracts/canonical";
import { apiClient } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { CollectionCard } from "@/components/mothership/collection-card";
import { CollectionForm } from "@/components/mothership/collection-form";
import { CollectionDetail } from "@/components/mothership/collection-detail";
import { Plus, FolderOpen, Search, Users } from "lucide-react";
import { toast } from "sonner";

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
        const [allCols, allCandidates] = await Promise.all([
          apiClient.collections.list(),
          apiClient.candidates.list(),
        ]);
        setCollections(allCols);
        setSharedCollections(allCols.filter((c: Collection) => c.visibility !== "private"));
        setCandidates(allCandidates);
      } catch {
        toast.error("Failed to load collections");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleSubmit(data: CollectionCreate) {
    try {
      if (editTarget) {
        // Optimistic update — no update endpoint available yet
        const updated: Collection = {
          ...editTarget,
          ...data,
          shared_with: data.shared_with ?? [],
          description: data.description ?? "",
          updated_at: new Date().toISOString(),
        };
        setCollections(collections.map((c) => (c.id === editTarget.id ? updated : c)));
        toast.success("Collection updated");
      } else {
        const created = await apiClient.collections.create(data);
        setCollections([created, ...collections]);
        toast.success("Collection created");
      }
    } catch {
      toast.error(editTarget ? "Failed to update collection" : "Failed to create collection");
    }
  }

  function handleEdit(col: Collection) {
    setEditTarget(col);
    setFormOpen(true);
  }

  async function handleRemoveCandidate(candidateId: string) {
    if (!selectedCollection) return;
    try {
      await apiClient.collections.removeCandidate(selectedCollection.id, candidateId);
      const updated = {
        ...selectedCollection,
        candidate_ids: selectedCollection.candidate_ids.filter((id) => id !== candidateId),
        candidate_count: selectedCollection.candidate_count - 1,
      };
      setSelectedCollection(updated);
      setCollections(collections.map((c) => (c.id === updated.id ? updated : c)));
      toast.success("Candidate removed from collection");
    } catch {
      toast.error("Failed to remove candidate");
    }
  }

  async function handleAddCandidate(candidateId: string) {
    if (!selectedCollection) return;
    try {
      const updated = await apiClient.collections.addCandidate(selectedCollection.id, candidateId);
      setSelectedCollection(updated);
      setCollections(collections.map((c) => (c.id === updated.id ? updated : c)));
      toast.success("Candidate added to collection");
    } catch {
      toast.error("Failed to add candidate");
    }
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
      <div className="p-4 md:p-6 max-w-5xl">
        <CollectionDetail
          collection={selectedCollection}
          candidates={collectionCandidates}
          allCandidates={candidates}
          onBack={() => setSelectedCollection(null)}
          onEdit={() => handleEdit(selectedCollection)}
          onRemoveCandidate={handleRemoveCandidate}
          onAddCandidate={handleAddCandidate}
        />
      </div>
    );
  }

  return (
    <div className="p-0 max-w-6xl">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
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
        key={editTarget?.id ?? "new"}
        open={formOpen}
        onOpenChange={setFormOpen}
        onSubmit={handleSubmit}
        initial={editTarget}
      />
    </div>
  );
}
