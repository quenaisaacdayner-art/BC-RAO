/**
 * Test suite for campaign-stages.ts
 * Critical: Validates BUG-B01 fix (stage URLs and progression logic)
 */

import { describe, it, expect } from 'vitest'
import {
  computeStages,
  getCurrentStage,
  getStageUrl,
  type CampaignStage,
} from '@/lib/campaign-stages'

describe('campaign-stages', () => {
  const mockCampaignId = 'test-campaign-123'

  describe('getStageUrl', () => {
    it('should return correct URL for Stage 1 (Project Briefing)', () => {
      const url = getStageUrl(1, mockCampaignId)
      expect(url).toBe(`/dashboard/campaigns/${mockCampaignId}/edit`)
    })

    it('should return correct URL for Stage 2 (Strategic Selection)', () => {
      const url = getStageUrl(2, mockCampaignId)
      expect(url).toBe(`/dashboard/campaigns/${mockCampaignId}/collect`)
    })

    it('should return correct URL for Stage 3 (Community Intelligence)', () => {
      const url = getStageUrl(3, mockCampaignId)
      expect(url).toBe(`/dashboard/campaigns/${mockCampaignId}/analysis`)
    })

    it('should return correct URL for Stage 4 (Alchemical Transmutation)', () => {
      const url = getStageUrl(4, mockCampaignId)
      expect(url).toBe(`/dashboard/campaigns/${mockCampaignId}/drafts/new`)
    })

    it('should return correct URL for Stage 5 (Deployment & Monitoring)', () => {
      const url = getStageUrl(5, mockCampaignId)
      expect(url).toBe(`/dashboard/campaigns/${mockCampaignId}/monitoring`)
    })

    it('should return campaign overview for invalid stage ID', () => {
      const url = getStageUrl(99, mockCampaignId)
      expect(url).toBe(`/dashboard/campaigns/${mockCampaignId}`)
    })
  })

  describe('computeStages', () => {
    it('should return all 5 stages', () => {
      const campaign = {
        id: mockCampaignId,
        stats: {
          posts_collected: 0,
          drafts_generated: 0,
          monitored_posts: 0,
        },
      }

      const stages = computeStages(campaign, [])
      expect(stages).toHaveLength(5)
      expect(stages.map((s) => s.id)).toEqual([1, 2, 3, 4, 5])
    })

    describe('Stage 1 - Project Briefing', () => {
      it('should be incomplete when campaign has no configuration', () => {
        const campaign = {
          id: mockCampaignId,
          stats: {
            posts_collected: 0,
            drafts_generated: 0,
          },
        }

        const stages = computeStages(campaign, [])
        const stage1 = stages.find((s) => s.id === 1)!

        expect(stage1.completed).toBe(false)
        expect(stage1.active).toBe(true) // Active because not completed
        expect(stage1.locked).toBe(false) // Stage 1 never locked
        expect(stage1.url).toBe(`/dashboard/campaigns/${mockCampaignId}/edit`)
      })

      it('should be complete when campaign has product_context, keywords, and subreddits', () => {
        const campaign = {
          id: mockCampaignId,
          product_context: 'Test product',
          keywords: ['test', 'keywords'],
          target_subreddits: ['test_subreddit'],
          stats: {
            posts_collected: 0,
            drafts_generated: 0,
          },
        }

        const stages = computeStages(campaign, [])
        const stage1 = stages.find((s) => s.id === 1)!

        expect(stage1.completed).toBe(true)
        expect(stage1.active).toBe(false) // Not active when completed
      })

      it('should be incomplete when missing any required field', () => {
        const testCases = [
          {
            id: mockCampaignId,
            // Missing product_context
            keywords: ['test'],
            target_subreddits: ['test'],
            stats: { posts_collected: 0, drafts_generated: 0 },
          },
          {
            id: mockCampaignId,
            product_context: 'Test',
            // Missing keywords
            target_subreddits: ['test'],
            stats: { posts_collected: 0, drafts_generated: 0 },
          },
          {
            id: mockCampaignId,
            product_context: 'Test',
            keywords: ['test'],
            // Missing target_subreddits
            stats: { posts_collected: 0, drafts_generated: 0 },
          },
        ]

        testCases.forEach((campaign) => {
          const stages = computeStages(campaign, [])
          const stage1 = stages.find((s) => s.id === 1)!
          expect(stage1.completed).toBe(false)
        })
      })
    })

    describe('Stage 2 - Strategic Selection', () => {
      it('should be locked when Stage 1 is incomplete', () => {
        const campaign = {
          id: mockCampaignId,
          // Stage 1 incomplete
          stats: {
            posts_collected: 0,
            drafts_generated: 0,
          },
        }

        const stages = computeStages(campaign, [])
        const stage2 = stages.find((s) => s.id === 2)!

        expect(stage2.locked).toBe(true)
        expect(stage2.active).toBe(false)
        expect(stage2.completed).toBe(false)
      })

      it('should be unlocked and active when Stage 1 is complete but Stage 2 is not', () => {
        const campaign = {
          id: mockCampaignId,
          product_context: 'Test product',
          keywords: ['test'],
          target_subreddits: ['test'],
          stats: {
            posts_collected: 0, // Stage 2 not complete
            drafts_generated: 0,
          },
        }

        const stages = computeStages(campaign, [])
        const stage2 = stages.find((s) => s.id === 2)!

        expect(stage2.locked).toBe(false)
        expect(stage2.active).toBe(true)
        expect(stage2.completed).toBe(false)
        expect(stage2.url).toBe(`/dashboard/campaigns/${mockCampaignId}/collect`)
      })

      it('should be complete when posts are collected', () => {
        const campaign = {
          id: mockCampaignId,
          product_context: 'Test product',
          keywords: ['test'],
          target_subreddits: ['test'],
          stats: {
            posts_collected: 5, // Stage 2 complete
            drafts_generated: 0,
          },
        }

        const stages = computeStages(campaign, [])
        const stage2 = stages.find((s) => s.id === 2)!

        expect(stage2.completed).toBe(true)
        expect(stage2.active).toBe(false)
      })
    })

    describe('Stage 3 - Community Intelligence', () => {
      it('should be locked when Stage 2 is incomplete', () => {
        const campaign = {
          id: mockCampaignId,
          product_context: 'Test',
          keywords: ['test'],
          target_subreddits: ['test'],
          stats: {
            posts_collected: 0, // Stage 2 incomplete
            drafts_generated: 0,
          },
        }

        const stages = computeStages(campaign, [])
        const stage3 = stages.find((s) => s.id === 3)!

        expect(stage3.locked).toBe(true)
        expect(stage3.active).toBe(false)
      })

      it('should be unlocked and active when Stage 2 is complete but Stage 3 is not', () => {
        const campaign = {
          id: mockCampaignId,
          product_context: 'Test',
          keywords: ['test'],
          target_subreddits: ['test'],
          stats: {
            posts_collected: 5, // Stage 2 complete
            drafts_generated: 0,
          },
        }

        const stages = computeStages(campaign, []) // No profiles = Stage 3 incomplete

        const stage3 = stages.find((s) => s.id === 3)!

        expect(stage3.locked).toBe(false)
        expect(stage3.active).toBe(true)
        expect(stage3.completed).toBe(false)
        expect(stage3.url).toBe(`/dashboard/campaigns/${mockCampaignId}/analysis`)
      })

      it('should be complete when profiles exist', () => {
        const campaign = {
          id: mockCampaignId,
          product_context: 'Test',
          keywords: ['test'],
          target_subreddits: ['test'],
          stats: {
            posts_collected: 5,
            drafts_generated: 0,
          },
        }

        const profiles = [
          { id: 'profile-1', subreddit: 'test_subreddit' },
        ]

        const stages = computeStages(campaign, profiles)
        const stage3 = stages.find((s) => s.id === 3)!

        expect(stage3.completed).toBe(true)
        expect(stage3.active).toBe(false)
      })
    })

    describe('Stage 4 - Alchemical Transmutation', () => {
      it('should be locked when Stage 3 is incomplete', () => {
        const campaign = {
          id: mockCampaignId,
          product_context: 'Test',
          keywords: ['test'],
          target_subreddits: ['test'],
          stats: {
            posts_collected: 5,
            drafts_generated: 0,
          },
        }

        const stages = computeStages(campaign, []) // No profiles = Stage 3 incomplete

        const stage4 = stages.find((s) => s.id === 4)!

        expect(stage4.locked).toBe(true)
        expect(stage4.active).toBe(false)
      })

      it('should be unlocked and active when Stage 3 is complete but Stage 4 is not', () => {
        const campaign = {
          id: mockCampaignId,
          product_context: 'Test',
          keywords: ['test'],
          target_subreddits: ['test'],
          stats: {
            posts_collected: 5,
            drafts_generated: 0, // Stage 4 not complete
          },
        }

        const profiles = [{ id: 'profile-1', subreddit: 'test' }]

        const stages = computeStages(campaign, profiles)
        const stage4 = stages.find((s) => s.id === 4)!

        expect(stage4.locked).toBe(false)
        expect(stage4.active).toBe(true)
        expect(stage4.completed).toBe(false)
        expect(stage4.url).toBe(`/dashboard/campaigns/${mockCampaignId}/drafts/new`)
      })

      it('should be complete when drafts are generated', () => {
        const campaign = {
          id: mockCampaignId,
          product_context: 'Test',
          keywords: ['test'],
          target_subreddits: ['test'],
          stats: {
            posts_collected: 5,
            drafts_generated: 3, // Stage 4 complete
          },
        }

        const profiles = [{ id: 'profile-1', subreddit: 'test' }]

        const stages = computeStages(campaign, profiles)
        const stage4 = stages.find((s) => s.id === 4)!

        expect(stage4.completed).toBe(true)
        expect(stage4.active).toBe(false)
      })
    })

    describe('Stage 5 - Deployment & Monitoring', () => {
      it('should be locked when Stage 4 is incomplete', () => {
        const campaign = {
          id: mockCampaignId,
          product_context: 'Test',
          keywords: ['test'],
          target_subreddits: ['test'],
          stats: {
            posts_collected: 5,
            drafts_generated: 0, // Stage 4 incomplete
          },
        }

        const profiles = [{ id: 'profile-1', subreddit: 'test' }]

        const stages = computeStages(campaign, profiles)
        const stage5 = stages.find((s) => s.id === 5)!

        expect(stage5.locked).toBe(true)
        expect(stage5.active).toBe(false)
      })

      it('should be unlocked and active when Stage 4 is complete but Stage 5 is not', () => {
        const campaign = {
          id: mockCampaignId,
          product_context: 'Test',
          keywords: ['test'],
          target_subreddits: ['test'],
          stats: {
            posts_collected: 5,
            drafts_generated: 3,
            monitored_posts: 0, // Stage 5 not complete
          },
        }

        const profiles = [{ id: 'profile-1', subreddit: 'test' }]

        const stages = computeStages(campaign, profiles)
        const stage5 = stages.find((s) => s.id === 5)!

        expect(stage5.locked).toBe(false)
        expect(stage5.active).toBe(true)
        expect(stage5.completed).toBe(false)
        expect(stage5.url).toBe(`/dashboard/campaigns/${mockCampaignId}/monitoring`)
      })

      it('should be complete when posts are being monitored', () => {
        const campaign = {
          id: mockCampaignId,
          product_context: 'Test',
          keywords: ['test'],
          target_subreddits: ['test'],
          stats: {
            posts_collected: 5,
            drafts_generated: 3,
            monitored_posts: 2, // Stage 5 complete
          },
        }

        const profiles = [{ id: 'profile-1', subreddit: 'test' }]

        const stages = computeStages(campaign, profiles)
        const stage5 = stages.find((s) => s.id === 5)!

        expect(stage5.completed).toBe(true)
        expect(stage5.active).toBe(false)
      })
    })
  })

  describe('getCurrentStage', () => {
    it('should return 1 when Stage 1 is active', () => {
      const stages: CampaignStage[] = [
        {
          id: 1,
          name: 'Stage 1',
          description: 'Test',
          completed: false,
          active: true,
          url: '/test',
          locked: false,
        },
        {
          id: 2,
          name: 'Stage 2',
          description: 'Test',
          completed: false,
          active: false,
          url: '/test',
          locked: true,
        },
      ]

      expect(getCurrentStage(stages)).toBe(1)
    })

    it('should return 3 when Stage 3 is active', () => {
      const stages: CampaignStage[] = [
        {
          id: 1,
          name: 'Stage 1',
          description: 'Test',
          completed: true,
          active: false,
          url: '/test',
          locked: false,
        },
        {
          id: 2,
          name: 'Stage 2',
          description: 'Test',
          completed: true,
          active: false,
          url: '/test',
          locked: false,
        },
        {
          id: 3,
          name: 'Stage 3',
          description: 'Test',
          completed: false,
          active: true,
          url: '/test',
          locked: false,
        },
      ]

      expect(getCurrentStage(stages)).toBe(3)
    })

    it('should return 5 when all stages are complete (no active stage)', () => {
      const stages: CampaignStage[] = [
        {
          id: 1,
          name: 'Stage 1',
          description: 'Test',
          completed: true,
          active: false,
          url: '/test',
          locked: false,
        },
        {
          id: 2,
          name: 'Stage 2',
          description: 'Test',
          completed: true,
          active: false,
          url: '/test',
          locked: false,
        },
        {
          id: 3,
          name: 'Stage 3',
          description: 'Test',
          completed: true,
          active: false,
          url: '/test',
          locked: false,
        },
        {
          id: 4,
          name: 'Stage 4',
          description: 'Test',
          completed: true,
          active: false,
          url: '/test',
          locked: false,
        },
        {
          id: 5,
          name: 'Stage 5',
          description: 'Test',
          completed: true,
          active: false,
          url: '/test',
          locked: false,
        },
      ]

      expect(getCurrentStage(stages)).toBe(5)
    })
  })

  describe('Integration: Full stage progression', () => {
    it('should correctly compute stages as campaign progresses through all stages', () => {
      const mockProfiles = [{ id: 'profile-1', subreddit: 'test' }]

      // Initial state - nothing complete
      const campaign1 = {
        id: mockCampaignId,
        stats: {
          posts_collected: 0,
          drafts_generated: 0,
          monitored_posts: 0,
        },
      }
      const stages1 = computeStages(campaign1, [])
      expect(getCurrentStage(stages1)).toBe(1)
      expect(stages1[0].locked).toBe(false)
      expect(stages1[1].locked).toBe(true)

      // Stage 1 complete
      const campaign2 = {
        ...campaign1,
        product_context: 'Test',
        keywords: ['test'],
        target_subreddits: ['test'],
      }
      const stages2 = computeStages(campaign2, [])
      expect(getCurrentStage(stages2)).toBe(2)
      expect(stages2[0].completed).toBe(true)
      expect(stages2[1].locked).toBe(false)
      expect(stages2[2].locked).toBe(true)

      // Stage 2 complete
      const campaign3 = {
        ...campaign2,
        stats: {
          posts_collected: 10,
          drafts_generated: 0,
          monitored_posts: 0,
        },
      }
      const stages3 = computeStages(campaign3, [])
      expect(getCurrentStage(stages3)).toBe(3)
      expect(stages3[1].completed).toBe(true)
      expect(stages3[2].locked).toBe(false)
      expect(stages3[3].locked).toBe(true)

      // Stage 3 complete
      const stages4 = computeStages(campaign3, mockProfiles)
      expect(getCurrentStage(stages4)).toBe(4)
      expect(stages4[2].completed).toBe(true)
      expect(stages4[3].locked).toBe(false)
      expect(stages4[4].locked).toBe(true)

      // Stage 4 complete
      const campaign5 = {
        ...campaign3,
        stats: {
          posts_collected: 10,
          drafts_generated: 5,
          monitored_posts: 0,
        },
      }
      const stages5 = computeStages(campaign5, mockProfiles)
      expect(getCurrentStage(stages5)).toBe(5)
      expect(stages5[3].completed).toBe(true)
      expect(stages5[4].locked).toBe(false)

      // All complete
      const campaign6 = {
        ...campaign5,
        stats: {
          posts_collected: 10,
          drafts_generated: 5,
          monitored_posts: 3,
        },
      }
      const stages6 = computeStages(campaign6, mockProfiles)
      expect(getCurrentStage(stages6)).toBe(5)
      expect(stages6[4].completed).toBe(true)
    })
  })
})
