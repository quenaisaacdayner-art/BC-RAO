import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import Link from "next/link";
import ComparisonTable from "@/components/analysis/ComparisonTable";
import ManualAnalysisTrigger from "@/components/analysis/ManualAnalysisTrigger";

interface CommunityProfile {
  id: string;
  subreddit: string;
  isc_score: number;
  isc_tier: string;
  dominant_tone: string | null;
  formality_level: number | null;
  sample_size: number;
  archetype_distribution: Record<string, number>;
  last_analyzed_at: string;
}

async function getProfiles(campaignId: string, accessToken: string) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";
  const url = `${apiUrl}/analysis/campaigns/${campaignId}/community-profiles`;

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    if (response.status === 404) {
      return null;
    }
    throw new Error(`Failed to fetch profiles: ${response.statusText}`);
  }

  const data = await response.json();
  return data.profiles || [];
}

export default async function CommunityProfilesPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  // Get user's access token
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    redirect("/login");
  }

  // Verify campaign ownership
  const { data: campaign } = await supabase
    .from("campaigns")
    .select("id, name, target_subreddits")
    .eq("id", id)
    .eq("user_id", user.id)
    .single();

  if (!campaign) {
    redirect("/dashboard/campaigns");
  }

  // Fetch community profiles
  let profiles: CommunityProfile[] = [];
  try {
    profiles = (await getProfiles(id, session.access_token)) || [];
  } catch (error) {
    console.error("Error fetching profiles:", error);
  }

  // Empty state - no profiles yet
  if (profiles.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Community Profiles</h1>
          <p className="text-muted-foreground mt-1">
            Intelligence data for {campaign.name}
          </p>
        </div>

        <div className="rounded-lg border border-dashed bg-muted/50 p-12 text-center">
          <div className="mx-auto max-w-md space-y-4">
            <div className="text-5xl">📊</div>
            <div>
              <h2 className="text-lg font-semibold">No Analysis Data Yet</h2>
              <p className="text-sm text-muted-foreground mt-2">
                Community profiles are generated after you collect posts from your target subreddits.
                Analysis automatically starts after collection completes.
              </p>
            </div>
            <div className="flex flex-col items-center gap-3">
              <Link
                href={`/dashboard/campaigns/${id}/collect`}
                className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                Collect Posts
              </Link>
              <p className="text-xs text-muted-foreground">or</p>
              <ManualAnalysisTrigger campaignId={id} />
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Profiles exist - show comparison table
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Community Profiles</h1>
        <p className="text-muted-foreground mt-1">
          Intelligence data for {campaign.name} - {profiles.length} subreddits analyzed
        </p>
      </div>

      <ComparisonTable profiles={profiles} campaignId={id} />

      {/* Legend */}
      <div className="rounded-lg border bg-muted/50 p-4">
        <h3 className="text-sm font-medium mb-2">ISC Score Legend</h3>
        <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full bg-green-500"></span>
            <span>Low (1-3): Relaxed standards</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full bg-yellow-500"></span>
            <span>Moderate (3-5): Balanced moderation</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full bg-orange-500"></span>
            <span>High (5-7): Strict quality control</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full bg-red-500"></span>
            <span>Very High (7-10): Extremely sensitive</span>
          </div>
        </div>
      </div>
    </div>
  );
}
