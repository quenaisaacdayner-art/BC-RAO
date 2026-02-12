"use client";

import { formatDistanceToNow } from "date-fns";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import Link from "next/link";

interface ShadowEntry {
  id: string;
  post_url: string;
  subreddit: string;
  status_vida: "Ativo" | "Removido" | "Shadowbanned" | "Auditado";
  submitted_at: string;
  isc_at_post: number;
  audit_result: "SocialSuccess" | "Rejection" | "Inertia" | null;
  campaign_id: string;
  total_checks: number;
  last_check_at: string;
}

interface PostCardProps {
  post: ShadowEntry;
}

function getStatusBadgeVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
  const statusMap: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    Ativo: "default",
    Removido: "secondary",
    Shadowbanned: "destructive",
    Auditado: "outline",
  };
  return statusMap[status] || "outline";
}

function getStatusLabel(status: string): string {
  const labelMap: Record<string, string> = {
    Ativo: "Active",
    Removido: "Removed",
    Shadowbanned: "Shadowbanned",
    Auditado: "Audited",
  };
  return labelMap[status] || status;
}

function getOutcomeBadgeVariant(outcome: string | null): "default" | "destructive" | "secondary" {
  if (!outcome) return "secondary";
  const outcomeMap: Record<string, "default" | "destructive" | "secondary"> = {
    SocialSuccess: "default",
    Rejection: "destructive",
    Inertia: "secondary",
  };
  return outcomeMap[outcome] || "secondary";
}

export default function PostCard({ post }: PostCardProps) {
  const submittedDate = new Date(post.submitted_at);
  const timeAgo = isNaN(submittedDate.getTime())
    ? "Unknown"
    : formatDistanceToNow(submittedDate, { addSuffix: true });

  // Extract a display title from post_url (last path segment)
  const postTitle = (() => {
    try {
      const url = new URL(post.post_url);
      const segments = url.pathname.split("/").filter(Boolean);
      // reddit.com/r/sub/comments/id/title -> title is the last segment
      const titleSegment = segments.length >= 5 ? segments[4] : segments[segments.length - 1];
      return titleSegment.replace(/_/g, " ");
    } catch {
      return post.post_url;
    }
  })();

  return (
    <Accordion type="single" collapsible>
      <AccordionItem value={post.id}>
        <Card>
          <CardHeader>
            <AccordionTrigger className="hover:no-underline">
              <div className="flex flex-1 items-start justify-between gap-4 pr-4">
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-left line-clamp-2">
                    {postTitle}
                  </h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    r/{post.subreddit}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-2 shrink-0">
                  <Badge variant={getStatusBadgeVariant(post.status_vida)}>
                    {getStatusLabel(post.status_vida)}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {timeAgo}
                  </span>
                </div>
              </div>
            </AccordionTrigger>
          </CardHeader>

          <AccordionContent>
            <CardContent className="space-y-4 pt-4 border-t">
              {/* Monitoring Status */}
              <div>
                <h4 className="text-sm font-medium mb-2">Monitoring Status</h4>
                <p className="text-sm text-muted-foreground">
                  {post.total_checks} check{post.total_checks !== 1 ? "s" : ""} performed
                  {post.last_check_at && (() => {
                    const lastCheck = new Date(post.last_check_at);
                    return isNaN(lastCheck.getTime())
                      ? ""
                      : ` — last ${formatDistanceToNow(lastCheck, { addSuffix: true })}`;
                  })()}
                </p>
              </div>

              {/* ISC at Posting */}
              <div>
                <h4 className="text-sm font-medium mb-2">ISC at Posting</h4>
                <div className="text-2xl font-bold">
                  {post.isc_at_post.toFixed(2)}
                </div>
              </div>

              {/* Outcome Classification (if audited) */}
              {post.audit_result && (
                <div>
                  <h4 className="text-sm font-medium mb-2">
                    Outcome Classification
                  </h4>
                  <Badge variant={getOutcomeBadgeVariant(post.audit_result)}>
                    {post.audit_result}
                  </Badge>
                </div>
              )}

              {/* Pattern Analysis (if removed/shadowbanned) */}
              {(post.status_vida === "Removido" ||
                post.status_vida === "Shadowbanned") && (
                <div>
                  <h4 className="text-sm font-medium mb-2">Pattern Analysis</h4>
                  <p className="text-sm text-muted-foreground">
                    Auto-extracted patterns added to{" "}
                    <Link
                      href={`/dashboard/campaigns/${post.campaign_id}/blacklist`}
                      className="text-primary hover:underline"
                    >
                      blacklist
                    </Link>
                  </p>
                </div>
              )}
            </CardContent>
          </AccordionContent>
        </Card>
      </AccordionItem>
    </Accordion>
  );
}
