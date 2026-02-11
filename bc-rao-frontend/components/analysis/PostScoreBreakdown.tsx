"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import PenaltyHighlighter from "./PenaltyHighlighter";

interface PostScoreBreakdownProps {
  postId: string;
  campaignId: string;
  postText: string;
  totalScore: number;
  postTitle?: string;
}

interface ScoringBreakdown {
  rhythm_adherence: number;
  vulnerability_weight: number;
  formality_match: number;
  marketing_jargon_penalty: number;
  link_density_penalty: number;
  penalties: Array<{
    phrase: string;
    severity: "high" | "medium" | "low";
    category: string;
  }>;
}

function getScoreBadgeClass(score: number): string {
  if (score >= 7) return "bg-green-100 text-green-800 border-green-300";
  if (score >= 5) return "bg-yellow-100 text-yellow-800 border-yellow-300";
  if (score >= 3) return "bg-orange-100 text-orange-800 border-orange-300";
  return "bg-red-100 text-red-800 border-red-300";
}

export default function PostScoreBreakdown({
  postId,
  campaignId,
  postText,
  totalScore,
  postTitle,
}: PostScoreBreakdownProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [breakdown, setBreakdown] = useState<ScoringBreakdown | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleToggle = async () => {
    if (!isExpanded && !breakdown) {
      // First time expanding - fetch breakdown
      setIsLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem("supabase.auth.token");
        const response = await fetch(
          `/api/campaigns/${campaignId}/scoring-breakdown?post_id=${postId}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error("Failed to fetch scoring breakdown");
        }

        const data = await response.json();
        setBreakdown(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setIsLoading(false);
      }
    }

    setIsExpanded(!isExpanded);
  };

  const text = postText || "";
  const previewText = postTitle || text.slice(0, 100) + (text.length > 100 ? "..." : "");
  const scoreBadgeClass = getScoreBadgeClass(totalScore ?? 0);

  return (
    <div className="border border-gray-200 rounded-lg bg-white shadow-sm">
      {/* Collapsed view */}
      <button
        onClick={handleToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3 flex-1 text-left">
          <span className={`px-2 py-1 text-sm font-medium rounded border ${scoreBadgeClass}`}>
            {(totalScore ?? 0).toFixed(1)}
          </span>
          <p className="text-gray-700 text-sm line-clamp-1">{previewText}</p>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-gray-500" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-500" />
        )}
      </button>

      {/* Expanded view */}
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-gray-200">
          {isLoading && (
            <div className="py-4 text-center text-gray-500">Loading breakdown...</div>
          )}

          {error && (
            <div className="py-4 text-center text-red-600">Error: {error}</div>
          )}

          {breakdown && (
            <>
              {/* Key factors */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 mb-4">
                <div className="bg-gray-50 p-3 rounded border border-gray-200">
                  <p className="text-xs text-gray-500 mb-1">Rhythm Match</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {breakdown.rhythm_adherence.toFixed(1)}
                  </p>
                </div>
                <div className="bg-gray-50 p-3 rounded border border-gray-200">
                  <p className="text-xs text-gray-500 mb-1">Vulnerability</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {breakdown.vulnerability_weight.toFixed(1)}
                  </p>
                </div>
                <div className="bg-gray-50 p-3 rounded border border-gray-200">
                  <p className="text-xs text-gray-500 mb-1">Formality</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {breakdown.formality_match.toFixed(1)}
                  </p>
                </div>
                <div className="bg-gray-50 p-3 rounded border border-gray-200">
                  <p className="text-xs text-gray-500 mb-1">Penalties</p>
                  <p className="text-lg font-semibold text-red-600">
                    -{(breakdown.marketing_jargon_penalty + breakdown.link_density_penalty).toFixed(1)}
                  </p>
                </div>
              </div>

              {/* Full post text with penalty highlighting */}
              <div className="bg-gray-50 p-4 rounded border border-gray-200">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Post Content</h4>
                <PenaltyHighlighter text={postText} penalties={breakdown.penalties} />
              </div>

              {/* Penalty legend if penalties exist */}
              {breakdown.penalties.length > 0 && (
                <div className="mt-3 flex items-center gap-4 text-xs text-gray-600">
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-3 h-3 bg-red-100 border-b-2 border-red-500 rounded-sm"></span>
                    High
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-3 h-3 bg-orange-100 border-b-2 border-orange-500 rounded-sm"></span>
                    Medium
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="inline-block w-3 h-3 bg-yellow-100 border-b-2 border-yellow-500 rounded-sm"></span>
                    Low
                  </span>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
