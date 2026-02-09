"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { createClient } from "@/lib/supabase/client";
import { apiClient } from "@/lib/api";
import { campaignSchema, type CampaignFormValues } from "@/lib/validations/campaign";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { SubredditAutocomplete } from "./subreddit-autocomplete";

interface CampaignFormProps {
  mode: "create" | "edit";
  defaultValues?: Partial<CampaignFormValues>;
  campaignId?: string;
}

export function CampaignForm({
  mode,
  defaultValues,
  campaignId,
}: CampaignFormProps) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<CampaignFormValues>({
    resolver: zodResolver(campaignSchema),
    defaultValues: defaultValues || {
      name: "",
      product_context: "",
      product_url: "",
      keywords: "",
      target_subreddits: [],
    },
  });

  const onSubmit = async (data: CampaignFormValues) => {
    setIsSubmitting(true);

    try {
      // Get Supabase JWT token
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        toast.error("Authentication required. Please log in again.");
        router.push("/login");
        return;
      }

      // Parse keywords
      const keywords = data.keywords
        .split(",")
        .map((k) => k.trim())
        .filter((k) => k.length > 0);

      const payload = {
        name: data.name,
        product_context: data.product_context,
        product_url: data.product_url || "",
        keywords,
        target_subreddits: data.target_subreddits,
      };

      if (mode === "create") {
        // Create campaign
        const response = await apiClient.post(
          "/campaigns",
          payload,
          session.access_token
        );

        if (response.error) {
          toast.error(response.error.message || "Failed to create campaign");
          return;
        }

        toast.success("Campaign created successfully");
        router.push("/dashboard/campaigns");
      } else {
        // Update campaign
        if (!campaignId) {
          toast.error("Campaign ID is required for updates");
          return;
        }

        const response = await apiClient.patch(
          `/campaigns/${campaignId}`,
          payload,
          session.access_token
        );

        if (response.error) {
          toast.error(response.error.message || "Failed to update campaign");
          return;
        }

        toast.success("Campaign updated successfully");
        router.push(`/dashboard/campaigns/${campaignId}`);
      }
    } catch (error) {
      toast.error("An unexpected error occurred");
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Campaign Name</FormLabel>
              <FormControl>
                <Input placeholder="My SaaS Campaign" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="product_context"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Product Context</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Describe your product, target audience, and value proposition"
                  rows={4}
                  {...field}
                />
              </FormControl>
              <FormDescription>
                Describe your product, target audience, and value proposition
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="product_url"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Product URL (Optional)</FormLabel>
              <FormControl>
                <Input
                  type="url"
                  placeholder="https://yourproduct.com"
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="keywords"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Keywords</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="saas, startup, growth, marketing, tools"
                  rows={2}
                  {...field}
                />
              </FormControl>
              <FormDescription>
                Comma-separated, 5-15 required
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="target_subreddits"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Target Subreddits</FormLabel>
              <FormControl>
                <SubredditAutocomplete
                  selected={field.value}
                  onSelect={field.onChange}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.back()}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting
              ? mode === "create"
                ? "Creating..."
                : "Saving..."
              : mode === "create"
              ? "Create Campaign"
              : "Save Changes"}
          </Button>
        </div>
      </form>
    </Form>
  );
}
