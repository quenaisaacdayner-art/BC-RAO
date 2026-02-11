"use client";

import { useEffect, useState } from "react";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import Link from "next/link";

interface ProgressData {
  current: number;
  total: number;
  currentStep: string;
  currentSubreddit?: string;
  warnings: Array<{ subreddit: string; reason: string }>;
}

interface AnalysisProgressProps {
  campaignId: string;
  taskId: string;
  onComplete: () => void;
}

export default function AnalysisProgress({ campaignId, taskId, onComplete }: AnalysisProgressProps) {
  const [progress, setProgress] = useState<ProgressData>({
    current: 0,
    total: 0,
    currentStep: "",
    currentSubreddit: undefined,
    warnings: [],
  });
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const eventSource = new EventSource(`/api/analysis/${taskId}/progress`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.state === "PROGRESS") {
          // Update progress from meta field
          const meta = data.meta || {};
          setProgress({
            current: meta.current || 0,
            total: meta.total || 0,
            currentStep: meta.step || "",
            currentSubreddit: meta.current_subreddit || undefined,
            warnings: meta.warnings || [],
          });
        } else if (data.state === "SUCCESS") {
          // Analysis complete
          setIsComplete(true);

          // Show toast notification with link
          toast.success("Analysis complete", {
            description: "Community profiles are ready to view",
            action: {
              label: "View Profiles",
              onClick: () => {
                window.location.href = `/dashboard/campaigns/${campaignId}/profiles`;
              },
            },
            duration: 10000,
          });

          onComplete();
          eventSource.close();
        } else if (data.state === "FAILURE" || data.error) {
          // Analysis failed
          setError(data.error || "Analysis failed");
          toast.error("Analysis failed", {
            description: data.error || "An error occurred during analysis",
          });
          eventSource.close();
        }
      } catch (err) {
        console.error("Failed to parse SSE message:", err);
      }
    };

    eventSource.onerror = () => {
      setError("Connection lost. Please refresh the page.");
      toast.error("Connection lost", {
        description: "Please refresh the page to reconnect",
      });
      eventSource.close();
    };

    // Cleanup: close EventSource on unmount
    return () => {
      eventSource.close();
    };
  }, [taskId, campaignId, onComplete]);

  const progressPercent = progress.total > 0
    ? Math.round((progress.current / progress.total) * 100)
    : 0;

  // Step name mapping for better display
  const stepNames: Record<string, string> = {
    nlp_analysis: "Natural Language Processing",
    scoring: "Scoring Posts",
    profiling: "Building Profiles",
  };

  const displayStep = stepNames[progress.currentStep] || progress.currentStep;

  return (
    <div className="space-y-6">
      {/* Error State */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm font-medium text-red-800">Error</p>
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Success State */}
      {isComplete && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
          <p className="text-sm font-medium text-green-800">Analysis Complete!</p>
          <p className="text-sm text-green-700 mt-1">
            Community profiles are ready to view.
          </p>
          <Link
            href={`/dashboard/campaigns/${campaignId}/profiles`}
            className="text-sm font-medium text-green-700 underline mt-2 inline-block"
          >
            View Profiles →
          </Link>
        </div>
      )}

      {/* Progress State */}
      {!isComplete && !error && (
        <>
          {/* Current Step and Subreddit */}
          <div className="space-y-2">
            {displayStep && (
              <p className="text-sm text-muted-foreground">
                {displayStep}
                {progress.currentSubreddit && (
                  <span className="font-medium text-foreground"> - r/{progress.currentSubreddit}</span>
                )}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              Analyzing post {progress.current} of {progress.total}
            </p>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <Progress value={progressPercent} className="h-2" />
            <p className="text-sm text-muted-foreground text-right">
              {progressPercent}% complete
            </p>
          </div>

          {/* Analysis Stats */}
          <div className="rounded-lg border bg-card p-4">
            <div className="flex items-center justify-center gap-6 text-sm">
              <div className="text-center">
                <p className="text-2xl font-bold tabular-nums transition-all duration-300">
                  {progress.current}
                </p>
                <p className="text-xs text-muted-foreground">Analyzed</p>
              </div>

              <span className="text-muted-foreground">/</span>

              <div className="text-center">
                <p className="text-2xl font-bold tabular-nums transition-all duration-300">
                  {progress.total}
                </p>
                <p className="text-xs text-muted-foreground">Total</p>
              </div>
            </div>
          </div>

          {/* Insufficient Data Warnings */}
          {progress.warnings.length > 0 && (
            <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
              <p className="text-sm font-medium text-yellow-800">Insufficient Data Warnings</p>
              <div className="mt-2 space-y-1">
                {progress.warnings.map((warning, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <span className="inline-flex items-center rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800">
                      r/{warning.subreddit}
                    </span>
                    <span className="text-xs text-yellow-700">{warning.reason}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
