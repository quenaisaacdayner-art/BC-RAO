"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { createClient } from "@/lib/supabase/client";

interface Post {
  id: string;
  title: string;
  raw_text: string;
  subreddit: string;
  archetype: "Journey" | "ProblemSolution" | "Feedback";
  success_score: number;
  author?: string;
  reddit_created_at?: string;
  upvote_ratio?: number;
  comment_count?: number;
}

interface PostGridProps {
  campaignId: string;
  filters: {
    archetype: string | null;
    subreddit: string | null;
    minScore: number;
    maxScore: number;
  };
  onPostClick: (post: Post) => void;
}

export default function PostGrid({ campaignId, filters, onPostClick }: PostGridProps) {
  const [posts, setPosts] = useState<Post[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const perPage = 20;

  // Fetch posts when filters or page changes
  useEffect(() => {
    fetchPosts();
  }, [campaignId, filters, page]);

  async function fetchPosts() {
    setLoading(true);
    setError(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        setError("Authentication required");
        return;
      }

      // Build query params
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: perPage.toString(),
      });

      if (filters.archetype) params.set("archetype", filters.archetype);
      if (filters.subreddit) params.set("subreddit", filters.subreddit);
      params.set("min_score", filters.minScore.toString());
      params.set("max_score", filters.maxScore.toString());

      const response = await fetch(
        `/api/campaigns/${campaignId}/posts?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to load posts");
      }

      const data = await response.json();
      setPosts(data.posts || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load posts");
    } finally {
      setLoading(false);
    }
  }

  // Reset to page 1 when filters change
  useEffect(() => {
    setPage(1);
  }, [filters]);

  const archetypeColors: Record<string, string> = {
    Journey: "bg-blue-500/10 text-blue-700 border-blue-500/20",
    ProblemSolution: "bg-purple-500/10 text-purple-700 border-purple-500/20",
    Feedback: "bg-green-500/10 text-green-700 border-green-500/20",
  };

  if (loading && posts.length === 0) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-4 w-1/2 mt-2" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full mt-2" />
              <Skeleton className="h-4 w-2/3 mt-2" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <p className="text-sm text-destructive">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (posts.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-muted-foreground">
            No posts collected yet. Start a collection to see results here.
          </p>
        </CardContent>
      </Card>
    );
  }

  const startIdx = (page - 1) * perPage + 1;
  const endIdx = Math.min(page * perPage, total);

  return (
    <div className="space-y-4">
      {/* Post Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {posts.map((post) => (
          <Card
            key={post.id}
            className="cursor-pointer hover:shadow-lg transition-shadow"
            onClick={() => onPostClick(post)}
          >
            <CardHeader>
              {/* Title */}
              <h3 className="font-semibold line-clamp-2 text-sm">{post.title}</h3>

              {/* Badges row */}
              <div className="flex items-center gap-2 mt-2">
                <Badge
                  variant="outline"
                  className={archetypeColors[post.archetype] || ""}
                >
                  {post.archetype === "ProblemSolution"
                    ? "Problem-Solution"
                    : post.archetype}
                </Badge>
                <Badge variant="outline">r/{post.subreddit}</Badge>
              </div>
            </CardHeader>

            <CardContent className="space-y-3">
              {/* Post snippet */}
              <p className="text-sm text-muted-foreground line-clamp-3">
                {post.raw_text}
              </p>

              {/* Score display */}
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium">
                  {post.success_score.toFixed(1)}/10
                </span>
                <Progress
                  value={(post.success_score / 10) * 100}
                  className="h-2 flex-1"
                  style={{ maxWidth: "80px" }}
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between pt-4">
        <p className="text-sm text-muted-foreground">
          Showing {startIdx}-{endIdx} of {total}
        </p>

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => p + 1)}
            disabled={endIdx >= total}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
