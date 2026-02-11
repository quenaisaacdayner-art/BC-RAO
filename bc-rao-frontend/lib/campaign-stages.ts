export interface CampaignStage {
  id: 1 | 2 | 3 | 4;
  name: string;
  description: string;
  completed: boolean;
  active: boolean;
  url: string;
  locked: boolean;
}

interface Campaign {
  id: string;
  product_context?: string;
  keywords?: string[];
  target_subreddits?: string[];
  stats: {
    posts_collected: number;
    drafts_generated: number;
  };
}

interface CommunityProfile {
  id: string;
  subreddit: string;
}

/**
 * Compute the 4-stage campaign journey progress
 * Linear progression: each stage must be completed before the next unlocks
 */
export function computeStages(
  campaign: Campaign,
  profiles: CommunityProfile[] = []
): CampaignStage[] {
  const campaignId = campaign.id;

  // Stage 1: Project Briefing - completed when campaign has basic config
  const stage1Complete =
    !!campaign.product_context &&
    (campaign.keywords?.length ?? 0) > 0 &&
    (campaign.target_subreddits?.length ?? 0) > 0;

  // Stage 2: Strategic Selection - completed when posts collected
  const stage2Complete = campaign.stats.posts_collected > 0;

  // Stage 3: Community Intelligence - completed when profiles exist
  const stage3Complete = profiles.length > 0;

  // Stage 4: Alchemical Transmutation - completed when drafts generated
  const stage4Complete = campaign.stats.drafts_generated > 0;

  const stages: CampaignStage[] = [
    {
      id: 1,
      name: "Project Briefing",
      description: "Campaign setup with product context and keywords",
      completed: stage1Complete,
      active: !stage1Complete, // Active if not completed (always accessible)
      url: `/dashboard/campaigns/${campaignId}/edit`,
      locked: false, // Stage 1 never locked
    },
    {
      id: 2,
      name: "Strategic Selection",
      description: "Collect posts from target subreddits",
      completed: stage2Complete,
      active: stage1Complete && !stage2Complete, // Active if Stage 1 done
      url: `/dashboard/campaigns/${campaignId}/collect`,
      locked: !stage1Complete, // Locked until Stage 1 complete
    },
    {
      id: 3,
      name: "Community Intelligence",
      description: "Analyze community profiles and patterns",
      completed: stage3Complete,
      active: stage2Complete && !stage3Complete, // Active if Stage 2 done
      url: `/dashboard/campaigns/${campaignId}/profiles`,
      locked: !stage2Complete, // Locked until Stage 2 complete
    },
    {
      id: 4,
      name: "Alchemical Transmutation",
      description: "Generate drafts with community DNA",
      completed: stage4Complete,
      active: stage3Complete && !stage4Complete, // Active if Stage 3 done
      url: `/dashboard/campaigns/${campaignId}/drafts/new`,
      locked: !stage3Complete, // Locked until Stage 3 complete
    },
  ];

  return stages;
}

/**
 * Get the current active stage (first non-completed stage)
 */
export function getCurrentStage(stages: CampaignStage[]): number {
  const activeStage = stages.find((s) => s.active);
  return activeStage?.id ?? 4; // Default to Stage 4 if all complete
}

/**
 * Get the URL for a specific stage
 */
export function getStageUrl(stageId: number, campaignId: string): string {
  const baseUrls: Record<number, string> = {
    1: `/dashboard/campaigns/${campaignId}/edit`,
    2: `/dashboard/campaigns/${campaignId}/collect`,
    3: `/dashboard/campaigns/${campaignId}/profiles`,
    4: `/dashboard/campaigns/${campaignId}/drafts/new`,
  };

  return baseUrls[stageId] || `/dashboard/campaigns/${campaignId}`;
}
