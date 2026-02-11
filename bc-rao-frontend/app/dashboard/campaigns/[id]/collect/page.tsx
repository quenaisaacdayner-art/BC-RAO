"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import ProgressTracker from "@/components/collection/ProgressTracker";
import AnalysisProgress from "@/components/analysis/AnalysisProgress";
import FunnelStats from "@/components/collection/FunnelStats";
import PostFilters from "@/components/collection/PostFilters";
import PostGrid from "@/components/collection/PostGrid";
import PostDetailModal from "@/components/collection/PostDetailModal";
import { createClient } from "@/lib/supabase/client";

type Phase = "idle" | "collecting" | "analyzing" | "complete" | "results";

interface Campaign {
  id: string;
  name: string;
  target_subreddits: string[];
}

interface CollectionResult {
  scraped: number;
  filtered: number;
  classified: number;
  errors: string[];
  analysis_task_id?: string | null;
}

interface CollectionStats {
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
}

interface Post {
  id: string;
  title: string;
  raw_text: string;
  subreddit: string;
  archetype: "Journey" | "ProblemSolution" | "Feedback";
  success_score: number;
  author?: string;
  reddit_created_at?: string;
  upvote_ratio?: number;
  comment_count?: number;
}

export default function CollectPage() {
  const params = useParams();
  const router = useRouter();
  const campaignId = params?.id as string;

  const [phase, setPhase] = useState<Phase>("idle");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [result, setResult] = useState<CollectionResult | null>(null);
  const [stats, setStats] = useState<CollectionStats | null>(null);
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [filters, setFilters] = useState({
    archetype: null as string | null,
    subreddit: null as string | null,
    minScore: 0,
    maxScore: 10,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);
  const [analysisTaskId, setAnalysisTaskId] = useState<string | null>(null);

  // Fetch campaign details and check for existing posts on mount
  useEffect(() => {
    async function fetchCampaignAndStats() {
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();

        if (!session) {
          router.push("/login");
          return;
        }

        // Fetch campaign details
        const campaignResponse = await fetch(`/api/campaigns/${campaignId}`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        if (!campaignResponse.ok) {
          throw new Error("Failed to load campaign");
        }

        const campaignData = await campaignResponse.json();
        setCampaign({
          id: campaignData.id,
          name: campaignData.name,
          target_subreddits: campaignData.target_subreddits || [],
        });

        // Check if posts already exist for this campaign
        const statsResponse = await fetch(`/api/campaigns/${campaignId}/collection-stats`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          const total = statsData.total || 0;

          // If we have collected posts, show results view
          if (total > 0) {
            setStats({
              scraped: 0,
              filtered: 0,
              classified: total,
              filter_rate: 0,
              by_archetype: {
                Journey: statsData.by_archetype?.Journey || 0,
                ProblemSolution: statsData.by_archetype?.ProblemSolution || 0,
                Feedback: statsData.by_archetype?.Feedback || 0,
              },
              by_subreddit: statsData.by_subreddit || {},
            });
            setPhase("results");
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load campaign");
      } finally {
        setLoading(false);
      }
    }

    fetchCampaignAndStats();
  }, [campaignId, router]);

  // Navigation guard during collection
  useEffect(() => {
    if (phase !== "collecting") return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "Collection in progress, are you sure you want to leave?";
      return e.returnValue;
    };

    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [phase]);

  // Trigger collection
  async function startCollection() {
    setTriggering(true);
    setError(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push("/login");
        return;
      }

      const response = await fetch(`/api/campaigns/${campaignId}/collect`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error?.message || "Failed to start collection");
      }

      const data = await response.json();
      setTaskId(data.task_id);
      setPhase("collecting");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start collection");
    } finally {
      setTriggering(false);
    }
  }

  // Handle collection completion
  async function handleComplete(collectionResult: CollectionResult) {
    setResult(collectionResult);

    // Build stats by combining SSE result (scraped/filtered/classified) with backend stats (by_archetype/by_subreddit)
    const filter_rate = collectionResult.scraped > 0
      ? ((collectionResult.scraped - collectionResult.filtered) / collectionResult.scraped) * 100
      : 0;

    // Default stats from SSE result
    let mergedStats: CollectionStats = {
      scraped: collectionResult.scraped,
      filtered: collectionResult.filtered,
      classified: collectionResult.classified,
      filter_rate,
      by_archetype: { Journey: 0, ProblemSolution: 0, Feedback: 0 },
      by_subreddit: {},
    };

    // Fetch archetype/subreddit breakdown from backend
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (session) {
        const statsResponse = await fetch(`/api/campaigns/${campaignId}/collection-stats`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          mergedStats.by_archetype = {
            Journey: statsData.by_archetype?.Journey || 0,
            ProblemSolution: statsData.by_archetype?.ProblemSolution || 0,
            Feedback: statsData.by_archetype?.Feedback || 0,
          };
          mergedStats.by_subreddit = statsData.by_subreddit || {};
        }
      }
    } catch (err) {
      console.error("Failed to fetch stats:", err);
    }

    setStats(mergedStats);

    // Auto-trigger analysis if backend started it
    if (collectionResult.analysis_task_id) {
      setAnalysisTaskId(collectionResult.analysis_task_id);
      setPhase("analyzing");
    } else {
      setPhase("results");
    }
  }

  // Restart collection (for "Collect More")
  async function collectMore() {
    setPhase("idle");
    setTaskId(null);
    setResult(null);
    setError(null);
    // Trigger collection immediately
    await startCollection();
  }

  if (loading) {
    return (
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-64 bg-muted rounded"></div>
          <div className="h-32 bg-muted rounded"></div>
        </div>
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Campaign not found</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
      {/* Page Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Collect Data</h2>
        <p className="text-muted-foreground">{campaign.name}</p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm font-medium text-red-800">Error</p>
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* IDLE PHASE */}
      {phase === "idle" && (
        <div className="grid gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Ready to Collect</CardTitle>
              <CardDescription>
                We'll scrape your target subreddits, filter for quality posts, and classify the top results into archetypes.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Target Subreddits */}
              <div>
                <p className="text-sm font-medium mb-2">Target Subreddits ({campaign.target_subreddits.length})</p>
                <div className="flex flex-wrap gap-2">
                  {campaign.target_subreddits.map((subreddit) => (
                    <Badge key={subreddit} variant="secondary">
                      r/{subreddit}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Start Button */}
              <Button
                onClick={startCollection}
                disabled={triggering}
                size="lg"
                className="w-full"
              >
                {triggering ? "Starting..." : "Start Collection (5 remaining)"}
              </Button>

              <p className="text-xs text-muted-foreground text-center">
                Collection typically takes 2-5 minutes depending on subreddit size
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* COLLECTING PHASE */}
      {phase === "collecting" && taskId && (
        <div className="grid gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Collection in progress
                <span className="flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                </span>
              </CardTitle>
              <CardDescription>
                Please keep this page open while we collect and analyze your data
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ProgressTracker taskId={taskId} onComplete={handleComplete} />
            </CardContent>
          </Card>
        </div>
      )}

      {/* ANALYZING PHASE */}
      {phase === "analyzing" && analysisTaskId && (
        <div className="grid gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                Analysis in progress
                <span className="flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
              </CardTitle>
              <CardDescription>
                Building community profiles from collected posts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <AnalysisProgress
                campaignId={campaignId}
                taskId={analysisTaskId}
                onComplete={() => setPhase("results")}
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* RESULTS PHASE */}
      {phase === "results" && stats && campaign && (
        <div className="space-y-4">
          {/* Collect More Button */}
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-semibold">Collected Posts</h3>
              <p className="text-sm text-muted-foreground">
                Browse and filter your collected posts
              </p>
            </div>
            <Button onClick={collectMore} variant="outline">
              Collect More (4 remaining)
            </Button>
          </div>

          {/* Partial Failure Warning */}
          {result?.errors && result.errors.length > 0 && (
            <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
              <p className="text-sm font-medium text-yellow-800">Partial Collection</p>
              <p className="text-sm text-yellow-700 mt-1">
                Failed to collect from: {result.errors.join(", ")}. You can try again with Collect More.
              </p>
            </div>
          )}

          {/* Funnel Stats */}
          <FunnelStats stats={stats} />

          {/* Filters */}
          <PostFilters
            subreddits={campaign.target_subreddits}
            onFiltersChange={setFilters}
          />

          {/* Post Grid */}
          <PostGrid
            campaignId={campaignId}
            filters={filters}
            onPostClick={setSelectedPost}
          />

          {/* Post Detail Modal */}
          <PostDetailModal
            post={selectedPost}
            open={!!selectedPost}
            onClose={() => setSelectedPost(null)}
          />
        </div>
      )}
    </div>
  );
}
