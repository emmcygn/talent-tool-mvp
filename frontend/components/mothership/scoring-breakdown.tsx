import type { Match } from "@/contracts/canonical";
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
