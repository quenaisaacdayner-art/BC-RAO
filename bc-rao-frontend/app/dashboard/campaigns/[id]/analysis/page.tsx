"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { createClient } from "@/lib/supabase/client";
import { ChevronLeft, SlidersHorizontal } from "lucide-react";
import PostScoreBreakdown from "@/components/analysis/PostScoreBreakdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface AnalyzedPost {
  post_id: string;
  post_text: string;
  post_title?: string;
  subreddit: string;
  total_score: number;
  rhythm_adherence: number;
  vulnerability_weight: number;
  formality_match: number;
  marketing_jargon_penalty: number;
  link_density_penalty: number;
}

interface AnalysisResponse {
  posts: AnalyzedPost[];
  total: number;
  page: number;
  per_page: number;
}

export default function AnalysisPage() {
  const router = useRouter();
  const params = useParams();
  const campaignId = params.id as string;
  const [campaign, setCampaign] = useState<{ name: string } | null>(null);
  const [posts, setPosts] = useState<AnalyzedPost[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [subreddits, setSubreddits] = useState<string[]>([]);
  const [selectedSubreddit, setSelectedSubreddit] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("total_score");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [perPage] = useState(20);

  useEffect(() => {
    fetchCampaign();
  }, [campaignId]);

  useEffect(() => {
    fetchAnalyzedPosts();
  }, [campaignId, selectedSubreddit, sortBy, sortDir, page]);

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

  const fetchAnalyzedPosts = async () => {
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

      const params = new URLSearchParams({
        sort_by: sortBy,
        sort_dir: sortDir,
        page: page.toString(),
        per_page: perPage.toString(),
      });

      if (selectedSubreddit !== "all") {
        params.set("subreddit", selectedSubreddit);
      }

      const response = await fetch(
        `/api/campaigns/${campaignId}/analyzed-posts?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch analyzed posts");
      }

      const data: AnalysisResponse = await response.json();
      setPosts(data.posts || []);
      setTotal(data.total || 0);

      // Extract unique subreddits from posts
      if (data.posts && data.posts.length > 0) {
        const uniqueSubreddits = Array.from(
          new Set(data.posts.map((p) => p.subreddit))
        );
        setSubreddits(uniqueSubreddits);
      }
    } catch (error) {
      toast.error("Failed to fetch analysis data");
      console.error(error);
      setPosts([]);
    } finally {
      setIsLoading(false);
    }
  };

  const totalPages = Math.ceil(total / perPage);

  if (isLoading && !posts.length) {
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
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-muted rounded animate-pulse" />
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
          <h1 className="text-3xl font-bold">Post Analysis</h1>
          {campaign && (
            <p className="text-sm text-muted-foreground">{campaign.name}</p>
          )}
        </div>
      </div>

      {/* Filters and sorting */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <SlidersHorizontal className="h-5 w-5" />
            Filters & Sorting
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {/* Subreddit filter */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Subreddit
              </label>
              <select
                value={selectedSubreddit}
                onChange={(e) => {
                  setSelectedSubreddit(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Subreddits</option>
                {subreddits.map((sub) => (
                  <option key={sub} value={sub}>
                    r/{sub}
                  </option>
                ))}
              </select>
            </div>

            {/* Sort by */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => {
                  setSortBy(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="total_score">Total Score</option>
                <option value="vulnerability_weight">Vulnerability</option>
                <option value="rhythm_adherence">Rhythm Match</option>
                <option value="formality_match">Formality</option>
                <option value="marketing_jargon_penalty">Marketing Penalty</option>
              </select>
            </div>

            {/* Sort direction */}
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Direction
              </label>
              <select
                value={sortDir}
                onChange={(e) => {
                  setSortDir(e.target.value as "asc" | "desc");
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {posts.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500 mb-4">
              No analysis data available yet.
            </p>
            <Button asChild>
              <Link href={`/dashboard/campaigns/${campaignId}/collect`}>
                Run Collection
              </Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="space-y-3">
            <div className="text-sm text-muted-foreground mb-2">
              Showing {(page - 1) * perPage + 1}-
              {Math.min(page * perPage, total)} of {total} posts
            </div>
            {posts.map((post) => (
              <PostScoreBreakdown
                key={post.post_id}
                postId={post.post_id}
                campaignId={campaignId}
                postText={post.post_text}
                totalScore={post.total_score}
                postTitle={post.post_title}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-6">
              <Button
                variant="outline"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                Previous
              </Button>
              <span className="px-4 py-2 text-sm text-gray-700">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
