"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Check, Lock, ChevronRight } from "lucide-react";
import { CampaignStage } from "@/lib/campaign-stages";
import { cn } from "@/lib/utils";

interface StageIndicatorProps {
  stages: CampaignStage[];
  className?: string;
}

export default function StageIndicator({ stages, className }: StageIndicatorProps) {
  const router = useRouter();
  const prevStagesRef = useRef<CampaignStage[]>([]);

  // Auto-advance toast notification when stage unlocks
  useEffect(() => {
    const prevStages = prevStagesRef.current;

    if (prevStages.length === 0) {
      prevStagesRef.current = stages;
      return;
    }

    // Check if any stage transitioned from locked to active
    stages.forEach((stage, idx) => {
      const prevStage = prevStages[idx];

      if (prevStage && prevStage.locked && stage.active) {
        // Stage just unlocked - show toast
        toast.success(`${stage.name} unlocked!`, {
          description: `You can now continue to the next stage.`,
          action: {
            label: "Continue",
            onClick: () => router.push(stage.url),
          },
          duration: 5000,
        });
      }
    });

    prevStagesRef.current = stages;
  }, [stages, router]);

  const handleStageClick = (stage: CampaignStage) => {
    if (stage.locked) {
      toast.error("Stage locked", {
        description: `Complete previous stages first to unlock ${stage.name}.`,
      });
      return;
    }

    router.push(stage.url);
  };

  return (
    <div className={cn("w-full", className)}>
      {/* Desktop: Horizontal layout */}
      <div className="hidden md:flex items-center justify-between gap-2">
        {stages.map((stage, idx) => (
          <div key={stage.id} className="flex items-center flex-1">
            <button
              onClick={() => handleStageClick(stage)}
              disabled={stage.locked}
              className={cn(
                "flex items-center gap-3 rounded-lg border p-4 transition-all w-full text-left",
                stage.locked && "opacity-50 cursor-not-allowed",
                !stage.locked && "cursor-pointer hover:shadow-md",
                stage.completed && "bg-green-50 dark:bg-green-950/40 border-green-400 dark:border-green-700 ring-1 ring-green-300 dark:ring-green-800",
                stage.active && "bg-blue-50 dark:bg-blue-950/40 border-blue-300 dark:border-blue-700 shadow-sm ring-1 ring-blue-200 dark:ring-blue-800",
                !stage.active && !stage.completed && stage.locked && "bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700"
              )}
            >
              {/* Icon */}
              <div
                className={cn(
                  "flex h-10 w-10 items-center justify-center rounded-full shrink-0",
                  stage.completed && "bg-green-500 text-white",
                  stage.active && "bg-blue-500 text-white animate-pulse",
                  stage.locked && "bg-gray-300 text-gray-600"
                )}
              >
                {stage.completed ? (
                  <Check className="h-5 w-5" />
                ) : stage.locked ? (
                  <Lock className="h-5 w-5" />
                ) : (
                  <span className="text-sm font-bold">{stage.id}</span>
                )}
              </div>

              {/* Text */}
              <div className="flex-1 min-w-0">
                <div className={cn("font-semibold text-sm truncate", stage.completed && "text-green-800")}>{stage.name}</div>
                <div className="text-xs text-muted-foreground truncate">{stage.description}</div>
              </div>
            </button>

            {/* Chevron between stages (except after last) */}
            {idx < stages.length - 1 && (
              <ChevronRight className="h-5 w-5 text-muted-foreground mx-2 shrink-0" />
            )}
          </div>
        ))}
      </div>

      {/* Mobile: Vertical layout */}
      <div className="md:hidden space-y-2">
        {stages.map((stage) => (
          <button
            key={stage.id}
            onClick={() => handleStageClick(stage)}
            disabled={stage.locked}
            className={cn(
              "flex items-center gap-3 rounded-lg border p-4 transition-all w-full text-left",
              stage.locked && "opacity-50 cursor-not-allowed",
              !stage.locked && "cursor-pointer hover:shadow-md",
              stage.completed && "bg-green-50 border-green-400 ring-1 ring-green-300",
              stage.active && "bg-blue-50 border-blue-300 shadow-sm ring-1 ring-blue-200",
              !stage.active && !stage.completed && stage.locked && "bg-gray-50 border-gray-200"
            )}
          >
            {/* Icon */}
            <div
              className={cn(
                "flex h-10 w-10 items-center justify-center rounded-full shrink-0",
                stage.completed && "bg-green-500 text-white",
                stage.active && "bg-blue-500 text-white animate-pulse",
                stage.locked && "bg-gray-300 text-gray-600"
              )}
            >
              {stage.completed ? (
                <Check className="h-5 w-5" />
              ) : stage.locked ? (
                <Lock className="h-5 w-5" />
              ) : (
                <span className="text-sm font-bold">{stage.id}</span>
              )}
            </div>

            {/* Text */}
            <div className="flex-1 min-w-0">
              <div className={cn("font-semibold text-sm", stage.completed && "text-green-800")}>{stage.name}</div>
              <div className="text-xs text-muted-foreground">{stage.description}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
