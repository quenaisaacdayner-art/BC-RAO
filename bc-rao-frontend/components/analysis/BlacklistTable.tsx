"use client";

import { Lock } from "lucide-react";

interface ForbiddenPattern {
  id: string;
  pattern: string;
  category: string;
  is_system: boolean;
  subreddit?: string;
  severity?: string;
}

interface BlacklistTableProps {
  patterns: ForbiddenPattern[];
  categories: Record<string, number>;
}

const CATEGORY_COLORS: Record<string, string> = {
  Promotional: "bg-red-50 border-red-200 text-red-900",
  "Self-referential": "bg-orange-50 border-orange-200 text-orange-900",
  "Link patterns": "bg-yellow-50 border-yellow-200 text-yellow-900",
  "Low-effort": "bg-blue-50 border-blue-200 text-blue-900",
  "Spam indicators": "bg-purple-50 border-purple-200 text-purple-900",
  "Off-topic": "bg-pink-50 border-pink-200 text-pink-900",
  Custom: "bg-gray-50 border-gray-200 text-gray-900",
};

export default function BlacklistTable({ patterns, categories }: BlacklistTableProps) {
  if (patterns.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No forbidden patterns detected yet. Run analysis first.
      </div>
    );
  }

  // Group patterns by category
  const groupedPatterns = patterns.reduce((acc, pattern) => {
    const category = pattern.category || "Custom";
    if (!acc[category]) acc[category] = [];
    acc[category].push(pattern);
    return acc;
  }, {} as Record<string, ForbiddenPattern[]>);

  return (
    <div className="space-y-4">
      {/* Category summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {Object.entries(categories).map(([category, count]) => {
          const colorClass = CATEGORY_COLORS[category] || CATEGORY_COLORS.Custom;
          return (
            <div
              key={category}
              className={`p-4 rounded-lg border ${colorClass}`}
            >
              <p className="text-sm font-medium mb-1">{category}</p>
              <p className="text-2xl font-bold">{count}</p>
            </div>
          );
        })}
      </div>

      {/* Pattern details by category */}
      <div className="space-y-6 mt-6">
        {Object.entries(groupedPatterns).map(([category, categoryPatterns]) => {
          const colorClass = CATEGORY_COLORS[category] || CATEGORY_COLORS.Custom;
          return (
            <div key={category}>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">
                {category}
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({categoryPatterns.length} patterns)
                </span>
              </h3>
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        Pattern
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        Subreddit
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        Severity
                      </th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        Type
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {categoryPatterns.map((pattern) => (
                      <tr key={pattern.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-900">
                          <code className="bg-gray-100 px-2 py-1 rounded text-xs font-mono">
                            {pattern.pattern}
                          </code>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {pattern.subreddit || "All"}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {pattern.severity ? (
                            <span
                              className={`px-2 py-1 text-xs font-medium rounded ${
                                pattern.severity === "high"
                                  ? "bg-red-100 text-red-800"
                                  : pattern.severity === "medium"
                                  ? "bg-orange-100 text-orange-800"
                                  : "bg-yellow-100 text-yellow-800"
                              }`}
                            >
                              {pattern.severity}
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {pattern.is_system ? (
                            <span className="flex items-center gap-1 text-gray-500">
                              <Lock className="w-3 h-3" />
                              System
                            </span>
                          ) : (
                            <span className="text-blue-600">Custom</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
