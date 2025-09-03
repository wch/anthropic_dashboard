import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useShinyOutput } from "@posit/shiny-react";
import { Activity, Cpu, DollarSign, Info, Zap } from "lucide-react";
import React from "react";
import { ErrorState } from "../ErrorState";

export function StatsCards() {
  // Connect to Shiny outputs for Anthropic API KPI data
  const [totalTokens] = useShinyOutput<string>("total_tokens", "0");
  const [totalCost] = useShinyOutput<string>("total_cost", "$0.00");
  const [activeModels] = useShinyOutput<string>("active_models", "0");
  const [apiCalls] = useShinyOutput<string>("api_calls", "0");

  // Get current filter state to show warnings
  const [currentFilters] = useShinyOutput<{
    workspace_id: string;
    api_key_id: string;
    model: string;
    granularity: string;
  }>("current_filters", {
    workspace_id: "all",
    api_key_id: "all",
    model: "all",
    granularity: "1d",
  });

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

  const showApiKeyWarning = currentFilters?.api_key_id !== "all";

  const stats = [
    {
      title: "Total Tokens",
      value: formatNumber(totalTokens),
      icon: Zap,
      description: "Input + Output tokens",
    },
    {
      title: "Total Cost",
      value: showApiKeyWarning
        ? "Not available for individual key"
        : totalCost && totalCost.startsWith("$")
          ? totalCost
          : `$${totalCost || "0.00"}`,
      icon: DollarSign,
      description: showApiKeyWarning
        ? "Cost data is workspace-level only"
        : "Current period spending",
      showInfoPopover: showApiKeyWarning,
    },
    {
      title: "Active Models",
      value: activeModels,
      icon: Cpu,
      description: "Models in use",
    },
    {
      title: "API Calls",
      value: formatNumber(apiCalls),
      icon: Activity,
      description: "Total requests made",
    },
  ];

  // Show error state if API is in error state and all values are defaults/zeros
  if (
    apiStatus?.status === "error" &&
    totalTokens === "0" &&
    totalCost === "$0.00" &&
    activeModels === "0" &&
    apiCalls === "0"
  ) {
    return (
      <ErrorState
        title='Statistics Unavailable'
        message={apiStatus.message}
        showDemoModeButton={true}
        showRetryButton={true}
      />
    );
  }

  return (
    <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.title}>
            <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
              <CardTitle className='text-sm font-medium flex items-center gap-1'>
                {stat.title}
                {stat.showInfoPopover && (
                  <Popover>
                    <PopoverTrigger asChild>
                      <Info className='h-3 w-3 text-muted-foreground hover:text-foreground cursor-help' />
                    </PopoverTrigger>
                    <PopoverContent className='w-80' align='start'>
                      <div className='space-y-2'>
                        <h4 className='font-medium'>Cost Data Limitation</h4>
                        <p className='text-sm text-muted-foreground'>
                          The Anthropic Cost API doesn't provide cost breakdowns
                          per individual API key. Cost data is only available at
                          the workspace level, so when filtering by a specific
                          API key, we cannot show accurate cost information for
                          just that key.
                        </p>
                        <p className='text-sm text-muted-foreground'>
                          To see cost data, select "All API Keys" or filter by
                          workspace instead.
                        </p>
                      </div>
                    </PopoverContent>
                  </Popover>
                )}
              </CardTitle>
              <Icon className='h-4 w-4 text-muted-foreground' />
            </CardHeader>
            <CardContent>
              <div
                className={`font-bold ${stat.showInfoPopover ? "text-sm text-muted-foreground" : "text-2xl"}`}
              >
                {stat.value}
              </div>
              <p className='text-xs text-muted-foreground'>
                {stat.description}
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
