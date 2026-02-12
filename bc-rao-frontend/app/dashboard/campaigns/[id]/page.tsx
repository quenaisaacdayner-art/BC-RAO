"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { createClient } from "@/lib/supabase/client";
import { apiClient } from "@/lib/api";
import { DeleteCampaignDialog } from "@/components/campaigns/delete-campaign-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChevronLeft, Edit, Database, Users, BarChart3, ShieldAlert, Wand2, Lock, FileText, Rocket } from "lucide-react";
import StageIndicator from "@/components/dashboard/StageIndicator";
import { computeStages } from "@/lib/campaign-stages";
import DraftCard from "@/components/drafts/DraftCard";

interface Campaign {
  id: string;
  name: string;
  status: "active" | "paused" | "archived";
  product_context: string;
  product_url?: string;
  keywords: string[];
  target_subreddits: string[];
  created_at: string;
  updated_at: string;
  stats: {
    posts_collected: number;
    drafts_generated: number;
    active_monitors: number;
    monitored_posts?: number;
  };
}

interface CommunityProfile {
  id: string;
  subreddit: string;
}

interface Draft {
  id: string;
  campaign_id: string;
  subreddit: string;
  archetype: string;
  body: string;
  vulnerability_score: number;
  rhythm_score: number;
  status: string;
  created_at: string;
}

