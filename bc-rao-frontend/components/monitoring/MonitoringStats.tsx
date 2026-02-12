import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface MonitoringStatsProps {
  stats: {
    active_count: number;
    removed_count: number;
    shadowbanned_count: number;
    total_count: number;
    success_rate: number;
  };
}

export default function MonitoringStats({ stats }: MonitoringStatsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {/* Active Posts */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Active
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600">
            {stats.active_count}
          </div>
        </CardContent>
      </Card>

      {/* Removed Posts */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Removed
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-secondary-foreground">
            {stats.removed_count}
          </div>
        </CardContent>
      </Card>

      {/* Shadowbanned Posts */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Shadowbanned
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-destructive">
            {stats.shadowbanned_count}
          </div>
        </CardContent>
      </Card>

      {/* Success Rate */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Success Rate
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {stats.success_rate.toFixed(1)}%
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {stats.active_count} of {stats.total_count} posts live
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
