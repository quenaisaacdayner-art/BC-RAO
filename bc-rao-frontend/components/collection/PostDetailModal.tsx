"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

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

interface PostDetailModalProps {
  post: Post | null;
  open: boolean;
  onClose: () => void;
}

export default function PostDetailModal({ post, open, onClose }: PostDetailModalProps) {
  if (!post) return null;

  const archetypeColors: Record<string, string> = {
    Journey: "bg-blue-500/10 text-blue-700 border-blue-500/20",
    ProblemSolution: "bg-purple-500/10 text-purple-700 border-purple-500/20",
    Feedback: "bg-green-500/10 text-green-700 border-green-500/20",
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const formatUpvoteRatio = (ratio?: number) => {
    if (ratio === undefined) return "N/A";
    return `${(ratio * 100).toFixed(0)}%`;
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl">{post.title}</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Badges row */}
          <div className="flex flex-wrap items-center gap-2">
            <Badge
              variant="outline"
              className={archetypeColors[post.archetype] || ""}
            >
              {post.archetype === "ProblemSolution"
                ? "Problem-Solution"
                : post.archetype}
            </Badge>
            <Badge variant="outline">r/{post.subreddit}</Badge>
            <Badge variant="secondary">
              Score: {post.success_score.toFixed(1)}/10
            </Badge>
          </div>

          {/* Full post text */}
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <div className="rounded-lg border bg-muted/30 p-4 max-h-[60vh] overflow-y-auto">
              <p className="whitespace-pre-wrap text-sm">{post.raw_text}</p>
            </div>
          </div>

          {/* Metadata grid */}
          <div className="grid grid-cols-2 gap-4 rounded-lg border bg-card p-4">
            <div>
              <p className="text-xs text-muted-foreground">Author</p>
              <p className="text-sm font-medium">u/{post.author || "N/A"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Date</p>
              <p className="text-sm font-medium">{formatDate(post.reddit_created_at)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Upvote Ratio</p>
              <p className="text-sm font-medium">{formatUpvoteRatio(post.upvote_ratio)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Comments</p>
              <p className="text-sm font-medium">{post.comment_count ?? "N/A"}</p>
            </div>
          </div>

          {/* Success score visualization */}
          <div className="space-y-2">
            <p className="text-sm font-medium">Success Score</p>
            <div className="flex items-center gap-3">
              <span className="text-lg font-bold">
                {post.success_score.toFixed(1)}/10
              </span>
              <Progress
                value={(post.success_score / 10) * 100}
                className="h-3 flex-1"
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Based on engagement potential, content quality, and archetype match
            </p>
          </div>

          {/* Archetype label */}
          <div className="rounded-lg border bg-muted/30 p-4">
            <p className="text-xs text-muted-foreground mb-1">Archetype</p>
            <p className="text-sm font-medium">
              {post.archetype === "ProblemSolution"
                ? "Problem-Solution"
                : post.archetype}
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              {post.archetype === "Journey" &&
                "Narrative posts sharing personal experiences and transformations"}
              {post.archetype === "ProblemSolution" &&
                "Posts presenting problems and solutions, ideal for product recommendations"}
              {post.archetype === "Feedback" &&
                "Posts seeking opinions or feedback, opportunity for engagement"}
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
