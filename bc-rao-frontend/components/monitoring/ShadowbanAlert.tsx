"use client";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface ShadowbanAlertProps {
  isOpen: boolean;
  onDismiss: () => void;
  postTitle: string;
  subreddit: string;
  detectedAt: string;
}

export default function ShadowbanAlert({
  isOpen,
  onDismiss,
  postTitle,
  subreddit,
  detectedAt,
}: ShadowbanAlertProps) {
  return (
    <AlertDialog open={isOpen} onOpenChange={(open) => !open && onDismiss()}>
      <AlertDialogContent className="max-w-2xl">
        <AlertDialogHeader>
          <AlertDialogTitle className="text-2xl text-destructive">
            Shadowban Detected
          </AlertDialogTitle>
          <AlertDialogDescription className="text-base">
            Your post has been shadowbanned on r/{subreddit}
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="space-y-4">
          {/* Post Details */}
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
            <p className="font-medium">{postTitle}</p>
            <p className="text-sm text-muted-foreground mt-1">
              Detected: {new Date(detectedAt).toLocaleString()}
            </p>
          </div>

          {/* What This Means */}
          <div>
            <h3 className="font-semibold mb-2">What This Means</h3>
            <p className="text-sm text-muted-foreground">
              Your post appears normal to you, but it's invisible to other users.
              This is Reddit's silent moderation mechanism. The system has
              automatically extracted patterns from this post to prevent similar
              issues in future drafts.
            </p>
          </div>

          {/* Immediate Actions */}
          <div>
            <h3 className="font-semibold mb-2">Immediate Actions</h3>
            <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
              <li>
                <strong>Pause posting to r/{subreddit} for 48 hours</strong> to
                avoid triggering additional filters
              </li>
              <li>
                <strong>Review the extracted patterns</strong> in your blacklist
                to understand what triggered the shadowban
              </li>
              <li>
                <strong>Check your other posts</strong> on this subreddit for
                similar patterns
              </li>
              <li>
                <strong>Don't delete the post</strong> — it won't improve your
                standing and removes evidence
              </li>
            </ol>
          </div>

          {/* Auto-extracted Patterns Note */}
          <div className="bg-muted rounded-lg p-4">
            <p className="text-sm">
              <strong>Good news:</strong> Auto-extracted patterns have been added
              to your blacklist. Future drafts will avoid these issues
              automatically.
            </p>
          </div>
        </div>

        <AlertDialogFooter>
          <AlertDialogAction
            onClick={onDismiss}
            className="bg-destructive hover:bg-destructive/90"
          >
            I Understand — View Dashboard
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
