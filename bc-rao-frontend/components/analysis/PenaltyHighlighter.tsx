"use client";

import Highlighter from "react-highlight-words";

interface Penalty {
  phrase: string;
  severity: "high" | "medium" | "low";
  category: string;
}

interface PenaltyHighlighterProps {
  text: string;
  penalties: Penalty[];
}

const SEVERITY_STYLES = {
  high: "bg-red-100 text-red-900 border-b-2 border-red-500 rounded-sm px-0.5",
  medium: "bg-orange-100 text-orange-900 border-b-2 border-orange-500 rounded-sm px-0.5",
  low: "bg-yellow-100 text-yellow-900 border-b-2 border-yellow-500 rounded-sm px-0.5",
};

export default function PenaltyHighlighter({ text, penalties }: PenaltyHighlighterProps) {
  const safeText = text || "";

  // If no penalties, render plain text
  if (!penalties || penalties.length === 0) {
    return <p className="text-gray-700 whitespace-pre-wrap">{safeText}</p>;
  }

  // Extract search words from penalties
  const searchWords = penalties.map(p => p.phrase);

  // Create a mapping from phrase to penalty for tooltip/styling
  const penaltyMap = new Map<string, Penalty>();
  penalties.forEach(p => penaltyMap.set(p.phrase.toLowerCase(), p));

  return (
    <div className="text-gray-700 whitespace-pre-wrap">
      <Highlighter
        searchWords={searchWords}
        autoEscape={true}
        textToHighlight={safeText}
        highlightClassName=""
        unhighlightClassName=""
        highlightTag={({ children, highlightIndex }) => {
          // Find matching penalty by comparing children text
          const matchedText = String(children).toLowerCase();
          const penalty = Array.from(penaltyMap.values()).find(p =>
            matchedText.includes(p.phrase.toLowerCase())
          );

          if (!penalty) {
            return <span>{children}</span>;
          }

          const severityClass = SEVERITY_STYLES[penalty.severity];

          return (
            <span
              className={severityClass}
              title={`${penalty.category} (${penalty.severity} severity)`}
            >
              {children}
            </span>
          );
        }}
      />
    </div>
  );
}
