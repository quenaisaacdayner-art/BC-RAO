"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import DraftCard from "@/components/drafts/DraftCard";
import { createClient } from "@/lib/supabase/client";
import { Plus } from "lucide-react";

interface Campaign {
  id: string;
  name: string;
  target_subreddits: string[];
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
}

export default function DraftsPage() {
  const params = useParams();
  const router = useRouter();
  const campaignId = params?.id as string;

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [filteredDrafts, setFilteredDrafts] = useState<Draft[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [subredditFilter, setSubredditFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch campaign and drafts
  useEffect(() => {
    async function loadData() {
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();

        if (!session) {
          router.push("/login");
          return;
        }

        // Fetch campaign
        const campaignResponse = await fetch(`/api/campaigns/${campaignId}`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        if (!campaignResponse.ok) {
          throw new Error("Failed to load campaign");
        }

        const campaignData = await campaignResponse.json();
        setCampaign({
          id: campaignData.id,
          name: campaignData.name,
          target_subreddits: campaignData.target_subreddits || [],
        });

        // Fetch drafts
        const draftsResponse = await fetch(`/api/campaigns/${campaignId}/drafts`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        if (draftsResponse.ok) {
          const draftsData = await draftsResponse.json();
          setDrafts(draftsData);
          setFilteredDrafts(draftsData);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [campaignId, router]);

  // Apply filters
  useEffect(() => {
    let filtered = drafts;

    if (statusFilter !== "all") {
      filtered = filtered.filter((draft) => draft.status === statusFilter);
    }

    if (subredditFilter !== "all") {
      filtered = filtered.filter((draft) => draft.subreddit === subredditFilter);
    }

    setFilteredDrafts(filtered);
  }, [drafts, statusFilter, subredditFilter]);

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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Drafts</h2>
          <p className="text-muted-foreground">{campaign.name}</p>
        </div>
        <Button onClick={() => router.push(`/dashboard/campaigns/${campaignId}/drafts/new`)}>
          <Plus className="h-4 w-4 mr-2" />
          Generate Draft
        </Button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm font-medium text-red-800">Error</p>
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Filter Drafts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            {/* Status Filter */}
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Status</label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="ready">Ready</SelectItem>
                  <SelectItem value="discarded">Discarded</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Subreddit Filter */}
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Subreddit</label>
              <Select value={subredditFilter} onValueChange={setSubredditFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All subreddits" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  {campaign.target_subreddits.map((subreddit) => (
                    <SelectItem key={subreddit} value={subreddit}>
                      r/{subreddit}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Empty State */}
      {filteredDrafts.length === 0 && (
        <Card>
          <CardContent className="pt-6 text-center">
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">No drafts found</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {drafts.length === 0
                    ? "Generate your first draft to get started"
                    : "Try adjusting your filters"}
                </p>
              </div>
              {drafts.length === 0 && (
                <Button onClick={() => router.push(`/dashboard/campaigns/${campaignId}/drafts/new`)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Generate First Draft
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Draft Grid */}
      {filteredDrafts.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredDrafts.map((draft) => (
            <DraftCard key={draft.id} draft={draft} />
          ))}
        </div>
      )}
    </div>
  );
}
