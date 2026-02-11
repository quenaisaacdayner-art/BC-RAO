"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Check, Trash2, RefreshCw } from "lucide-react";
import CopyButton from "./CopyButton";

interface DraftActionsProps {
  draftText: string;
  isProcessing: boolean;
  onApprove: () => void;
  onDiscard: () => void;
  onRegenerate: (feedback: string) => void;
}

export default function DraftActions({
  draftText,
  isProcessing,
  onApprove,
  onDiscard,
  onRegenerate,
}: DraftActionsProps) {
  const [showRegenerateFeedback, setShowRegenerateFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");

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

  return (
    <Card className="p-6 space-y-4">
      <h3 className="font-semibold text-sm">Actions</h3>

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
