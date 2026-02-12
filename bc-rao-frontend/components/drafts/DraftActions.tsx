"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Check, Trash2, RefreshCw, ExternalLink, Rocket } from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";
import CopyButton from "./CopyButton";
import { createClient } from "@/lib/supabase/client";

interface DraftActionsProps {
  draftText: string;
  draftStatus: string;
  campaignId: string;
  isProcessing: boolean;
  onApprove: () => void;
  onDiscard: () => void;
  onRegenerate: (feedback: string) => void;
}

export default function DraftActions({
  draftText,
  draftStatus,
  campaignId,
  isProcessing,
  onApprove,
  onDiscard,
  onRegenerate,
}: DraftActionsProps) {
  const [showRegenerateFeedback, setShowRegenerateFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [showPostUrlInput, setShowPostUrlInput] = useState(false);
  const [postUrl, setPostUrl] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);

  const handleRegenerate = () => {
    if (showRegenerateFeedback) {
      onRegenerate(feedback);
      setFeedback("");
      setShowRegenerateFeedback(false);
    } else {
      setShowRegenerateFeedback(true);
    }
  };

  const handleCancelRegenerate = () => {
    setShowRegenerateFeedback(false);
    setFeedback("");
  };

  const handlePostUrlSubmit = async () => {
    // Validate Reddit URL format
    const redditUrlRegex = /^https?:\/\/(www\.)?(reddit\.com|redd\.it)\/(r\/[^\/]+\/comments\/[^\/]+|comments\/[^\/]+)/i;

    if (!postUrl.trim()) {
      toast.error("Please enter a Reddit URL");
      return;
    }

    if (!redditUrlRegex.test(postUrl.trim())) {
      toast.error("Invalid Reddit URL format", {
        description: "Please enter a valid Reddit post URL (e.g., https://reddit.com/r/subreddit/comments/...)",
      });
      return;
    }

    try {
      setIsRegistering(true);

      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session?.access_token) {
        toast.error("Session expired. Please log in again.");
        return;
      }

      // POST to monitoring API
      const response = await fetch("/api/monitoring", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          post_url: postUrl.trim(),
          campaign_id: campaignId,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "Failed to register post");
      }

      // Success
      toast.success("Post registered! Monitoring has started.", {
        description: "View monitoring dashboard to track performance",
        action: {
          label: "View Monitoring",
          onClick: () => {
            window.location.href = `/dashboard/campaigns/${campaignId}/monitoring`;
          },
        },
        duration: 5000,
      });

      // Reset form
      setPostUrl("");
      setShowPostUrlInput(false);
    } catch (error) {
      toast.error("Failed to register post", {
        description: error instanceof Error ? error.message : "An error occurred",
      });
    } finally {
      setIsRegistering(false);
    }
  };

  const showIPostedThisButton = draftStatus === "approved" || draftStatus === "posted";

  return (
    <Card className="p-6 space-y-4">
      <h3 className="font-semibold text-sm">Actions</h3>

      {/* "I Posted This" Section - Only show for approved/posted drafts */}
      {showIPostedThisButton && (
        <div className="space-y-3 pb-4 border-b">
          {draftStatus === "posted" ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <Rocket className="h-4 w-4 text-green-600" />
                <span className="text-sm font-semibold text-green-800">Monitoring Active</span>
              </div>
              <Link
                href={`/dashboard/campaigns/${campaignId}/monitoring`}
                className="text-xs text-green-700 hover:underline flex items-center gap-1"
              >
                View monitoring dashboard
                <ExternalLink className="h-3 w-3" />
              </Link>
            </div>
          ) : (
            <>
              {!showPostUrlInput ? (
                <Button
                  variant="outline"
                  onClick={() => setShowPostUrlInput(true)}
                  disabled={isProcessing || isRegistering}
                  className="w-full gap-2"
                >
                  <Rocket className="h-4 w-4" />
                  I Posted This
                </Button>
              ) : (
                <div className="space-y-2 bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <Label htmlFor="post-url" className="text-sm font-semibold">
                    Reddit Post URL
                  </Label>
                  <Input
                    id="post-url"
                    type="url"
                    placeholder="https://reddit.com/r/subreddit/comments/..."
                    value={postUrl}
                    onChange={(e) => setPostUrl(e.target.value)}
                    disabled={isRegistering}
                    className="text-sm"
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setShowPostUrlInput(false);
                        setPostUrl("");
                      }}
                      disabled={isRegistering}
                    >
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      onClick={handlePostUrlSubmit}
                      disabled={isRegistering || !postUrl.trim()}
                      className="gap-1"
                    >
                      {isRegistering ? "Registering..." : "Start Monitoring"}
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Regenerate Feedback Section */}
      {showRegenerateFeedback && (
        <div className="space-y-2">
          <Label htmlFor="feedback" className="text-sm">
            Regeneration Feedback (Optional)
          </Label>
          <Textarea
            id="feedback"
            placeholder="What should be different in the new draft?"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            rows={4}
            disabled={isProcessing}
          />
          <p className="text-xs text-muted-foreground">
            Provide guidance for the regeneration. Leave blank to try a different variation.
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="space-y-2">
        <Button
          onClick={onApprove}
          disabled={isProcessing}
          className="w-full gap-2"
        >
          <Check className="h-4 w-4" />
          Approve Draft
        </Button>

        <CopyButton text={draftText} disabled={isProcessing} />

        {showRegenerateFeedback ? (
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              onClick={handleCancelRegenerate}
              disabled={isProcessing}
            >
              Cancel
            </Button>
            <Button
              variant="default"
              onClick={handleRegenerate}
              disabled={isProcessing}
              className="gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Generate
            </Button>
          </div>
        ) : (
          <Button
            variant="outline"
            onClick={handleRegenerate}
            disabled={isProcessing}
            className="w-full gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Regenerate
          </Button>
        )}

        <Button
          variant="destructive"
          onClick={onDiscard}
          disabled={isProcessing}
          className="w-full gap-2"
        >
          <Trash2 className="h-4 w-4" />
          Discard Draft
        </Button>
      </div>
    </Card>
  );
}
