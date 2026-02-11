"use client";

import { AlertTriangle } from "lucide-react";

interface ISCGatingWarningProps {
  subreddit: string;
  iscScore: number;
  iscTier: string;
}

/**
 * Warning banner for high ISC communities
 * Shows when ISC > 7.5 to inform user that only Feedback archetype is available
 */
export default function ISCGatingWarning({ subreddit, iscScore, iscTier }: ISCGatingWarningProps) {
  return (
    <div className="rounded-lg border border-orange-200 bg-orange-50 p-4">
      <div className="flex gap-3">
        <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <p className="text-sm font-medium text-orange-800">
            High Sensitivity Community
          </p>
          <p className="text-sm text-orange-700 mt-1">
            r/{subreddit} has ISC {iscScore.toFixed(1)}/10 ({iscTier}). Only <strong>Feedback archetype</strong> is available with zero links to reduce promotional risk.
          </p>
        </div>
      </div>
    </div>
  );
}
