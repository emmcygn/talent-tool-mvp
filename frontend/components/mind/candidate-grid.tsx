import { AnonymizedMatchCard } from "./anonymized-match-card";
import type { Match, CandidateAnonymized } from "@/contracts/canonical";

interface CandidateGridProps {
  matches: { match: Match; candidate: CandidateAnonymized }[];
  onShortlist: (matchId: string) => void;
  onDismiss: (matchId: string) => void;
  onRequestIntro: (matchId: string) => void;
}

export function CandidateGrid({ matches, onShortlist, onDismiss, onRequestIntro }: CandidateGridProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {matches.map(({ match, candidate }) => (
        <AnonymizedMatchCard
          key={match.id}
          match={match}
          candidate={candidate}
          onShortlist={onShortlist}
          onDismiss={onDismiss}
          onRequestIntro={onRequestIntro}
        />
      ))}
    </div>
  );
}