export default function CampaignDetailPage() {
  const router = useRouter();
  const params = useParams();
  const campaignId = params.id as string;
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [profiles, setProfiles] = useState<CommunityProfile[]>([]);
  const [recentDrafts, setRecentDrafts] = useState<Draft[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchCampaign();
  }, [campaignId]);

  const fetchCampaign = async () => {
    setIsLoading(true);
    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        toast.error("Authentication required. Please log in again.");
        router.push("/login");
        return;
      }

      const response = await apiClient.get<Campaign>(
        `/campaigns/${campaignId}`,
        session.access_token
      );

      if (response.error) {
        toast.error(response.error.message || "Failed to fetch campaign");
        router.push("/dashboard/campaigns");
        return;
      }

      setCampaign(response.data!);

      // Fetch community profiles for stage computation
      try {
        const profilesResponse = await apiClient.get<{ profiles: CommunityProfile[] }>(
          `/campaigns/${campaignId}/community-profiles`,
          session.access_token
        );
        if (!profilesResponse.error && profilesResponse.data?.profiles) {
          setProfiles(profilesResponse.data.profiles);
        }
      } catch (error) {
        console.error("Error fetching profiles:", error);
      }

      // Fetch recent drafts (top 3)
      try {
        const draftsResponse = await apiClient.get<{ drafts: Draft[] }>(
          `/campaigns/${campaignId}/drafts?limit=3`,
          session.access_token
        );
        if (!draftsResponse.error && draftsResponse.data?.drafts) {
          setRecentDrafts(draftsResponse.data.drafts);
        }
      } catch (error) {
        console.error("Error fetching drafts:", error);
      }
    } catch (error) {
      toast.error("An unexpected error occurred");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const statusColors = {
    active: "bg-green-500/10 text-green-500 border-green-500/20",
    paused: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
    archived: "bg-gray-500/10 text-gray-500 border-gray-500/20",
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <Link
            href="/dashboard/campaigns"
            className="flex items-center text-sm text-muted-foreground hover:text-foreground"
          >
            <ChevronLeft className="h-4 w-4" />
            Back to campaigns
          </Link>
        </div>
        <div className="h-8 w-1/3 bg-muted rounded animate-pulse" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <div className="h-6 w-1/4 bg-muted rounded" />
              </CardHeader>
              <CardContent>
                <div className="h-4 bg-muted rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!campaign) {
    return null;
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  // Compute stages for StageIndicator
  const stages = computeStages(campaign, profiles);
  const stage3Complete = profiles.length > 0;
  const stage4Complete = campaign.stats.drafts_generated > 0;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-center gap-2">
        <Link
          href="/dashboard/campaigns"
          className="flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="h-4 w-4" />
          Back to campaigns
        </Link>
      </div>

      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold">{campaign.name}</h1>
          <span
            className={`inline-block rounded-full border px-3 py-1 text-xs font-medium ${
              statusColors[campaign.status]
            }`}
          >
            {campaign.status}
          </span>
        </div>
        <div className="flex gap-2">
          <Button asChild>
            <Link href={`/dashboard/campaigns/${campaign.id}/collect`}>
              <Database className="mr-2 h-4 w-4" />
              Collect Data
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href={`/dashboard/campaigns/${campaign.id}/edit`}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Link>
          </Button>
          <DeleteCampaignDialog
            campaignId={campaign.id}
            campaignName={campaign.name}
          />
        </div>
      </div>

      {/* Stage Indicator */}
      <StageIndicator stages={stages} />

      <div className="grid gap-6">
        {/* Quick Actions */}
        <div className="grid gap-4 md:grid-cols-4">
          <Link href={`/dashboard/campaigns/${campaign.id}/profiles`}>
            <Card className="hover:bg-gray-50 transition-colors cursor-pointer h-full">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Users className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm mb-1">Community Profiles</h3>
                    <p className="text-xs text-muted-foreground">
                      View subreddit ISC scores and top archetypes
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>

          <Link href={`/dashboard/campaigns/${campaign.id}/analysis`}>
            <Card className="hover:bg-gray-50 transition-colors cursor-pointer h-full">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <BarChart3 className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm mb-1">Post Analysis</h3>
                    <p className="text-xs text-muted-foreground">
                      Scoring breakdowns with inline penalty highlights
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>

          <Link href={`/dashboard/campaigns/${campaign.id}/blacklist`}>
            <Card className="hover:bg-gray-50 transition-colors cursor-pointer h-full">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <ShieldAlert className="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm mb-1">Forbidden Patterns</h3>
                    <p className="text-xs text-muted-foreground">
                      Manage blacklisted patterns by subreddit
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Draft Generation Card */}
          {stage3Complete ? (
            <Link href={`/dashboard/campaigns/${campaign.id}/drafts/new`}>
              <Card className="hover:bg-gray-50 transition-colors cursor-pointer h-full">
                <CardContent className="pt-6">
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <Wand2 className="h-5 w-5 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-sm mb-1">Draft Generation</h3>
                      <p className="text-xs text-muted-foreground">
                        Generate posts with community DNA
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ) : (
            <Card className="opacity-50 cursor-not-allowed h-full">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-gray-100 rounded-lg">
                    <Lock className="h-5 w-5 text-gray-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm mb-1 text-muted-foreground">
                      Draft Generation
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      Complete analysis to unlock
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Stage 4: Alchemical Transmutation */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wand2 className="h-5 w-5 text-purple-600" />
              Alchemical Transmutation
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!stage3Complete ? (
              <div className="text-center py-8">
                <Lock className="h-12 w-12 text-muted-foreground mx-auto mb-3 opacity-50" />
                <h3 className="font-semibold text-lg mb-2">Stage Locked</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Complete Community Intelligence (Stage 3) to unlock draft generation.
                </p>
                <Button asChild>
                  <Link href={`/dashboard/campaigns/${campaign.id}/profiles`}>
                    View Community Profiles
                  </Link>
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Generate Button */}
                <div className="flex items-center justify-between">
                  <p className="text-sm text-muted-foreground">
                    Generate Reddit posts that match community behavioral patterns
                  </p>
                  <Button asChild>
                    <Link href={`/dashboard/campaigns/${campaign.id}/drafts/new`}>
                      <Wand2 className="mr-2 h-4 w-4" />
                      Generate Draft
                    </Link>
                  </Button>
                </div>

                {/* Recent Drafts */}
                {recentDrafts.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-sm">Recent Drafts</h4>
                      <Button asChild variant="link" size="sm">
                        <Link href={`/dashboard/campaigns/${campaign.id}/drafts`}>
                          <FileText className="mr-1 h-3 w-3" />
                          View All
                        </Link>
                      </Button>
                    </div>
                    <div className="grid gap-3">
                      {recentDrafts.map((draft) => (
                        <DraftCard key={draft.id} draft={draft} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Empty State */}
                {recentDrafts.length === 0 && (
                  <div className="text-center py-6 border-t">
                    <p className="text-sm text-muted-foreground">
                      No drafts yet. Generate your first draft to get started.
                    </p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Stage 5: Deployment & Monitoring */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Rocket className="h-5 w-5 text-orange-600" />
              Deployment & Monitoring
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!stage4Complete ? (
              <div className="text-center py-8">
                <Lock className="h-12 w-12 text-muted-foreground mx-auto mb-3 opacity-50" />
                <h3 className="font-semibold text-lg mb-2">Stage Locked</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Complete Alchemical Transmutation (Stage 4) to unlock deployment monitoring.
                </p>
                <Button asChild>
                  <Link href={`/dashboard/campaigns/${campaign.id}/drafts/new`}>
                    Generate Drafts
                  </Link>
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Ready to deploy? Post your approved drafts on Reddit, then register the URL here or on the monitoring page to start tracking.
                </p>

                {/* Monitored posts count */}
                {(campaign.stats.monitored_posts ?? 0) > 0 && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <p className="text-sm font-semibold text-green-800">
                      {campaign.stats.monitored_posts} post{campaign.stats.monitored_posts !== 1 ? 's' : ''} currently being monitored
                    </p>
                  </div>
                )}

                {/* Go to Monitoring button */}
                <div className="flex items-center justify-end">
                  <Button asChild>
                    <Link href={`/dashboard/campaigns/${campaign.id}/monitoring`}>
                      <Rocket className="mr-2 h-4 w-4" />
                      Go to Monitoring
                    </Link>
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Product Context</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{campaign.product_context}</p>
          </CardContent>
        </Card>

        {campaign.product_url && (
          <Card>
            <CardHeader>
              <CardTitle>Product URL</CardTitle>
            </CardHeader>
            <CardContent>
              <a
                href={campaign.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline"
              >
                {campaign.product_url}
              </a>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Keywords</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {campaign.keywords.map((keyword) => (
                <span
                  key={keyword}
                  className="rounded-md bg-secondary px-3 py-1 text-sm"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Target Subreddits</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              {campaign.target_subreddits.map((subreddit) => (
                <div key={subreddit} className="text-sm">
                  <a
                    href={`https://reddit.com/r/${subreddit}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    r/{subreddit}
                  </a>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <p className="text-sm text-muted-foreground">Posts Collected</p>
                <p className="text-2xl font-bold">{campaign.stats.posts_collected}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Drafts Generated</p>
                <p className="text-2xl font-bold">{campaign.stats.drafts_generated}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Active Monitors</p>
                <p className="text-2xl font-bold">{campaign.stats.active_monitors}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Metadata</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Created</span>
              <span>{formatDate(campaign.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Last Updated</span>
              <span>{formatDate(campaign.updated_at)}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
