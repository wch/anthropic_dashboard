import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useShinyOutput } from "shiny-react";
import { ErrorState } from "../ErrorState";

interface TokenUsageData {
  date: string;
  input_tokens: number;
  output_tokens: number;
}

interface CostByModelData {
  model: string;
  cost: number;
}

interface ServiceTierData {
  service_tier: string;
  tokens: number;
}

const COLORS = [
  "#0088FE",
  "#00C49F",
  "#FFBB28",
  "#FF8042",
  "#8884D8",
  "#82CA9D",
];

export function ChartsSection() {
  // Connect to Shiny outputs for Anthropic API chart data
  const [tokenUsageDataRaw] = useShinyOutput<any>("token_usage_chart_data", {});
  const [costByModelDataRaw] = useShinyOutput<any>(
    "cost_by_model_chart_data",
    {}
  );
  const [serviceTierDataRaw] = useShinyOutput<any>(
    "service_tier_chart_data",
    {}
  );

  // Get current granularity setting to format dates appropriately
  const [granularity] = useShinyOutput<string>("current_granularity", "1d");

  // Check API status to determine if we should show error state
  const [apiStatus] = useShinyOutput<{
    status: string;
    message: string;
    last_update: string;
  }>("api_status", undefined);

  // Debug logging
  console.log("Token Usage Data Raw:", tokenUsageDataRaw);
  console.log("Cost By Model Data Raw:", costByModelDataRaw);
  console.log("Service Tier Data Raw:", serviceTierDataRaw);

  // Convert column-major data to row-major arrays for recharts
  const tokenUsageData: TokenUsageData[] = React.useMemo(() => {
    if (
      !tokenUsageDataRaw ||
      typeof tokenUsageDataRaw !== "object" ||
      !tokenUsageDataRaw.date
    )
      return [];

    const length = tokenUsageDataRaw.date.length || 0;
    return Array.from({ length }, (_, i) => ({
      date: tokenUsageDataRaw.date[i],
      input_tokens: tokenUsageDataRaw.input_tokens[i] || 0,
      output_tokens: tokenUsageDataRaw.output_tokens[i] || 0,
    }));
  }, [tokenUsageDataRaw]);

  const costByModelData: CostByModelData[] = React.useMemo(() => {
    if (
      !costByModelDataRaw ||
      typeof costByModelDataRaw !== "object" ||
      !costByModelDataRaw.model
    )
      return [];

    const length = costByModelDataRaw.model.length || 0;
    return Array.from({ length }, (_, i) => ({
      model: costByModelDataRaw.model[i]?.replace("claude-", "") || "Unknown",
      cost: costByModelDataRaw.cost[i] || 0,
    }));
  }, [costByModelDataRaw]);

  const serviceTierData: ServiceTierData[] = React.useMemo(() => {
    if (
      !serviceTierDataRaw ||
      typeof serviceTierDataRaw !== "object" ||
      !serviceTierDataRaw.service_tier
    )
      return [];

    const length = serviceTierDataRaw.service_tier.length || 0;
    return Array.from({ length }, (_, i) => ({
      service_tier: serviceTierDataRaw.service_tier[i] || "standard",
      tokens: serviceTierDataRaw.tokens[i] || 0,
    }));
  }, [serviceTierDataRaw]);

  console.log("Processed Token Usage Data:", tokenUsageData);
  console.log("Processed Cost By Model Data:", costByModelData);
  console.log("Processed Service Tier Data:", serviceTierData);

  // Show error state if API is in error state and all data arrays are empty
  if (
    apiStatus?.status === "error" &&
    tokenUsageData.length === 0 &&
    costByModelData.length === 0 &&
    serviceTierData.length === 0
  ) {
    return (
      <ErrorState
        title='Charts Unavailable'
        message={apiStatus.message}
        showDemoModeButton={true}
        showRetryButton={true}
      />
    );
  }

  // Prepare pie chart data for service tiers
  const serviceTierPieData = serviceTierData.map((item, index) => ({
    name: `${item.service_tier} tier`,
    value: item.tokens,
    fill: COLORS[index % COLORS.length],
  }));

  return (
    <div className='grid gap-6'>
      {/* Token Usage Over Time Line Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Token Usage Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width='100%' height={300}>
            <LineChart data={tokenUsageData}>
              <CartesianGrid strokeDasharray='3 3' />
              <XAxis
                dataKey='date'
                tickFormatter={(value) => {
                  try {
                    const date = new Date(value);
                    if (granularity === "1m") {
                      // For per-minute: show "HH:MM" format
                      return date.toLocaleTimeString("en-US", {
                        hour: "2-digit",
                        minute: "2-digit",
                      });
                    } else if (granularity === "1h") {
                      // For hourly: show "MM/DD HH:00" format
                      return (
                        date.toLocaleDateString("en-US", {
                          month: "numeric",
                          day: "numeric",
                        }) +
                        " " +
                        date.toLocaleTimeString("en-US", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      );
                    } else {
                      // For daily: show "Mon DD" format (default)
                      return date.toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                      });
                    }
                  } catch {
                    return value;
                  }
                }}
              />
              <YAxis
                tickFormatter={(value) => value.toLocaleString()}
                width={100}
              />
              <Tooltip
                labelFormatter={(value) => {
                  try {
                    const date = new Date(value);
                    if (granularity === "1m") {
                      return date.toLocaleString("en-US", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      });
                    } else if (granularity === "1h") {
                      return date.toLocaleString("en-US", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      });
                    } else {
                      return date.toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      });
                    }
                  } catch {
                    return value;
                  }
                }}
                formatter={(value: any, name) => [value.toLocaleString(), name]}
              />
              <Line
                type='monotone'
                dataKey='input_tokens'
                stroke='#2563eb'
                strokeWidth={2}
                name='Input Tokens'
                animationDuration={300}
              />
              <Line
                type='monotone'
                dataKey='output_tokens'
                stroke='#dc2626'
                strokeWidth={2}
                name='Output Tokens'
                animationDuration={300}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Cost by Model Bar Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Cost Breakdown by Model</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width='100%' height={300}>
            <BarChart data={costByModelData}>
              <CartesianGrid strokeDasharray='3 3' />
              <XAxis
                dataKey='model'
                angle={-45}
                textAnchor='end'
                height={140}
              />
              <YAxis
                tickFormatter={(value) => `$${value.toFixed(2)}`}
                width={100}
              />
              <Tooltip
                formatter={(value: any) => [`$${value.toFixed(4)}`, "Cost"]}
                labelFormatter={(label) => `Model: ${label}`}
              />
              <Bar
                dataKey='cost'
                fill='#16a34a'
                radius={[4, 4, 0, 0]}
                animationDuration={300}
              />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
