"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import AnalysisProgress from "./AnalysisProgress";

interface ManualAnalysisTriggerProps {
  campaignId: string;
}

export default function ManualAnalysisTrigger({ campaignId }: ManualAnalysisTriggerProps) {
  const router = useRouter();
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isTriggering, setIsTriggering] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const triggerAnalysis = async () => {
    setIsTriggering(true);
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session?.access_token) {
        toast.error("Authentication required");
        router.push("/login");
        return;
      }

      const response = await fetch(`/api/campaigns/${campaignId}/analyze`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ force_refresh: true }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error?.message || "Failed to start analysis");
      }

      const data = await response.json();
      setTaskId(data.task_id);
      setIsAnalyzing(true);
      toast.success("Analysis started");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to start analysis");
    } finally {
      setIsTriggering(false);
    }
  };

  if (isAnalyzing && taskId) {
    return (
      <div className="w-full max-w-md rounded-lg border bg-card p-4">
        <AnalysisProgress
          campaignId={campaignId}
          taskId={taskId}
          onComplete={() => {
            setIsAnalyzing(false);
            router.refresh();
          }}
        />
      </div>
    );
  }

  return (
    <Button
      onClick={triggerAnalysis}
      disabled={isTriggering}
      variant="outline"
      size="sm"
    >
      {isTriggering ? "Starting..." : "Run Analysis Manually"}
    </Button>
  );
}
