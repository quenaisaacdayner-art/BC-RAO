"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts";

interface ArchetypeDistribution {
  archetype: string;
  count: number;
}

interface ArchetypePieProps {
  distribution: ArchetypeDistribution[];
}

// Color mapping for archetypes
const ARCHETYPE_COLORS: Record<string, string> = {
  Journey: "#3B82F6", // blue
  ProblemSolution: "#10B981", // green
  Feedback: "#F59E0B", // amber
  Unclassified: "#6B7280", // gray
};

export default function ArchetypePie({ distribution }: ArchetypePieProps) {
  // Transform data for Recharts
  const data = distribution.map((item) => ({
    name: item.archetype,
    value: item.count,
    color: ARCHETYPE_COLORS[item.archetype] || "#6B7280",
  }));

  // Calculate total for percentage
  const total = data.reduce((sum, item) => sum + item.value, 0);

  // Custom label to show count
  const renderLabel = (entry: any) => {
    const percent = ((entry.value / total) * 100).toFixed(0);
    return `${entry.value} (${percent}%)`;
  };

  return (
    <div className="w-full h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
            label={renderLabel}
            labelLine={false}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number | undefined) => [`${value || 0} posts`, "Count"]}
            contentStyle={{
              backgroundColor: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
            }}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value) => {
              const item = data.find((d) => d.name === value);
              return `${value} (${item?.value || 0})`;
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
