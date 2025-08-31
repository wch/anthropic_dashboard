import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useShinyOutput } from "shiny-react";
import { TrendingUp, Zap, DollarSign, Activity, Cpu } from "lucide-react";
import { ErrorState } from "../ErrorState";

export function StatsCards() {
  // Connect to Shiny outputs for Anthropic API KPI data
  const [totalTokens] = useShinyOutput<string>("total_tokens", "0");
  const [totalCost] = useShinyOutput<string>("total_cost", "$0.00");
  const [activeModels] = useShinyOutput<string>("active_models", "0");
  const [apiCalls] = useShinyOutput<string>("api_calls", "0");
  
  // Check API status to determine if we should show error state
  const [apiStatus] = useShinyOutput<{
    status: string;
    message: string;
    last_update: string;
  }>("api_status", undefined);

  // Format numbers for display
  const formatNumber = (value: string | undefined) => {
    if (!value) return "0";
    const num = parseFloat(value);
    if (isNaN(num)) return "0";
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const stats = [
    {
      title: "Total Tokens",
      value: formatNumber(totalTokens),
      change: "+15.2%",
      icon: Zap,
      trend: "up" as const,
      description: "Input + Output tokens"
    },
    {
      title: "Total Cost",
      value: totalCost && totalCost.startsWith("$") ? totalCost : `$${totalCost || "0.00"}`,
      change: "+8.7%",
      icon: DollarSign,
      trend: "up" as const,
      description: "Current period spending"
    },
    {
      title: "Active Models",
      value: activeModels,
      change: "+2",
      icon: Cpu,
      trend: "up" as const,
      description: "Models in use"
    },
    {
      title: "API Calls",
      value: formatNumber(apiCalls),
      change: "+12.3%",
      icon: Activity,
      trend: "up" as const,
      description: "Total requests made"
    },
  ];

  // Show error state if API is in error state and all values are defaults/zeros
  if (apiStatus?.status === "error" && 
      totalTokens === "0" && 
      totalCost === "$0.00" && 
      activeModels === "0" && 
      apiCalls === "0") {
    return (
      <ErrorState 
        title="Statistics Unavailable"
        message={apiStatus.message}
        showDemoModeButton={true}
        showRetryButton={true}
      />
    );
  }

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
                <span className="text-muted-foreground">from last period</span>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}