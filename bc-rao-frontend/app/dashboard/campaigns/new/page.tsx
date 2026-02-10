import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { CampaignForm } from "@/components/forms/campaign-form";

export default function NewCampaignPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center gap-2">
        <Link
          href="/dashboard/campaigns"
          className="flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="h-4 w-4" />
          Back to campaigns
        </Link>
      </div>

      <div>
        <h1 className="text-3xl font-bold">Create Campaign</h1>
        <p className="mt-2 text-muted-foreground">
          Set up a new campaign to start collecting community data from Reddit.
        </p>
      </div>

      <CampaignForm mode="create" />
    </div>
  );
}
