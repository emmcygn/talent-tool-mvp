"use client";

import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

interface SkillTrend {
  skill: string;
  demand: number;
  supply: number;
}

interface TrendingSkillsChartProps {
  data: SkillTrend[];
}

const COLORS = [
  "#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe",
  "#818cf8", "#4f46e5", "#4338ca",
];

export function TrendingSkillsChart({ data }: TrendingSkillsChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical" margin={{ left: 80 }}>
        <XAxis type="number" tick={{ fontSize: 12 }} />
        <YAxis
          type="category"
          dataKey="skill"
          tick={{ fontSize: 12 }}
          width={80}
        />
        <Tooltip
          contentStyle={{
            fontSize: 12,
            borderRadius: 8,
            border: "1px solid #e2e8f0",
            boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
          }}
        />
        <Bar dataKey="demand" name="Demand (roles)" radius={[0, 4, 4, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
        <Bar dataKey="supply" name="Supply (candidates)" fill="#94a3b8" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
