import { Badge } from "@/components/ui/badge";
import type { SkillMatch } from "@/contracts/canonical";
import { cn, skillMatchColor } from "@/lib/utils";

interface SkillChipsProps {
  skills: SkillMatch[];
  maxDisplay?: number;
  className?: string;
}

export function SkillChips({ skills, maxDisplay = 8, className }: SkillChipsProps) {
  const sorted = [...skills].sort((a, b) => {
    const order = { matched: 0, partial: 1, missing: 2 };
    return order[a.status] - order[b.status];
  });

  const displayed = sorted.slice(0, maxDisplay);
  const remaining = sorted.length - maxDisplay;

  return (
    <div className={cn("flex flex-wrap gap-1.5", className)}>
      {displayed.map((skill) => (
        <Badge
          key={skill.skill_name}
          variant="outline"
          className={cn("text-xs font-normal border", skillMatchColor(skill.status))}
        >
          {skill.skill_name}
          {skill.candidate_years != null && (
            <span className="ml-1 opacity-70">{skill.candidate_years}y</span>
          )}
          {skill.required_years != null && (
            <span className="ml-0.5 opacity-50">/{skill.required_years}y</span>
          )}
        </Badge>
      ))}
      {remaining > 0 && (
        <Badge variant="outline" className="text-xs font-normal text-slate-400 border-slate-200">
          +{remaining} more
        </Badge>
      )}
    </div>
  );
}
