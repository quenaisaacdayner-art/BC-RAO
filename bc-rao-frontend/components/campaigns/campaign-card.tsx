"use client";

import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Edit, Trash2 } from "lucide-react";

interface CampaignCardProps {
  campaign: {
    id: string;
    name: string;
    status: "active" | "paused" | "archived";
    product_context: string;
    keywords: string[];
    target_subreddits: string[];
    stats?: {
      posts_collected: number;
      drafts_generated: number;
      active_monitors: number;
    };
  };
  onDelete?: (id: string) => void;
}

export function CampaignCard({ campaign, onDelete }: CampaignCardProps) {
  const router = useRouter();

  const statusColors = {
    active: "bg-green-500/10 text-green-500 border-green-500/20",
    paused: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
    archived: "bg-gray-500/10 text-gray-500 border-gray-500/20",
  };

  const stats = campaign.stats || {
    posts_collected: 0,
    drafts_generated: 0,
    active_monitors: 0,
  };

  // Truncate product context to 2 lines (~120 chars)
  const truncatedContext =
    campaign.product_context.length > 120
      ? campaign.product_context.substring(0, 120) + "..."
      : campaign.product_context;

  // Show first 5 keywords, "+N more" if more
  const displayKeywords = campaign.keywords.slice(0, 5);
  const remainingKeywords = campaign.keywords.length - 5;

  return (
    <Card
      className="cursor-pointer transition-colors hover:border-primary/50"
      onClick={() => router.push(`/dashboard/campaigns/${campaign.id}`)}
    >
      <CardHeader className="space-y-2">
        <div className="flex items-start justify-between">
          <CardTitle className="text-xl">{campaign.name}</CardTitle>
          <span
            className={`rounded-full border px-2 py-1 text-xs font-medium ${
              statusColors[campaign.status]
            }`}
          >
            {campaign.status}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground line-clamp-2">
          {truncatedContext}
        </p>

        <div className="space-y-2">
          <div className="flex flex-wrap gap-1">
            {displayKeywords.map((keyword) => (
              <span
                key={keyword}
                className="rounded-md bg-secondary px-2 py-1 text-xs"
              >
                {keyword}
              </span>
            ))}
            {remainingKeywords > 0 && (
              <span className="rounded-md bg-secondary px-2 py-1 text-xs text-muted-foreground">
                +{remainingKeywords} more
              </span>
            )}
          </div>

          <div className="text-xs text-muted-foreground">
            {campaign.target_subreddits.map((sub, idx) => (
              <span key={sub}>
                r/{sub}
                {idx < campaign.target_subreddits.length - 1 ? ", " : ""}
              </span>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between border-t pt-3 text-sm">
          <div className="flex gap-4 text-muted-foreground">
            <span>Posts: {stats.posts_collected}</span>
            <span>Drafts: {stats.drafts_generated}</span>
            <span>Monitors: {stats.active_monitors}</span>
          </div>

          <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
            <Button
              variant="ghost"
              size="sm"
              onClick={() =>
                router.push(`/dashboard/campaigns/${campaign.id}/edit`)
              }
            >
              <Edit className="h-4 w-4" />
            </Button>
            {onDelete && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDelete(campaign.id)}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
