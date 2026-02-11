"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChevronDown, ChevronRight } from "lucide-react";

interface FunnelStatsProps {
  stats: {
    scraped: number;
    filtered: number;
    classified: number;
    filter_rate: number;
    by_archetype: {
      Journey: number;
      ProblemSolution: number;
      Feedback: number;
    };
    by_subreddit: Record<string, number>;
  };
}

export default function FunnelStats({ stats }: FunnelStatsProps) {
  const [showFilterDetails, setShowFilterDetails] = useState(false);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Collection Funnel</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Three-step funnel visualization */}
        <div className="flex items-center justify-center gap-3 text-sm">
          <div className="text-center">
            <p className="text-3xl font-bold">{stats.scraped}</p>
            <p className="text-xs text-muted-foreground">Scraped</p>
          </div>

          <span className="text-muted-foreground text-xl">→</span>

          <div className="text-center">
            <p className="text-3xl font-bold">{stats.filtered}</p>
            <p className="text-xs text-muted-foreground">Passed Regex</p>
          </div>

          <span className="text-muted-foreground text-xl">→</span>

          <div className="text-center">
            <p className="text-3xl font-bold">{stats.classified}</p>
            <p className="text-xs text-muted-foreground">Classified</p>
          </div>
        </div>

        {/* Filter rate summary */}
        <div className="text-center text-sm text-muted-foreground">
          {(stats.filter_rate ?? 0).toFixed(1)}% filtered out by quality pre-screening
        </div>

        {/* Expandable filter details */}
        <div>
          <button
            onClick={() => setShowFilterDetails(!showFilterDetails)}
            className="flex items-center gap-2 text-sm font-medium hover:text-primary transition-colors w-full"
          >
            {showFilterDetails ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
            Filter Breakdown
          </button>

          {showFilterDetails && (
            <div className="mt-3 space-y-2 text-sm">
              <p className="text-muted-foreground">
                Posts filtered: {(stats.scraped || 0) - (stats.filtered || 0)} ({(stats.filter_rate ?? 0).toFixed(1)}%)
              </p>
              <p className="text-muted-foreground">
                Regex pre-filter identified low-quality content (short posts, spam patterns, irrelevant topics)
              </p>
            </div>
          )}
        </div>

        {/* Archetype grouped sections */}
        <div>
          <p className="text-sm font-medium mb-3">Posts by Archetype</p>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary" className="px-3 py-1.5">
              Journey Posts ({stats.by_archetype.Journey})
            </Badge>
            <Badge variant="secondary" className="px-3 py-1.5">
              Problem-Solution Posts ({stats.by_archetype.ProblemSolution})
            </Badge>
            <Badge variant="secondary" className="px-3 py-1.5">
              Feedback Posts ({stats.by_archetype.Feedback})
            </Badge>
          </div>
        </div>

        {/* Subreddit distribution */}
        {Object.keys(stats.by_subreddit).length > 0 && (
          <div>
            <p className="text-sm font-medium mb-3">Posts by Subreddit</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
              {Object.entries(stats.by_subreddit).map(([subreddit, count]) => (
                <div key={subreddit} className="flex justify-between items-center">
                  <span className="text-muted-foreground">r/{subreddit}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
