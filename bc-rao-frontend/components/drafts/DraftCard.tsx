"use client";

import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface DraftCardProps {
  draft: {
    id: string;
    campaign_id: string;
    subreddit: string;
    archetype: string;
    body: string;
    vulnerability_score: number;
    rhythm_score: number;
    status: string;
  };
}

const archetypeBadgeColors: Record<string, string> = {
  Journey: "bg-purple-100 text-purple-800",
  ProblemSolution: "bg-blue-100 text-blue-800",
  Feedback: "bg-green-100 text-green-800",
};

const statusBadgeColors: Record<string, string> = {
  pending: "bg-gray-100 text-gray-800",
  ready: "bg-green-100 text-green-800",
  discarded: "bg-red-100 text-red-800",
};

/**
 * Draft card for list view
 * Shows archetype, subreddit, body preview, scores, and status
 * Clickable to navigate to draft editor
 */
export default function DraftCard({ draft }: DraftCardProps) {
  const router = useRouter();

  const handleClick = () => {
    router.push(`/dashboard/campaigns/${draft.campaign_id}/drafts/${draft.id}/edit`);
  };

  // Truncate body to 150 characters
  const bodyPreview = draft.body.length > 150
    ? draft.body.substring(0, 150) + "..."
    : draft.body;

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={handleClick}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-wrap gap-2">
            <Badge className={archetypeBadgeColors[draft.archetype] || "bg-gray-100 text-gray-800"}>
              {draft.archetype}
            </Badge>
            <Badge variant="outline">r/{draft.subreddit}</Badge>
          </div>
          <Badge className={statusBadgeColors[draft.status] || "bg-gray-100 text-gray-800"}>
            {draft.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Body Preview */}
        <p className="text-sm text-muted-foreground line-clamp-3">
          {bodyPreview}
        </p>

        {/* Scores */}
        <div className="flex gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Vulnerability:</span>{" "}
            <span className="font-medium">{(draft.vulnerability_score ?? 0).toFixed(1)}/10</span>
          </div>
          <div>
            <span className="text-muted-foreground">Rhythm:</span>{" "}
            <span className="font-medium">{(draft.rhythm_score ?? 0).toFixed(1)}/10</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
