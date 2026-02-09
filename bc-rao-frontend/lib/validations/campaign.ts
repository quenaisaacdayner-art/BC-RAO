import { z } from "zod";

export const campaignSchema = z.object({
  name: z
    .string()
    .min(1, "Campaign name is required")
    .max(100, "Campaign name must be less than 100 characters"),
  product_context: z
    .string()
    .min(10, "Product context must be at least 10 characters"),
  product_url: z
    .string()
    .url("Must be a valid URL")
    .or(z.literal(""))
    .optional(),
  keywords: z
    .string()
    .refine(
      (val) => {
        const keywords = val
          .split(",")
          .map((k) => k.trim())
          .filter((k) => k.length > 0);
        return keywords.length >= 5 && keywords.length <= 15;
      },
      { message: "Between 5 and 15 keywords required" }
    ),
  target_subreddits: z
    .array(z.string())
    .min(1, "At least one subreddit required"),
});

export const campaignUpdateSchema = z.object({
  name: z
    .string()
    .min(1, "Campaign name is required")
    .max(100, "Campaign name must be less than 100 characters")
    .optional(),
  product_context: z
    .string()
    .min(10, "Product context must be at least 10 characters")
    .optional(),
  product_url: z
    .string()
    .url("Must be a valid URL")
    .or(z.literal(""))
    .optional(),
  keywords: z
    .string()
    .refine(
      (val) => {
        const keywords = val
          .split(",")
          .map((k) => k.trim())
          .filter((k) => k.length > 0);
        return keywords.length >= 5 && keywords.length <= 15;
      },
      { message: "Between 5 and 15 keywords required" }
    )
    .optional(),
  target_subreddits: z
    .array(z.string())
    .min(1, "At least one subreddit required")
    .optional(),
  status: z.enum(["active", "paused", "archived"]).optional(),
});

export type CampaignFormValues = z.infer<typeof campaignSchema>;
export type CampaignUpdateValues = z.infer<typeof campaignUpdateSchema>;
