import { LayoutDashboard, Target } from "lucide-react";

export interface NavItem {
  title: string;
  href: string;
  icon: any;
}

export const navItems: NavItem[] = [
  {
    title: "Overview",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    title: "Campaigns",
    href: "/dashboard/campaigns",
    icon: Target,
  },
  // Future phases:
  // { title: "Collect", href: "/dashboard/collect", icon: Search },
  // { title: "Analyze", href: "/dashboard/analyze", icon: BarChart3 },
  // { title: "Generate", href: "/dashboard/generate", icon: Sparkles },
  // { title: "Monitor", href: "/dashboard/monitor", icon: Bell },
];
