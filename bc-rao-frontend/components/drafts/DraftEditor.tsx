"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import ScoreSidebar from "./ScoreSidebar";
import DraftActions from "./DraftActions";

interface Draft {
  id: string;
  body: string;
  vulnerability_score: number;
  rhythm_match_score: number;
  target_subreddit: string;
  archetype: string;
  created_at: string;
}

interface DraftEditorProps {
  draft: Draft;
  isProcessing: boolean;
  onApprove: () => void;
  onDiscard: () => void;
  onRegenerate: (feedback: string) => void;
  onTextChange: (text: string) => void;
}

export default function DraftEditor({
  draft,
  isProcessing,
  onApprove,
  onDiscard,
  onRegenerate,
  onTextChange,
}: DraftEditorProps) {
  const [editedBody, setEditedBody] = useState(draft.body);

  const handleTextChange = (value: string) => {
    setEditedBody(value);
    onTextChange(value);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
      {/* Left: Draft Text Editor */}
      <div className="space-y-4">
        <Card className="p-6">
          <div className="space-y-2">
            <label htmlFor="draft-text" className="text-sm font-semibold">
              Draft Text
            </label>
            <Textarea
              id="draft-text"
              value={editedBody}
              onChange={(e) => handleTextChange(e.target.value)}
              disabled={isProcessing}
              className="min-h-[500px] font-mono text-sm leading-relaxed resize-none"
              placeholder="Your draft text will appear here..."
            />
            <p className="text-xs text-muted-foreground">
              Character count: {editedBody.length}
            </p>
          </div>
        </Card>
      </div>

      {/* Right: Scores and Actions */}
      <div className="space-y-4">
        <ScoreSidebar
          vulnerabilityScore={draft.vulnerability_score}
          rhythmMatchScore={draft.rhythm_match_score}
          metadata={{
            subreddit: draft.target_subreddit,
            archetype: draft.archetype,
            generatedAt: draft.created_at,
          }}
        />

        <DraftActions
          draftText={editedBody}
          isProcessing={isProcessing}
          onApprove={onApprove}
          onDiscard={onDiscard}
          onRegenerate={onRegenerate}
        />
      </div>
    </div>
  );
}
