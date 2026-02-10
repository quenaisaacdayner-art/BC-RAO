"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { createClient } from "@/lib/supabase/client";
import { apiClient } from "@/lib/api";
import { CampaignCard } from "@/components/campaigns/campaign-card";
import { DeleteCampaignDialog } from "@/components/campaigns/delete-campaign-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Plus } from "lucide-react";

interface Campaign {
  id: string;
  name: string;
  status: "active" | "paused" | "archived";
  product_context: string;
  keywords: string[];
  target_subreddits: string[];
  stats?: {
    posts_collected: number;
    drafts_generated: number;
    active_monitors: number;
  };
}

export default function CampaignsPage() {
  const router = useRouter();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
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

      const response = await apiClient.get<{ campaigns: Campaign[]; total: number }>(
        "/campaigns",
        session.access_token
      );

      if (response.error) {
        toast.error(response.error.message || "Failed to fetch campaigns");
        return;
      }

      setCampaigns(response.data?.campaigns || []);
    } catch (error) {
      toast.error("An unexpected error occurred");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteClick = (campaign: Campaign) => {
    setSelectedCampaign(campaign);
    setDeleteDialogOpen(true);
  };

  const handleDeleted = () => {
    setDeleteDialogOpen(false);
    setSelectedCampaign(null);
    fetchCampaigns();
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Campaigns</h1>
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-6 w-2/3 bg-muted rounded" />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="h-4 bg-muted rounded" />
                  <div className="h-4 w-5/6 bg-muted rounded" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (campaigns.length === 0) {
    return (
      <div className="flex h-[calc(100vh-12rem)] items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>No campaigns yet</CardTitle>
            <CardDescription>
              Campaigns organize your Reddit research by product. Create a campaign to
              start collecting community data.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild className="w-full">
              <Link href="/dashboard/campaigns/new">
                <Plus className="mr-2 h-4 w-4" />
                Create your first campaign
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Campaigns</h1>
        <Button asChild>
          <Link href="/dashboard/campaigns/new">
            <Plus className="mr-2 h-4 w-4" />
            New Campaign
          </Link>
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {campaigns.map((campaign) => (
          <CampaignCard
            key={campaign.id}
            campaign={campaign}
            onDelete={() => handleDeleteClick(campaign)}
          />
        ))}
      </div>

      {selectedCampaign && deleteDialogOpen && (
        <DeleteCampaignDialog
          campaignId={selectedCampaign.id}
          campaignName={selectedCampaign.name}
          trigger={null}
          onDeleted={handleDeleted}
        />
      )}
    </div>
  );
}
