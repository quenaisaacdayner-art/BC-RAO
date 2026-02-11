"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ArrowUpDown } from "lucide-react";

interface CommunityProfile {
  id: string;
  subreddit: string;
  isc_score: number;
  isc_tier: string;
  dominant_tone: string | null;
  formality_level: number | null;
  sample_size: number;
  archetype_distribution: Record<string, number>;
  last_analyzed_at: string;
}

interface ComparisonTableProps {
  profiles: CommunityProfile[];
  campaignId: string;
}

type SortKey = "subreddit" | "isc_score" | "dominant_tone" | "sample_size";

export default function ComparisonTable({ profiles, campaignId }: ComparisonTableProps) {
  const router = useRouter();
  const [sortKey, setSortKey] = useState<SortKey>("isc_score");
  const [sortDesc, setSortDesc] = useState(true);

  // Sort profiles
  const sortedProfiles = [...profiles].sort((a, b) => {
    let aVal: any = a[sortKey];
    let bVal: any = b[sortKey];

    // Handle null values
    if (aVal === null) return 1;
    if (bVal === null) return -1;

    if (typeof aVal === "string") {
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }

    if (sortDesc) {
      return aVal > bVal ? -1 : aVal < bVal ? 1 : 0;
    } else {
      return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
    }
  });

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDesc(!sortDesc);
    } else {
      setSortKey(key);
      setSortDesc(true);
    }
  };

  const handleRowClick = (subreddit: string) => {
    router.push(`/dashboard/campaigns/${campaignId}/profiles/${subreddit}`);
  };

  // Tier color mapping (backend returns "X Sensitivity" format)
  const tierColors: Record<string, string> = {
    "Low Sensitivity": "bg-green-100 text-green-700",
    "Moderate Sensitivity": "bg-yellow-100 text-yellow-700",
    "High Sensitivity": "bg-orange-100 text-orange-700",
    "Very High Sensitivity": "bg-red-100 text-red-700",
  };

  // Formality level display
  const getFormalityDisplay = (level: number | null): string => {
    if (level === null) return "N/A";
    if (level < 0.33) return "Low";
    if (level < 0.67) return "Medium";
    return "High";
  };

  // Get dominant archetype
  const getDominantArchetype = (distribution: Record<string, number> | null): string => {
    if (!distribution) return "None";
    const entries = Object.entries(distribution);
    if (entries.length === 0) return "None";
    const sorted = entries.sort((a, b) => b[1] - a[1]);
    return `${sorted[0][0]} (${sorted[0][1]})`;
  };

  // Format relative time
  const getRelativeTime = (isoString: string): string => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    if (diffMins > 0) return `${diffMins}m ago`;
    return "Just now";
  };

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              <button
                onClick={() => handleSort("subreddit")}
                className="flex items-center gap-1 font-medium hover:text-foreground"
              >
                Subreddit
                <ArrowUpDown className="h-4 w-4" />
              </button>
            </TableHead>
            <TableHead>
              <button
                onClick={() => handleSort("isc_score")}
                className="flex items-center gap-1 font-medium hover:text-foreground"
              >
                ISC Score
                <ArrowUpDown className="h-4 w-4" />
              </button>
            </TableHead>
            <TableHead>
              <button
                onClick={() => handleSort("dominant_tone")}
                className="flex items-center gap-1 font-medium hover:text-foreground"
              >
                Dominant Tone
                <ArrowUpDown className="h-4 w-4" />
              </button>
            </TableHead>
            <TableHead>Formality</TableHead>
            <TableHead>
              <button
                onClick={() => handleSort("sample_size")}
                className="flex items-center gap-1 font-medium hover:text-foreground"
              >
                Sample Size
                <ArrowUpDown className="h-4 w-4" />
              </button>
            </TableHead>
            <TableHead>Archetypes</TableHead>
            <TableHead>Last Analyzed</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sortedProfiles.map((profile) => (
            <TableRow
              key={profile.id}
              onClick={() => handleRowClick(profile.subreddit)}
              className="cursor-pointer hover:bg-muted/50"
            >
              <TableCell className="font-medium">r/{profile.subreddit}</TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <span className="font-semibold tabular-nums">{profile.isc_score.toFixed(1)}</span>
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${tierColors[profile.isc_tier] || "bg-gray-100 text-gray-700"}`}>
                    {profile.isc_tier}
                  </span>
                </div>
              </TableCell>
              <TableCell>{profile.dominant_tone || "N/A"}</TableCell>
              <TableCell>{getFormalityDisplay(profile.formality_level)}</TableCell>
              <TableCell>{profile.sample_size} posts</TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {getDominantArchetype(profile.archetype_distribution)}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {getRelativeTime(profile.last_analyzed_at)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
