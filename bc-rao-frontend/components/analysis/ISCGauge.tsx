"use client";

import { Progress } from "@/components/ui/progress";

interface ISCGaugeProps {
  score: number;
  tier: string;
}

// Color coding by tier (backend returns "X Sensitivity" format)
const tierColors: Record<string, { text: string; bg: string; progress: string }> = {
  "Low Sensitivity": { text: "text-green-700", bg: "bg-green-100", progress: "bg-green-500" },
  "Moderate Sensitivity": { text: "text-yellow-700", bg: "bg-yellow-100", progress: "bg-yellow-500" },
  "High Sensitivity": { text: "text-orange-700", bg: "bg-orange-100", progress: "bg-orange-500" },
  "Very High Sensitivity": { text: "text-red-700", bg: "bg-red-100", progress: "bg-red-500" },
};

export default function ISCGauge({ score, tier }: ISCGaugeProps) {
  const colors = tierColors[tier] || tierColors["Moderate Sensitivity"];
  const progressValue = ((score ?? 0) / 10) * 100;

  return (
    <div className="space-y-4">
      {/* Score Display */}
      <div className="text-center">
        <div className="text-5xl font-bold tabular-nums mb-2">
          {(score ?? 0).toFixed(1)}
        </div>
        <div className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${colors.bg} ${colors.text}`}>
          {tier}
        </div>
      </div>

      {/* Visual Gauge */}
      <div className="space-y-2">
        <div className="relative">
          <Progress value={progressValue} className="h-3" />
          <style jsx global>{`
            .${colors.progress.replace('bg-', '')} {
              background-color: var(--${colors.progress.replace('bg-', '')});
            }
          `}</style>
        </div>
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>1.0</span>
          <span>5.0</span>
          <span>10.0</span>
        </div>
      </div>

      {/* Tier Description */}
      <p className="text-xs text-muted-foreground text-center">
        {tier === "Low Sensitivity" && "Community has relaxed content standards"}
        {tier === "Moderate Sensitivity" && "Community has balanced moderation"}
        {tier === "High Sensitivity" && "Community is strict about content quality"}
        {tier === "Very High Sensitivity" && "Community is extremely sensitive to promotional content"}
      </p>
    </div>
  );
}
