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

interface CheckRecord {
  checked_at: string;
  auth_visible: boolean;
  anon_visible: boolean;
}

interface ShadowEntry {
  shadow_id: string;
  post_title: string;
  subreddit: string;
  status_vida: "Ativo" | "Removido" | "Shadowbanned" | "Auditado";
  posted_at: string;
  isc_at_posting: number | null;
  outcome_classification: "SocialSuccess" | "Rejection" | "Inertia" | null;
  check_history: CheckRecord[];
  campaign_id: string;
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
  const timeAgo = formatDistanceToNow(new Date(post.posted_at), { addSuffix: true });

  return (
    <Accordion type="single" collapsible>
      <AccordionItem value={post.shadow_id}>
        <Card>
          <CardHeader>
            <AccordionTrigger className="hover:no-underline">
              <div className="flex flex-1 items-start justify-between gap-4 pr-4">
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-left line-clamp-2">
                    {post.post_title}
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
              {/* Check History */}
              <div>
                <h4 className="text-sm font-medium mb-2">Check History</h4>
                <div className="space-y-2">
                  {post.check_history.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No checks performed yet
                    </p>
                  ) : (
                    post.check_history.map((check, index) => (
                      <div
                        key={index}
                        className="flex items-center gap-2 text-sm"
                      >
                        <span className="text-muted-foreground">
                          {formatDistanceToNow(new Date(check.checked_at), {
                            addSuffix: true,
                          })}
                        </span>
                        <Badge variant={check.auth_visible ? "default" : "secondary"} className="text-xs">
                          Auth: {check.auth_visible ? "Visible" : "Hidden"}
                        </Badge>
                        <Badge variant={check.anon_visible ? "default" : "secondary"} className="text-xs">
                          Anon: {check.anon_visible ? "Visible" : "Hidden"}
                        </Badge>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* ISC at Posting */}
              <div>
                <h4 className="text-sm font-medium mb-2">ISC at Posting</h4>
                <div className="text-2xl font-bold">
                  {post.isc_at_posting !== null
                    ? post.isc_at_posting.toFixed(2)
                    : "N/A"}
                </div>
              </div>

              {/* Outcome Classification (if audited) */}
              {post.outcome_classification && (
                <div>
                  <h4 className="text-sm font-medium mb-2">
                    Outcome Classification
                  </h4>
                  <Badge variant={getOutcomeBadgeVariant(post.outcome_classification)}>
                    {post.outcome_classification}
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
