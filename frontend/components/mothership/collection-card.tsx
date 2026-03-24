"use client";

import type { Collection } from "@/contracts/canonical";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Eye, EyeOff, Share2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface CollectionCardProps {
  collection: Collection;
  onClick?: () => void;
  isShared?: boolean;
}

function visibilityIcon(visibility: string) {
  switch (visibility) {
    case "private":
      return <EyeOff className="h-3.5 w-3.5 text-slate-400" />;
    case "shared_specific":
      return <Share2 className="h-3.5 w-3.5 text-blue-500" />;
    case "shared_all":
      return <Eye className="h-3.5 w-3.5 text-green-500" />;
    default:
      return null;
  }
}

function visibilityLabel(visibility: string) {
  switch (visibility) {
    case "private":
      return "Private";
    case "shared_specific":
      return "Shared with select";
    case "shared_all":
      return "Shared with all";
    default:
      return visibility;
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
                : "\u2014"}
            </div>
            <div className="text-[11px] text-muted-foreground">Avg Match</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
