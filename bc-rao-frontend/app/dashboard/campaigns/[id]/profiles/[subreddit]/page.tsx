import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ISCGauge from "@/components/analysis/ISCGauge";
import ArchetypePie from "@/components/analysis/ArchetypePie";

interface CommunityProfile {
  id: string;
  subreddit: string;
  isc_score: number;
  isc_tier: string;
  avg_sentence_length: number | null;
  dominant_tone: string | null;
  formality_level: number | null;
  top_success_hooks: string[];
  forbidden_patterns: Record<string, number>;
  archetype_distribution: Record<string, number>;
  sample_size: number;
  last_analyzed_at: string;
}

async function getProfile(campaignId: string, subreddit: string, accessToken: string) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";
  const url = `${apiUrl}/analysis/campaigns/${campaignId}/community-profile?subreddit=${encodeURIComponent(subreddit)}`;

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
    throw new Error(`Failed to fetch profile: ${response.statusText}`);
  }

  return await response.json();
}

export default async function SubredditProfilePage({
  params,
}: {
  params: Promise<{ id: string; subreddit: string }>;
}) {
  const { id, subreddit } = await params;
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
    .select("id, name")
    .eq("id", id)
    .eq("user_id", user.id)
    .single();

  if (!campaign) {
    redirect("/dashboard/campaigns");
  }

  // Fetch profile
  let profile: CommunityProfile | null = null;
  try {
    profile = await getProfile(id, subreddit, session.access_token);
  } catch (error) {
    console.error("Error fetching profile:", error);
  }

  // Profile not found or insufficient data
  if (!profile) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Link
            href={`/dashboard/campaigns/${id}/profiles`}
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Profiles
          </Link>
        </div>

        <div>
          <h1 className="text-2xl font-semibold">r/{subreddit} Community Profile</h1>
        </div>

        <div className="rounded-lg border border-dashed bg-muted/50 p-12 text-center">
          <div className="mx-auto max-w-md space-y-4">
            <div className="text-5xl">⚠️</div>
            <div>
              <h2 className="text-lg font-semibold">Need More Data</h2>
              <p className="text-sm text-muted-foreground mt-2">
                This subreddit has insufficient data for profile generation.
                At least 10 high-quality posts are required for statistical validity.
              </p>
            </div>
            <Link
              href={`/dashboard/campaigns/${id}/collect`}
              className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Collect More Posts
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Transform archetype distribution for chart
  const archetypeData = Object.entries(profile.archetype_distribution).map(([archetype, count]) => ({
    archetype,
    count,
  }));

  // Formality level display
  const getFormalityDisplay = (level: number | null): string => {
    if (level === null) return "N/A";
    if (level < 0.33) return "Low";
    if (level < 0.67) return "Medium";
    return "High";
  };

  // Severity colors for forbidden patterns
  const getSeverityColor = (count: number): string => {
    if (count === 0) return "bg-green-100 text-green-700";
    if (count < 5) return "bg-yellow-100 text-yellow-700";
    if (count < 10) return "bg-orange-100 text-orange-700";
    return "bg-red-100 text-red-700";
  };

  return (
    <div className="space-y-6">
      {/* Header with back link */}
      <div className="flex items-center gap-4">
        <Link
          href={`/dashboard/campaigns/${id}/profiles`}
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Profiles
        </Link>
      </div>

      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-semibold">r/{profile.subreddit} Community Profile</h1>
        <p className="text-muted-foreground mt-1">
          Based on {profile.sample_size} analyzed posts
        </p>
      </div>

      {/* Tabbed Content */}
      <Tabs defaultValue="summary" className="w-full">
        <TabsList>
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="archetypes">Archetypes</TabsTrigger>
          <TabsTrigger value="rhythm">Rhythm</TabsTrigger>
          <TabsTrigger value="forbidden">Forbidden Patterns</TabsTrigger>
        </TabsList>

        {/* Summary Tab */}
        <TabsContent value="summary" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* ISC Gauge */}
            <div className="rounded-lg border p-6">
              <h3 className="text-sm font-medium mb-4">ISC Score</h3>
              <ISCGauge score={profile.isc_score} tier={profile.isc_tier} />
            </div>

            {/* Key Metrics */}
            <div className="rounded-lg border p-6">
              <h3 className="text-sm font-medium mb-4">Key Metrics</h3>
              <div className="space-y-4">
                <div>
                  <p className="text-xs text-muted-foreground">Dominant Tone</p>
                  <p className="text-lg font-semibold">{profile.dominant_tone || "N/A"}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Formality Level</p>
                  <p className="text-lg font-semibold">{getFormalityDisplay(profile.formality_level)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Avg Sentence Length</p>
                  <p className="text-lg font-semibold">
                    {profile.avg_sentence_length ? `${profile.avg_sentence_length.toFixed(1)} words` : "N/A"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Sample Size</p>
                  <p className="text-lg font-semibold">{profile.sample_size} posts</p>
                </div>
              </div>
            </div>
          </div>

          {/* Top Success Hooks */}
          <div className="rounded-lg border p-6">
            <h3 className="text-sm font-medium mb-4">Top Success Hooks</h3>
            {profile.top_success_hooks.length > 0 ? (
              <ul className="space-y-2">
                {profile.top_success_hooks.map((hook, idx) => (
                  <li key={idx} className="text-sm border-l-2 border-primary pl-3">
                    {hook}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">No success hooks identified yet.</p>
            )}
          </div>
        </TabsContent>

        {/* Archetypes Tab */}
        <TabsContent value="archetypes" className="space-y-6 mt-6">
          <div className="rounded-lg border p-6">
            <h3 className="text-sm font-medium mb-4">Archetype Distribution</h3>
            <ArchetypePie distribution={archetypeData} />
          </div>

          {/* Archetype Breakdown */}
          <div className="rounded-lg border p-6">
            <h3 className="text-sm font-medium mb-4">Archetype Details</h3>
            <div className="space-y-3">
              {archetypeData.map((item) => (
                <div key={item.archetype} className="flex items-center justify-between border-b pb-2">
                  <span className="text-sm font-medium">{item.archetype}</span>
                  <span className="text-sm text-muted-foreground">{item.count} posts</span>
                </div>
              ))}
            </div>
          </div>
        </TabsContent>

        {/* Rhythm Tab */}
        <TabsContent value="rhythm" className="space-y-6 mt-6">
          <div className="rounded-lg border p-6">
            <h3 className="text-sm font-medium mb-4">Sentence Analysis</h3>
            <div className="space-y-4">
              <div>
                <p className="text-xs text-muted-foreground">Average Sentence Length</p>
                <p className="text-2xl font-bold">
                  {profile.avg_sentence_length ? `${profile.avg_sentence_length.toFixed(1)} words` : "N/A"}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Formality Level</p>
                <p className="text-2xl font-bold">{getFormalityDisplay(profile.formality_level)}</p>
                {profile.formality_level !== null && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Score: {(profile.formality_level * 100).toFixed(0)}%
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Formality Context */}
          <div className="rounded-lg border bg-muted/50 p-4">
            <p className="text-sm text-muted-foreground">
              Formality level indicates the tone of successful posts. Low formality suggests casual, conversational
              content performs well. High formality suggests more professional, structured content is expected.
            </p>
          </div>
        </TabsContent>

        {/* Forbidden Patterns Tab */}
        <TabsContent value="forbidden" className="space-y-6 mt-6">
          <div className="rounded-lg border p-6">
            <h3 className="text-sm font-medium mb-4">Pattern Categories</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(profile.forbidden_patterns).map(([category, count]) => (
                <div key={category} className="flex items-center justify-between rounded-lg border p-4">
                  <span className="text-sm font-medium">{category}</span>
                  <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${getSeverityColor(count)}`}>
                    {count} occurrences
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Link to blacklist page */}
          <div className="rounded-lg border bg-muted/50 p-4">
            <p className="text-sm text-muted-foreground">
              These are patterns detected in removed or low-scoring posts. Avoid these patterns in your content.
              For detailed pattern rules, visit the{" "}
              <Link
                href={`/dashboard/campaigns/${id}/blacklist`}
                className="font-medium text-foreground underline"
              >
                Blacklist page
              </Link>
              .
            </p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
