"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import GenerationForm from "@/components/drafts/GenerationForm";
import { createClient } from "@/lib/supabase/client";
import { getSSEUrl } from "@/lib/sse";

interface Campaign {
  id: string;
  name: string;
  target_subreddits: string[];
}

interface CommunityProfile {
  subreddit: string;
  isc_score: number;
  isc_tier: string;
}

interface ProgressData {
  status: string;
  currentPhase?: string;
  draftId?: string;
}

type Phase = "idle" | "generating" | "complete" | "error";

export default function NewDraftPage() {
  const params = useParams();
  const router = useRouter();
  const campaignId = params?.id as string;

  const [phase, setPhase] = useState<Phase>("idle");
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [iscData, setIscData] = useState<Record<string, { score: number; tier: string }>>({});
  const [taskId, setTaskId] = useState<string | null>(null);
  const [progress, setProgress] = useState<ProgressData>({ status: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [draftUsage, setDraftUsage] = useState<{ used: number; limit: number } | null>(null);

  // Load campaign and community profiles
  useEffect(() => {
    async function loadData() {
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();

        if (!session) {
          router.push("/login");
          return;
        }

        // Fetch campaign
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

        // Fetch community profiles
        const profilesResponse = await fetch(`/api/campaigns/${campaignId}/community-profiles`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        if (profilesResponse.ok) {
          const responseData = await profilesResponse.json();
          const profilesData: CommunityProfile[] = Array.isArray(responseData)
            ? responseData
            : responseData.profiles || [];

          // Convert to lookup object
          const iscLookup: Record<string, { score: number; tier: string }> = {};
          profilesData.forEach((profile) => {
            iscLookup[profile.subreddit] = {
              score: profile.isc_score,
              tier: profile.isc_tier,
            };
          });
          setIscData(iscLookup);
        }

        // Fetch draft usage for current month
        const draftsResponse = await fetch(`/api/campaigns/${campaignId}/drafts?limit=1`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });
        if (draftsResponse.ok) {
          const draftsData = await draftsResponse.json();
          setDraftUsage({ used: draftsData.total ?? 0, limit: 10 }); // trial = 10
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [campaignId, router]);

  // Handle form submission
  async function handleSubmit(data: { subreddit: string; archetype: string; context?: string }) {
    setError(null);
    setPhase("generating");

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push("/login");
        return;
      }

      // Trigger generation
      const response = await fetch(`/api/campaigns/${campaignId}/drafts/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          subreddit: data.subreddit,
          archetype: data.archetype,
          context: data.context || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || "Failed to start generation");
      }

      const result = await response.json();
      setTaskId(result.task_id);

      // Open SSE stream for progress
      const eventSource = new EventSource(
        getSSEUrl(`/campaigns/${campaignId}/drafts/generate/stream/${result.task_id}`)
      );

      // Backend sends named SSE events (event: progress, success, error, done)
      // Must use addEventListener — onmessage only handles unnamed events
      eventSource.addEventListener("started", () => {
        setProgress({ status: "Starting generation..." });
      });

      eventSource.addEventListener("progress", ((event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          setProgress({
            status: data.message || "Processing...",
            currentPhase: data.phase,
          });
        } catch (err) {
          console.error("Failed to parse SSE progress:", err);
        }
      }) as EventListener);

      eventSource.addEventListener("success", ((event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          const draftId = data.draft?.id;
          setProgress({
            status: "Complete",
            draftId,
          });
          setPhase("complete");
          eventSource.close();

          // Redirect to draft editor after short delay
          if (draftId) {
            setTimeout(() => {
              router.push(`/dashboard/campaigns/${campaignId}/drafts/${draftId}/edit`);
            }, 1500);
          }
        } catch (err) {
          console.error("Failed to parse SSE success:", err);
        }
      }) as EventListener);

      eventSource.addEventListener("error", ((event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          setError(data.message || "Generation failed");
          setPhase("error");
          eventSource.close();
        } catch {
          // SSE connection error (not a named event from backend)
          // Only treat as connection lost if we haven't completed
          if (phase !== "complete") {
            setError("Connection lost. Please try again.");
            setPhase("error");
            eventSource.close();
          }
        }
      }) as EventListener);

      eventSource.addEventListener("done", () => {
        eventSource.close();
      });

      // Cleanup on unmount
      return () => {
        eventSource.close();
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate draft");
      setPhase("error");
    }
  }

  if (loading) {
    return (
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-64 bg-muted rounded"></div>
          <div className="h-96 bg-muted rounded"></div>
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
        <h2 className="text-3xl font-bold tracking-tight">Generate Draft</h2>
        <p className="text-muted-foreground">{campaign.name}</p>
      </div>

      {/* Draft Usage Indicator */}
      {draftUsage && (
        <div className={`rounded-lg border p-3 flex items-center justify-between ${
          draftUsage.used >= draftUsage.limit
            ? "border-red-300 bg-red-50 dark:bg-red-950/30 dark:border-red-800"
            : draftUsage.used >= draftUsage.limit * 0.8
              ? "border-yellow-300 bg-yellow-50 dark:bg-yellow-950/30 dark:border-yellow-800"
              : "border-border bg-muted/50"
        }`}>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">
              {draftUsage.used >= draftUsage.limit
                ? "Monthly limit reached"
                : "Monthly usage"}
            </span>
            <span className={`text-sm ${
              draftUsage.used >= draftUsage.limit ? "text-red-600 dark:text-red-400 font-semibold" : "text-muted-foreground"
            }`}>
              {draftUsage.used} / {draftUsage.limit} drafts
            </span>
          </div>
          <span className="text-xs text-muted-foreground">Trial plan</span>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm font-medium text-red-800">Error</p>
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* IDLE PHASE - Form */}
      {phase === "idle" && (
        <Card>
          <CardHeader>
            <CardTitle>Create New Draft</CardTitle>
            <CardDescription>
              Select your target subreddit, choose an archetype, and provide any additional context.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <GenerationForm
              campaignSubreddits={campaign.target_subreddits}
              iscData={iscData}
              onSubmit={handleSubmit}
              isGenerating={false}
            />
          </CardContent>
        </Card>
      )}

      {/* GENERATING PHASE - Progress */}
      {phase === "generating" && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Generation in progress
              <span className="flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
              </span>
            </CardTitle>
            <CardDescription>
              Please keep this page open while we generate your draft
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">{progress.status}</p>
              <Progress value={undefined} className="h-2" />
            </div>
            {progress.currentPhase && (
              <p className="text-xs text-muted-foreground">
                Current phase: {progress.currentPhase}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* COMPLETE PHASE - Success */}
      {phase === "complete" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-green-600">Generation Complete!</CardTitle>
            <CardDescription>Redirecting to draft editor...</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg border border-green-200 bg-green-50 p-4">
              <p className="text-sm font-medium text-green-800">Success</p>
              <p className="text-sm text-green-700">Your draft has been generated and is ready for review.</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
