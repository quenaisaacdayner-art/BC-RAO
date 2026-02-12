"use client";

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import DraftEditor from "@/components/drafts/DraftEditor";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { getSSEUrl } from "@/lib/sse";

interface Draft {
  id: string;
  campaign_id: string;
  body: string;
  vulnerability_score: number;
  rhythm_match_score: number;
  subreddit: string;
  archetype: string;
  status: string;
  created_at: string;
}

export default function DraftEditPage({
  params,
}: {
  params: Promise<{ id: string; draftId: string }>;
}) {
  const resolvedParams = use(params);
  const router = useRouter();
  const supabase = createClient();

  const [draft, setDraft] = useState<Draft | null>(null);
  const [editedBody, setEditedBody] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDraft();
  }, [resolvedParams.draftId]);

  const loadDraft = async () => {
    try {
      setIsLoading(true);
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        router.push("/login");
        return;
      }

      const response = await fetch(`/api/drafts/${resolvedParams.draftId}`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to load draft");
      }

      const data = await response.json();
      setDraft(data);
      setEditedBody(data.body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load draft");
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async () => {
    try {
      setIsProcessing(true);
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        router.push("/login");
        return;
      }

      const response = await fetch(`/api/drafts/${resolvedParams.draftId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          status: "approved",
          body: editedBody,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to approve draft");
      }

      // Redirect back to campaign page
      router.push(`/dashboard/campaigns/${resolvedParams.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve draft");
      setIsProcessing(false);
    }
  };

  const handleDiscard = async () => {
    try {
      setIsProcessing(true);
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        router.push("/login");
        return;
      }

      const response = await fetch(`/api/drafts/${resolvedParams.draftId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to discard draft");
      }

      // Redirect back to campaign page
      router.push(`/dashboard/campaigns/${resolvedParams.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to discard draft");
      setIsProcessing(false);
    }
  };

  const handleRegenerate = async (feedback: string) => {
    try {
      setIsProcessing(true);
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        router.push("/login");
        return;
      }

      // Trigger regeneration
      const response = await fetch(
        `/api/drafts/${resolvedParams.draftId}/regenerate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({ feedback }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to trigger regeneration");
      }

      const { task_id } = await response.json();

      // Set up SSE for progress tracking
      const eventSource = new EventSource(
        getSSEUrl(`/campaigns/${resolvedParams.id}/drafts/generate/stream/${task_id}`)
      );

      eventSource.addEventListener("progress", (event) => {
        const data = JSON.parse(event.data);
        console.log("Progress:", data.status);
      });

      eventSource.addEventListener("complete", (event) => {
        const data = JSON.parse(event.data);
        eventSource.close();
        // Redirect to the new draft
        router.push(
          `/dashboard/campaigns/${resolvedParams.id}/drafts/${data.draft_id}/edit`
        );
      });

      // Only handle server-sent "error" events (MessageEvent with data),
      // NOT native connection errors (plain Event) — those go to onerror for retry
      eventSource.addEventListener("error", ((event: Event) => {
        if (event instanceof MessageEvent && event.data) {
          try {
            const data = JSON.parse(event.data);
            eventSource.close();
            setError(data.error || "Regeneration failed");
            setIsProcessing(false);
          } catch {
            // Ignore parse errors
          }
        }
      }) as EventListener);

      eventSource.onerror = () => {
        eventSource.close();
        setError("Connection lost during regeneration");
        setIsProcessing(false);
      };
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to start regeneration"
      );
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="container py-8">
        <div className="text-center">Loading draft...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container py-8">
        <div className="text-center text-destructive">{error}</div>
        <div className="text-center mt-4">
          <Button asChild>
            <Link href={`/dashboard/campaigns/${resolvedParams.id}`}>
              Back to Campaign
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  if (!draft) {
    return (
      <div className="container py-8">
        <div className="text-center">Draft not found</div>
      </div>
    );
  }

  return (
    <div className="container py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link
            href={`/dashboard/campaigns/${resolvedParams.id}`}
            className="gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Campaign
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Edit Draft</h1>
          <p className="text-muted-foreground text-sm">
            Review and refine your generated content
          </p>
        </div>
      </div>

      {/* Editor */}
      <DraftEditor
        draft={draft}
        isProcessing={isProcessing}
        onApprove={handleApprove}
        onDiscard={handleDiscard}
        onRegenerate={handleRegenerate}
        onTextChange={setEditedBody}
      />
    </div>
  );
}
