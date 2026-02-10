"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { createClient } from "@/lib/supabase/client";
import { apiClient } from "@/lib/api";
import { CampaignForm } from "@/components/forms/campaign-form";
import { ChevronLeft } from "lucide-react";

interface Campaign {
  id: string;
  name: string;
  product_context: string;
  product_url?: string;
  keywords: string[];
  target_subreddits: string[];
}

export default function EditCampaignPage() {
  const router = useRouter();
  const params = useParams();
  const campaignId = params.id as string;
  const [campaign, setCampaign] = useState<Campaign | null>(null);
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
    } catch (error) {
      toast.error("An unexpected error occurred");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
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
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-20 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!campaign) {
    return null;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center gap-2">
        <Link
          href={`/dashboard/campaigns/${campaignId}`}
          className="flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="h-4 w-4" />
          Back to campaign
        </Link>
      </div>

      <div>
        <h1 className="text-3xl font-bold">Edit Campaign</h1>
        <p className="mt-2 text-muted-foreground">
          Update campaign details and targeting settings.
        </p>
      </div>

      <CampaignForm
        mode="edit"
        campaignId={campaignId}
        defaultValues={{
          name: campaign.name,
          product_context: campaign.product_context,
          product_url: campaign.product_url || "",
          keywords: campaign.keywords.join(", "),
          target_subreddits: campaign.target_subreddits,
        }}
      />
    </div>
  );
}
