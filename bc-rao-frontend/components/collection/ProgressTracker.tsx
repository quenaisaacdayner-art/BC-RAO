"use client";

import { useEffect, useState } from "react";
import { Progress } from "@/components/ui/progress";
import { getSSEUrl } from "@/lib/sse";

interface ProgressData {
  scraped: number;
  filtered: number;
  classified: number;
  currentStep: number;
  totalSteps: number;
  currentSubreddit: string;
  errors: Array<{ subreddit: string; error: string }>;
}

interface ProgressTrackerProps {
  taskId: string;
  onComplete: (result: { scraped: number; filtered: number; classified: number; errors: string[] }) => void;
}

export default function ProgressTracker({ taskId, onComplete }: ProgressTrackerProps) {
  const [progress, setProgress] = useState<ProgressData>({
    scraped: 0,
    filtered: 0,
    classified: 0,
    currentStep: 0,
    totalSteps: 0,
    currentSubreddit: "",
    errors: [],
  });
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let retryCount = 0;
    const maxRetries = 5;
    let eventSource: EventSource | null = null;
    let closed = false;

    function connect() {
      if (closed) return;
      eventSource = new EventSource(getSSEUrl(`/collection/${taskId}/progress`));

      // Handle named SSE events from backend
      const handleEvent = (event: MessageEvent) => {
        retryCount = 0;
        try {
          const data = JSON.parse(event.data);
          setProgress({
            scraped: data.scraped || 0,
            filtered: data.filtered || 0,
            classified: data.classified || 0,
            currentStep: data.current_step || 0,
            totalSteps: data.total_steps || 0,
            currentSubreddit: data.current_subreddit || "",
            errors: data.errors || [],
          });
        } catch (err) {
          console.error("Failed to parse SSE progress:", err);
        }
      };

      const handleSuccess = (event: MessageEvent) => {
        retryCount = 0;
        try {
          const data = JSON.parse(event.data);
          setIsComplete(true);
          onComplete({
            scraped: data.scraped || 0,
            filtered: data.filtered || 0,
            classified: data.classified || 0,
            errors: data.errors || [],
          });
          eventSource?.close();
          closed = true;
        } catch (err) {
          console.error("Failed to parse SSE success:", err);
        }
      };

      const handleError = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          setError(data.error || "Collection failed");
        } catch {
          setError("Collection failed");
        }
        eventSource?.close();
        closed = true;
      };

      // Backend sends named events: progress, started, pending, success, error, done
      eventSource.addEventListener("progress", handleEvent);
      eventSource.addEventListener("started", () => { retryCount = 0; });
      eventSource.addEventListener("pending", () => { retryCount = 0; });
      eventSource.addEventListener("success", handleSuccess);
      eventSource.addEventListener("error", handleError);

      // Also handle unnamed events as fallback
      eventSource.onmessage = (event) => {
        retryCount = 0;
        try {
          const data = JSON.parse(event.data);
          if (data.state === "PROGRESS") handleEvent(event);
          else if (data.state === "SUCCESS") handleSuccess(event);
          else if (data.state === "FAILURE") handleError(event);
        } catch (err) {
          console.error("Failed to parse SSE message:", err);
        }
      };

      eventSource.onerror = () => {
        eventSource?.close();
        if (closed) return;

        retryCount++;
        if (retryCount <= maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 16000);
          console.log(`SSE reconnecting in ${delay}ms (attempt ${retryCount}/${maxRetries})`);
          setTimeout(connect, delay);
        } else {
          setError("Connection lost after multiple retries. Please refresh the page.");
        }
      };
    }

    connect();

    // Cleanup: close EventSource on unmount
    return () => {
      closed = true;
      eventSource?.close();
    };
  }, [taskId, onComplete]);

  const progressPercent = progress.totalSteps > 0
    ? Math.round((progress.currentStep / progress.totalSteps) * 100)
    : 0;

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
          <p className="text-sm font-medium text-green-800">Collection Complete!</p>
          <p className="text-sm text-green-700 mt-1">
            Scraped {progress.scraped} posts → {progress.filtered} passed regex → {progress.classified} classified
          </p>
        </div>
      )}

      {/* Progress State */}
      {!isComplete && !error && (
        <>
          {/* Current Subreddit */}
          {progress.currentSubreddit && (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                Processing <span className="font-medium text-foreground">r/{progress.currentSubreddit}</span>
              </p>
            </div>
          )}

          {/* Progress Bar */}
          <div className="space-y-2">
            <Progress value={progressPercent} className="h-2" />
            <p className="text-sm text-muted-foreground text-right">
              Step {progress.currentStep} of {progress.totalSteps} subreddits
            </p>
          </div>

          {/* Funnel Stats with Animated Transitions */}
          <div className="rounded-lg border bg-card p-4">
            <div className="flex items-center justify-center gap-3 text-sm">
              <div className="text-center">
                <p className="text-2xl font-bold tabular-nums transition-all duration-300">
                  {progress.scraped}
                </p>
                <p className="text-xs text-muted-foreground">Scraped</p>
              </div>

              <span className="text-muted-foreground">→</span>

              <div className="text-center">
                <p className="text-2xl font-bold tabular-nums transition-all duration-300">
                  {progress.filtered}
                </p>
                <p className="text-xs text-muted-foreground">Filtered</p>
              </div>

              <span className="text-muted-foreground">→</span>

              <div className="text-center">
                <p className="text-2xl font-bold tabular-nums transition-all duration-300">
                  {progress.classified}
                </p>
                <p className="text-xs text-muted-foreground">Classified</p>
              </div>
            </div>
          </div>

          {/* Partial Errors */}
          {progress.errors.length > 0 && (
            <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
              <p className="text-sm font-medium text-yellow-800">Some subreddits had issues</p>
              <p className="text-xs text-yellow-700 mt-1">
                {progress.errors.length} subreddit{progress.errors.length > 1 ? "s" : ""} failed.
                You can retry after collection completes.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
