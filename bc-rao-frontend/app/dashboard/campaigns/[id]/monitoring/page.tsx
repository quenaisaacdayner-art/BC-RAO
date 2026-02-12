"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import MonitoringStats from "@/components/monitoring/MonitoringStats";
import StatusFilter from "@/components/monitoring/StatusFilter";
import PostCard from "@/components/monitoring/PostCard";
import ShadowbanAlert from "@/components/monitoring/ShadowbanAlert";
import { createClient } from "@/lib/supabase/client";
import { toast } from "sonner";

interface Campaign {
  id: string;
  name: string;
}

interface DashboardStats {
  active_count: number;
  removed_count: number;
  shadowbanned_count: number;
  total_count: number;
  success_rate: number;
}

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

export default function MonitoringPage() {
  const params = useParams();
  const router = useRouter();
  const campaignId = params?.id as string;

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [posts, setPosts] = useState<ShadowEntry[]>([]);
  const [filteredPosts, setFilteredPosts] = useState<ShadowEntry[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [postUrl, setPostUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [registering, setRegistering] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Shadowban alert state
  const [shadowbanAlert, setShadowbanAlert] = useState<{
    isOpen: boolean;
    postTitle: string;
    subreddit: string;
    detectedAt: string;
    shadowId: string;
  } | null>(null);

  // Fetch campaign details
  useEffect(() => {
    async function fetchCampaign() {
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();

        if (!session) {
          router.push("/login");
          return;
        }

        const response = await fetch(`/api/campaigns/${campaignId}`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to load campaign");
        }

        const data = await response.json();
        setCampaign({
          id: data.id,
          name: data.name,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load campaign");
      } finally {
        setLoading(false);
      }
    }

    fetchCampaign();
  }, [campaignId, router]);

  // Fetch dashboard stats
  const fetchStats = useCallback(async () => {
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) return;

      const response = await fetch(
        `/api/monitoring/dashboard?campaign_id=${campaignId}`,
        {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Failed to fetch stats:", err);
    }
  }, [campaignId]);

  // Fetch monitored posts
  const fetchPosts = useCallback(async () => {
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) return;

      const statusParam = statusFilter ? `&status=${statusFilter}` : "";
      const response = await fetch(
        `/api/monitoring?campaign_id=${campaignId}${statusParam}`,
        {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        }
      );

      if (response.ok) {
        const responseData = await response.json();
        const postsArray = Array.isArray(responseData)
          ? responseData
          : responseData.posts || [];
        setPosts(postsArray);
        setFilteredPosts(postsArray);
      }
    } catch (err) {
      console.error("Failed to fetch posts:", err);
    }
  }, [campaignId, statusFilter]);

  // Initial fetch
  useEffect(() => {
    if (campaign) {
      fetchStats();
      fetchPosts();
    }
  }, [campaign, fetchStats, fetchPosts]);

  // Polling for real-time updates (every 30 seconds)
  useEffect(() => {
    if (!campaign) return;

    const interval = setInterval(() => {
      fetchStats();
      fetchPosts();
    }, 30000);

    return () => clearInterval(interval);
  }, [campaign, fetchStats, fetchPosts]);

  // Re-fetch when filter changes
  useEffect(() => {
    if (campaign) {
      fetchPosts();
    }
  }, [campaign, fetchPosts]);

  // Check for shadowbanned posts and show alert
  useEffect(() => {
    const shadowbannedPost = posts.find(
      (post) => post.status_vida === "Shadowbanned"
    );

    if (shadowbannedPost) {
      const dismissKey = `shadowban_alert_dismissed_${shadowbannedPost.id}`;
      const isDismissed = localStorage.getItem(dismissKey);

      if (!isDismissed) {
        setShadowbanAlert({
          isOpen: true,
          postTitle: shadowbannedPost.subreddit,
          subreddit: shadowbannedPost.subreddit,
          detectedAt: shadowbannedPost.submitted_at,
          shadowId: shadowbannedPost.id,
        });
      }
    }
  }, [posts]);

  // Handle shadowban alert dismiss
  function handleDismissShadowbanAlert() {
    if (shadowbanAlert) {
      const dismissKey = `shadowban_alert_dismissed_${shadowbanAlert.shadowId}`;
      localStorage.setItem(dismissKey, "true");
      setShadowbanAlert(null);
    }
  }

  // Validate Reddit URL
  function isValidRedditUrl(url: string): boolean {
    const redditUrlPattern =
      /^https?:\/\/(www\.)?reddit\.com\/r\/[^/]+\/comments\/[^/]+\/.*/;
    return redditUrlPattern.test(url);
  }

  // Handle post registration
  async function handleRegisterPost() {
    if (!postUrl.trim()) {
      toast.error("Please enter a Reddit post URL");
      return;
    }

    if (!isValidRedditUrl(postUrl)) {
      toast.error("Invalid Reddit URL format. Please use a valid post URL.");
      return;
    }

    setRegistering(true);
    setError(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        router.push("/login");
        return;
      }

      const response = await fetch("/api/monitoring", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          post_url: postUrl,
          campaign_id: campaignId,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error?.message || "Failed to register post");
      }

      toast.success("Post registered! Monitoring started.");
      setPostUrl("");

      // Refresh stats and posts
      fetchStats();
      fetchPosts();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to register post";
      toast.error(errorMessage);
      setError(errorMessage);
    } finally {
      setRegistering(false);
    }
  }

  if (loading) {
    return (
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-64 bg-muted rounded"></div>
          <div className="h-32 bg-muted rounded"></div>
        </div>
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Campaign not found</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
      {/* Page Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Post Monitoring</h2>
        <p className="text-muted-foreground">{campaign.name}</p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm font-medium text-red-800">Error</p>
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* URL Registration Section */}
      <Card>
        <CardHeader>
          <CardTitle>Register New Post</CardTitle>
          <CardDescription>
            Paste your Reddit post URL to start monitoring its status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              type="url"
              placeholder="Paste your Reddit post URL here..."
              value={postUrl}
              onChange={(e) => setPostUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleRegisterPost();
                }
              }}
              disabled={registering}
            />
            <Button onClick={handleRegisterPost} disabled={registering}>
              {registering ? "Registering..." : "Register Post"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats Header */}
      {stats && <MonitoringStats stats={stats} />}

      {/* Status Filter */}
      {stats && (
        <StatusFilter
          value={statusFilter}
          onChange={setStatusFilter}
          counts={{
            all: stats.total_count,
            active: stats.active_count,
            removed: stats.removed_count,
            shadowbanned: stats.shadowbanned_count,
          }}
        />
      )}

      {/* Posts List */}
      <div className="space-y-4">
        {filteredPosts.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <p className="text-sm text-muted-foreground text-center">
                No monitored posts yet. Post a draft on Reddit and paste the URL
                above to start monitoring.
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredPosts.map((post) => <PostCard key={post.id} post={post} />)
        )}
      </div>

      {/* Shadowban Alert Modal */}
      {shadowbanAlert && (
        <ShadowbanAlert
          isOpen={shadowbanAlert.isOpen}
          onDismiss={handleDismissShadowbanAlert}
          postTitle={shadowbanAlert.postTitle}
          subreddit={shadowbanAlert.subreddit}
          detectedAt={shadowbanAlert.detectedAt}
        />
      )}
    </div>
  );
}
