import { AnonymizedMatchCard } from "./anonymized-match-card";
import type { Match, CandidateAnonymized } from "@/contracts/canonical";

interface CandidateListProps {
  matches: { match: Match; candidate: CandidateAnonymized }[];
  onShortlist: (matchId: string) => void;
  onDismiss: (matchId: string) => void;
  onRequestIntro: (matchId: string) => void;
}

export function CandidateList({ matches, onShortlist, onDismiss, onRequestIntro }: CandidateListProps) {
  return (
    <div className="space-y-3">
      {matches.map(({ match, candidate }) => (
        <AnonymizedMatchCard
          key={match.id}
          match={match}
          candidate={candidate}
          layout="horizontal"
          onShortlist={onShortlist}
          onDismiss={onDismiss}
          onRequestIntro={onRequestIntro}
        />
      ))}
    </div>
  );
}
