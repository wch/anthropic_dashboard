import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useShinyOutput } from "shiny-react";
import { TrendingUp, Users, DollarSign, Activity } from "lucide-react";

export function StatsCards() {
  // Connect to Shiny outputs for KPI data
  const [totalUsers] = useShinyOutput<string>("total_users", "0");
  const [totalRevenue] = useShinyOutput<string>("total_revenue", "0");
  const [activeSessions] = useShinyOutput<string>("active_sessions", "0");
  const [conversionRate] = useShinyOutput<string>("conversion_rate", "0");

  // Format numbers for display
  const formatNumber = (value: string | undefined) => {
    if (!value) return "0";
    const num = parseFloat(value);
    if (isNaN(num)) return "0";
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const formatCurrency = (value: string | undefined) => {
    if (!value) return "$0";
    const num = parseFloat(value);
    if (isNaN(num)) return "$0";
    return `$${formatNumber(value)}`;
  };

  const stats = [
    {
      title: "Total Users",
      value: formatNumber(totalUsers),
      change: "+12.5%",
      icon: Users,
      trend: "up" as const,
    },
    {
      title: "Revenue",
      value: formatCurrency(totalRevenue),
      change: "+8.2%",
      icon: DollarSign,
      trend: "up" as const,
    },
    {
      title: "Active Sessions",
      value: formatNumber(activeSessions),
      change: "+3.1%",
      icon: Activity,
      trend: "up" as const,
    },
    {
      title: "Conversion Rate",
      value: `${conversionRate}%`,
      change: "+0.8%",
      icon: TrendingUp,
      trend: "up" as const,
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <div className="flex items-center space-x-2 text-xs">
                <Badge
                  variant={stat.trend === "up" ? "default" : "secondary"}
                  className={`${
                    stat.trend === "up"
                      ? "bg-green-100 text-green-800 hover:bg-green-200"
                      : "bg-red-100 text-red-800 hover:bg-red-200"
                  }`}
                >
                  {stat.change}
                </Badge>
                <span className="text-muted-foreground">from last month</span>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}