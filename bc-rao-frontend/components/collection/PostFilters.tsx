"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";

interface PostFiltersProps {
  subreddits: string[];
  onFiltersChange: (filters: {
    archetype: string | null;
    subreddit: string | null;
    minScore: number;
    maxScore: number;
  }) => void;
}

export default function PostFilters({ subreddits, onFiltersChange }: PostFiltersProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Read initial values from URL params
  const [archetype, setArchetype] = useState<string | null>(
    searchParams.get("archetype") || null
  );
  const [subreddit, setSubreddit] = useState<string | null>(
    searchParams.get("subreddit") || null
  );
  const [scoreRange, setScoreRange] = useState<[number, number]>([
    parseFloat(searchParams.get("minScore") || "0"),
    parseFloat(searchParams.get("maxScore") || "10"),
  ]);

  // Update URL params and trigger callback when filters change
  useEffect(() => {
    const params = new URLSearchParams();

    if (archetype) params.set("archetype", archetype);
    if (subreddit) params.set("subreddit", subreddit);
    params.set("minScore", scoreRange[0].toString());
    params.set("maxScore", scoreRange[1].toString());

    // Update URL without triggering navigation
    router.replace(`?${params.toString()}`, { scroll: false });

    // Trigger callback
    onFiltersChange({
      archetype: archetype === "all" ? null : archetype,
      subreddit: subreddit === "all" ? null : subreddit,
      minScore: scoreRange[0],
      maxScore: scoreRange[1],
    });
  }, [archetype, subreddit, scoreRange, router, onFiltersChange]);

  return (
    <div className="flex flex-col md:flex-row gap-4 p-4 bg-muted/30 rounded-lg border">
      {/* Archetype Filter */}
      <div className="flex-1 space-y-2">
        <Label htmlFor="archetype-filter" className="text-xs text-muted-foreground">
          Archetype
        </Label>
        <Select
          value={archetype || "all"}
          onValueChange={(value) => setArchetype(value === "all" ? null : value)}
        >
          <SelectTrigger id="archetype-filter" className="w-full">
            <SelectValue placeholder="All Archetypes" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Archetypes</SelectItem>
            <SelectItem value="Journey">Journey</SelectItem>
            <SelectItem value="ProblemSolution">Problem-Solution</SelectItem>
            <SelectItem value="Feedback">Feedback</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Subreddit Filter */}
      <div className="flex-1 space-y-2">
        <Label htmlFor="subreddit-filter" className="text-xs text-muted-foreground">
          Subreddit
        </Label>
        <Select
          value={subreddit || "all"}
          onValueChange={(value) => setSubreddit(value === "all" ? null : value)}
        >
          <SelectTrigger id="subreddit-filter" className="w-full">
            <SelectValue placeholder="All Subreddits" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Subreddits</SelectItem>
            {subreddits.map((sub) => (
              <SelectItem key={sub} value={sub}>
                r/{sub}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Score Range Filter */}
      <div className="flex-1 space-y-2">
        <Label htmlFor="score-filter" className="text-xs text-muted-foreground">
          Score Range: {scoreRange[0].toFixed(1)} - {scoreRange[1].toFixed(1)}
        </Label>
        <div className="pt-2">
          <Slider
            id="score-filter"
            min={0}
            max={10}
            step={0.5}
            value={scoreRange}
            onValueChange={(value) => setScoreRange(value as [number, number])}
            className="w-full"
          />
        </div>
      </div>
    </div>
  );
}
