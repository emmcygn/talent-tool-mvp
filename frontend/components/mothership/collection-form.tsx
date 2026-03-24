"use client";

import { useState } from "react";
import type { Collection, CollectionCreate, Visibility } from "@/contracts/canonical";
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
import { cn } from "@/lib/utils";

interface CollectionFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: CollectionCreate) => void;
  initial?: Collection | null;
  partners?: { id: string; first_name: string; last_name: string }[];
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
              onValueChange={(val) => val && setVisibility(val as Visibility)}
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
                    {p.first_name} {p.last_name}
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
