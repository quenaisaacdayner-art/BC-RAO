"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { createClient } from "@/lib/supabase/client";
import { ChevronLeft, Plus } from "lucide-react";
import BlacklistTable from "@/components/analysis/BlacklistTable";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ForbiddenPattern {
  id: string;
  pattern: string;
  category: string;
  is_system: boolean;
  subreddit?: string;
  severity?: string;
}

interface BlacklistResponse {
  patterns: ForbiddenPattern[];
  categories: Record<string, number>;
}

const CATEGORY_OPTIONS = [
  "Promotional",
  "Self-referential",
  "Link patterns",
  "Low-effort",
  "Spam indicators",
  "Off-topic",
  "Custom",
];

export default function BlacklistPage() {
  const router = useRouter();
  const params = useParams();
  const campaignId = params.id as string;
  const [campaign, setCampaign] = useState<{ name: string; target_subreddits: string[] } | null>(null);
  const [patterns, setPatterns] = useState<ForbiddenPattern[]>([]);
  const [categories, setCategories] = useState<Record<string, number>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [selectedSubreddit, setSelectedSubreddit] = useState<string>("all");
  const [isAddingPattern, setIsAddingPattern] = useState(false);
  const [newPattern, setNewPattern] = useState({
    category: "Custom",
    pattern: "",
    subreddit: "",
  });

  useEffect(() => {
    fetchCampaign();
  }, [campaignId]);

  useEffect(() => {
    fetchPatterns();
  }, [campaignId, selectedSubreddit]);

  const fetchCampaign = async () => {
    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        toast.error("Authentication required");
        router.push("/login");
        return;
      }

      const response = await fetch(`/api/campaigns/${campaignId}`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) throw new Error("Failed to fetch campaign");

      const data = await response.json();
      setCampaign(data);
    } catch (error) {
      toast.error("Failed to fetch campaign");
      console.error(error);
    }
  };

  const fetchPatterns = async () => {
    setIsLoading(true);
    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        toast.error("Authentication required");
        router.push("/login");
        return;
      }

      const params = new URLSearchParams();
      if (selectedSubreddit !== "all") {
        params.set("subreddit", selectedSubreddit);
      }

      const response = await fetch(
        `/api/campaigns/${campaignId}/forbidden-patterns${params.toString() ? `?${params.toString()}` : ""}`,
        {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch forbidden patterns");
      }

      const data: BlacklistResponse = await response.json();
      setPatterns(data.patterns || []);
      setCategories(data.categories || {});
    } catch (error) {
      toast.error("Failed to fetch blacklist data");
      console.error(error);
      setPatterns([]);
      setCategories({});
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddPattern = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newPattern.pattern.trim()) {
      toast.error("Pattern text is required");
      return;
    }

    setIsAddingPattern(true);

    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        toast.error("Authentication required");
        router.push("/login");
        return;
      }

      const body: any = {
        category: newPattern.category,
        pattern: newPattern.pattern.trim(),
      };

      if (newPattern.subreddit && newPattern.subreddit !== "all") {
        body.subreddit = newPattern.subreddit;
      }

      const response = await fetch(
        `/api/campaigns/${campaignId}/forbidden-patterns`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
          body: JSON.stringify(body),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to add pattern");
      }

      toast.success("Custom pattern added successfully");
      setNewPattern({ category: "Custom", pattern: "", subreddit: "" });
      fetchPatterns(); // Refresh list
    } catch (error) {
      toast.error("Failed to add custom pattern");
      console.error(error);
    } finally {
      setIsAddingPattern(false);
    }
  };

  if (isLoading && !patterns.length) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <Link
            href={`/dashboard/campaigns/${campaignId}`}
            className="flex items-center text-sm text-muted-foreground hover:text-foreground"
          >
            <ChevronLeft className="h-4 w-4" />
            Back to campaign
          </Link>
        </div>
        <div className="h-8 w-1/3 bg-muted rounded animate-pulse" />
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-32 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex items-center gap-2">
        <Link
          href={`/dashboard/campaigns/${campaignId}`}
          className="flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="h-4 w-4" />
          Back to campaign
        </Link>
      </div>

      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold">Forbidden Patterns</h1>
          {campaign && (
            <p className="text-sm text-muted-foreground">{campaign.name}</p>
          )}
        </div>
      </div>

      {/* Subreddit filter */}
      <Card>
        <CardHeader>
          <CardTitle>Filter by Subreddit</CardTitle>
        </CardHeader>
        <CardContent>
          <select
            value={selectedSubreddit}
            onChange={(e) => setSelectedSubreddit(e.target.value)}
            className="w-full md:w-64 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Subreddits</option>
            {campaign?.target_subreddits.map((sub) => (
              <option key={sub} value={sub}>
                r/{sub}
              </option>
            ))}
          </select>
        </CardContent>
      </Card>

      {/* Patterns table */}
      <Card>
        <CardHeader>
          <CardTitle>Detected Patterns</CardTitle>
        </CardHeader>
        <CardContent>
          <BlacklistTable patterns={patterns} categories={categories} />
        </CardContent>
      </Card>

      {/* Add custom pattern form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Add Custom Pattern
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAddPattern} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  Category
                </label>
                <select
                  value={newPattern.category}
                  onChange={(e) =>
                    setNewPattern({ ...newPattern, category: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {CATEGORY_OPTIONS.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  Pattern (text or regex)
                </label>
                <input
                  type="text"
                  value={newPattern.pattern}
                  onChange={(e) =>
                    setNewPattern({ ...newPattern, pattern: e.target.value })
                  }
                  placeholder="e.g., 'check out my site' or 'use code.*discount'"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  Scope (optional)
                </label>
                <select
                  value={newPattern.subreddit}
                  onChange={(e) =>
                    setNewPattern({ ...newPattern, subreddit: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Subreddits</option>
                  {campaign?.target_subreddits.map((sub) => (
                    <option key={sub} value={sub}>
                      r/{sub}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <Button type="submit" disabled={isAddingPattern}>
              {isAddingPattern ? "Adding..." : "Add Pattern"}
            </Button>
          </form>

          <p className="text-xs text-gray-500 mt-4">
            System-detected patterns cannot be removed. Custom patterns apply to
            your campaign only.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
