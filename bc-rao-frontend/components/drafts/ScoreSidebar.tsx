"use client";

import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";

interface ScoreSidebarProps {
  vulnerabilityScore: number;
  rhythmMatchScore: number;
  metadata: {
    subreddit: string;
    archetype: string;
    generatedAt: string;
  };
}

// Score tier determination
function getScoreTier(score: number): string {
  if (score >= 8) return "Excellent";
  if (score >= 6) return "Good";
  if (score >= 4) return "Moderate";
  return "Low";
}

// Color coding by tier
const tierColors: Record<string, { text: string; bg: string; progress: string }> = {
  "Excellent": { text: "text-green-700", bg: "bg-green-100", progress: "bg-green-500" },
  "Good": { text: "text-blue-700", bg: "bg-blue-100", progress: "bg-blue-500" },
  "Moderate": { text: "text-yellow-700", bg: "bg-yellow-100", progress: "bg-yellow-500" },
  "Low": { text: "text-red-700", bg: "bg-red-100", progress: "bg-red-500" },
};

function ScoreGauge({ score, label }: { score: number; label: string }) {
  const tier = getScoreTier(score);
  const colors = tierColors[tier];
  const progressValue = (score / 10) * 100;

  return (
    <div className="space-y-3">
      {/* Score Display */}
      <div className="text-center">
        <div className="text-4xl font-bold tabular-nums mb-1">
          {score.toFixed(1)}
        </div>
        <div className="text-sm text-muted-foreground mb-2">{label}</div>
        <div className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${colors.bg} ${colors.text}`}>
          {tier}
        </div>
      </div>

      {/* Visual Gauge */}
      <div className="space-y-1.5">
        <Progress value={progressValue} className="h-2" />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>0</span>
          <span>5</span>
          <span>10</span>
        </div>
      </div>
    </div>
  );
}

export default function ScoreSidebar({ vulnerabilityScore, rhythmMatchScore, metadata }: ScoreSidebarProps) {
  return (
    <Card className="p-6 space-y-6">
      {/* Vulnerability Score */}
      <ScoreGauge score={vulnerabilityScore} label="Vulnerability Score" />

      <Separator />

      {/* Rhythm Match Score */}
      <ScoreGauge score={rhythmMatchScore} label="Rhythm Match Score" />

      <Separator />

      {/* Metadata */}
      <div className="space-y-3 text-sm">
        <div>
          <div className="text-muted-foreground mb-1">Subreddit</div>
          <div className="font-medium">r/{metadata.subreddit}</div>
        </div>
        <div>
          <div className="text-muted-foreground mb-1">Archetype</div>
          <div className="font-medium">{metadata.archetype}</div>
        </div>
        <div>
          <div className="text-muted-foreground mb-1">Generated</div>
          <div className="font-medium">
            {new Date(metadata.generatedAt).toLocaleString()}
          </div>
        </div>
      </div>

      <Separator />

      {/* Note */}
      <p className="text-xs text-muted-foreground leading-relaxed">
        Scores reflect the generated draft only. Manual editing is free-form and does not trigger re-scoring.
      </p>
    </Card>
  );
}
