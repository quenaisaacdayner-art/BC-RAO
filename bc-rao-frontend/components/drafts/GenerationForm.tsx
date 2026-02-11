"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { AlertCircle } from "lucide-react";
import ISCGatingWarning from "./ISCGatingWarning";

const formSchema = z.object({
  subreddit: z.string().min(1, "Subreddit is required"),
  archetype: z.enum(["Journey", "ProblemSolution", "Feedback"], {
    required_error: "Archetype is required",
  }),
  context: z.string().max(500, "Context must be 500 characters or less").optional(),
});

type FormData = z.infer<typeof formSchema>;

interface CommunityProfile {
  score: number;
  tier: string;
}

interface GenerationFormProps {
  campaignSubreddits: string[];
  iscData: Record<string, CommunityProfile>;
  onSubmit: (data: FormData) => void;
  isGenerating: boolean;
}

/**
 * Single-form generation page with ISC gating
 * - Subreddit dropdown (shows all campaign subreddits, marks unprofiled ones)
 * - Archetype selector (auto-switches to Feedback when ISC > 7.5)
 * - Optional context textarea with character count
 */
export default function GenerationForm({
  campaignSubreddits,
  iscData,
  onSubmit,
  isGenerating,
}: GenerationFormProps) {
  const [selectedSubreddit, setSelectedSubreddit] = useState<string | null>(null);

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      archetype: "Feedback",
      context: "",
    },
  });

  const currentSubreddit = form.watch("subreddit");
  const currentContext = form.watch("context") || "";
  const characterCount = currentContext.length;

  // Check if selected subreddit has a profile
  const hasProfile = currentSubreddit && iscData[currentSubreddit];
  const iscScore = hasProfile ? iscData[currentSubreddit].score : 0;
  const iscTier = hasProfile ? iscData[currentSubreddit].tier : "";
  const isHighISC = iscScore > 7.5;

  // Auto-switch to Feedback when high ISC subreddit is selected
  if (isHighISC && form.getValues("archetype") !== "Feedback") {
    form.setValue("archetype", "Feedback");
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Subreddit Selector */}
        <FormField
          control={form.control}
          name="subreddit"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Target Subreddit</FormLabel>
              <Select
                onValueChange={(value) => {
                  field.onChange(value);
                  setSelectedSubreddit(value);
                }}
                value={field.value}
              >
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a subreddit" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {campaignSubreddits.map((subreddit) => {
                    const hasProfile = !!iscData[subreddit];
                    return (
                      <SelectItem key={subreddit} value={subreddit}>
                        r/{subreddit} {!hasProfile && "(No profile)"}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Warning for subreddits without profile */}
        {currentSubreddit && !hasProfile && (
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
            <div className="flex gap-3">
              <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-800">No Community Profile</p>
                <p className="text-sm text-yellow-700 mt-1">
                  r/{currentSubreddit} has not been analyzed yet. Generation will use generic defaults with reduced accuracy.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ISC Gating Warning */}
        {currentSubreddit && isHighISC && (
          <ISCGatingWarning
            subreddit={currentSubreddit}
            iscScore={iscScore}
            iscTier={iscTier}
          />
        )}

        {/* Archetype Selector */}
        <FormField
          control={form.control}
          name="archetype"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Archetype</FormLabel>
              <Select
                onValueChange={field.onChange}
                value={field.value}
                disabled={isHighISC}
              >
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select an archetype" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="Journey">
                    Journey
                  </SelectItem>
                  <SelectItem value="ProblemSolution">
                    Problem-Solution
                  </SelectItem>
                  <SelectItem value="Feedback">
                    Feedback
                  </SelectItem>
                </SelectContent>
              </Select>
              <FormDescription>
                {isHighISC
                  ? "Only Feedback archetype available for high sensitivity communities"
                  : "Choose the narrative style for your draft"
                }
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Optional Context */}
        <FormField
          control={form.control}
          name="context"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Additional Context (Optional)</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Any specific points you want to mention in your post..."
                  className="min-h-[120px]"
                  {...field}
                />
              </FormControl>
              <FormDescription>
                <span className={characterCount > 500 ? "text-red-600" : "text-muted-foreground"}>
                  {characterCount}/500 characters
                </span>
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Generate Button */}
        <Button
          type="submit"
          size="lg"
          className="w-full"
          disabled={isGenerating}
        >
          {isGenerating ? "Generating..." : "Generate Draft"}
        </Button>
      </form>
    </Form>
  );
}
