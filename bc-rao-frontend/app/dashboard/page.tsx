import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default async function OverviewPage() {
  // For now, we assume zero campaigns until we implement the API call
  // In future plans, we'll fetch real campaign data here
  const campaignCount = 0;

  if (campaignCount === 0) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Welcome to BC-RAO</CardTitle>
            <CardDescription>
              Create a campaign to start collecting community data.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild className="w-full">
              <Link href="/dashboard/campaigns/new">Create Campaign</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // When campaigns exist, show overview stats
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Total Campaigns</CardTitle>
            <CardDescription>Active campaigns</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{campaignCount}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Last 7 days</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">0</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Get started</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild className="w-full">
              <Link href="/dashboard/campaigns/new">New Campaign</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
