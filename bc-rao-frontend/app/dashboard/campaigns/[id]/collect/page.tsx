"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import ProgressTracker from "@/components/collection/ProgressTracker";
import { createClient } from "@/lib/supabase/client";

type Phase = "idle" | "collecting" | "complete";

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
}

export default function CollectPage() {
  const params = useParams();
  const router = useRouter();
  const campaignId = params?.id as string;

  const [phase, setPhase] = useState<Phase>("idle");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [result, setResult] = useState<CollectionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);

  // Fetch campaign details on mount
  useEffect(() => {
    async function fetchCampaign() {
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();

        if (!session) {
          router.push("/login");
          return;
        }

        const response = await fetch(`/api/campaigns/${campaignId}`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to load campaign");
        }

        const data = await response.json();
        setCampaign({
          id: data.id,
          name: data.name,
          target_subreddits: data.target_subreddits || [],
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load campaign");
      } finally {
        setLoading(false);
      }
    }

    fetchCampaign();
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
  function handleComplete(collectionResult: CollectionResult) {
    setResult(collectionResult);
    setPhase("complete");
  }

  // Restart collection
  function restartCollection() {
    setPhase("idle");
    setTaskId(null);
    setResult(null);
    setError(null);
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

      {/* COMPLETE PHASE */}
      {phase === "complete" && result && (
        <div className="grid gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Collection Complete</CardTitle>
              <CardDescription>Your data has been collected and classified</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Final Stats */}
              <div className="rounded-lg border bg-card p-4">
                <div className="flex items-center justify-center gap-3 text-sm">
                  <div className="text-center">
                    <p className="text-3xl font-bold">{result.scraped}</p>
                    <p className="text-xs text-muted-foreground">Scraped</p>
                  </div>

                  <span className="text-muted-foreground">→</span>

                  <div className="text-center">
                    <p className="text-3xl font-bold">{result.filtered}</p>
                    <p className="text-xs text-muted-foreground">Passed Regex</p>
                  </div>

                  <span className="text-muted-foreground">→</span>

                  <div className="text-center">
                    <p className="text-3xl font-bold">{result.classified}</p>
                    <p className="text-xs text-muted-foreground">Classified</p>
                  </div>
                </div>
              </div>

              {/* Partial Failure Warning */}
              {result.errors.length > 0 && (
                <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
                  <p className="text-sm font-medium text-yellow-800">Partial Collection</p>
                  <p className="text-sm text-yellow-700 mt-1">
                    Failed to collect from: {result.errors.join(", ")}. You can try again with Collect More.
                  </p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-2">
                <Button
                  onClick={() => router.push(`/dashboard/campaigns/${campaignId}/browse`)}
                  className="flex-1"
                >
                  View Results
                </Button>
                <Button
                  onClick={restartCollection}
                  variant="outline"
                  className="flex-1"
                >
                  Collect More (4 remaining)
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
