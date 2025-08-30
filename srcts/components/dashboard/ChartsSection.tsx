import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useShinyOutput } from "shiny-react";
import { Bar, BarChart, Line, LineChart, Pie, PieChart, Cell, CartesianGrid, XAxis, YAxis, ResponsiveContainer, Tooltip, Legend } from "recharts";

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

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8", "#82CA9D"];

export function ChartsSection() {
  // Connect to Shiny outputs for Anthropic API chart data
  const [tokenUsageDataRaw] = useShinyOutput<any>("token_usage_chart_data", {});
  const [costByModelDataRaw] = useShinyOutput<any>("cost_by_model_chart_data", {});
  const [serviceTierDataRaw] = useShinyOutput<any>("service_tier_chart_data", {});

  // Debug logging
  console.log("Token Usage Data Raw:", tokenUsageDataRaw);
  console.log("Cost By Model Data Raw:", costByModelDataRaw);
  console.log("Service Tier Data Raw:", serviceTierDataRaw);

  // Convert column-major data to row-major arrays for recharts
  const tokenUsageData: TokenUsageData[] = React.useMemo(() => {
    if (!tokenUsageDataRaw || typeof tokenUsageDataRaw !== 'object' || !tokenUsageDataRaw.date) return [];
    
    const length = tokenUsageDataRaw.date.length || 0;
    return Array.from({ length }, (_, i) => ({
      date: tokenUsageDataRaw.date[i],
      input_tokens: tokenUsageDataRaw.input_tokens[i] || 0,
      output_tokens: tokenUsageDataRaw.output_tokens[i] || 0
    }));
  }, [tokenUsageDataRaw]);

  const costByModelData: CostByModelData[] = React.useMemo(() => {
    if (!costByModelDataRaw || typeof costByModelDataRaw !== 'object' || !costByModelDataRaw.model) return [];
    
    const length = costByModelDataRaw.model.length || 0;
    return Array.from({ length }, (_, i) => ({
      model: costByModelDataRaw.model[i]?.replace('claude-', '') || 'Unknown',
      cost: costByModelDataRaw.cost[i] || 0
    }));
  }, [costByModelDataRaw]);

  const serviceTierData: ServiceTierData[] = React.useMemo(() => {
    if (!serviceTierDataRaw || typeof serviceTierDataRaw !== 'object' || !serviceTierDataRaw.service_tier) return [];
    
    const length = serviceTierDataRaw.service_tier.length || 0;
    return Array.from({ length }, (_, i) => ({
      service_tier: serviceTierDataRaw.service_tier[i] || 'standard',
      tokens: serviceTierDataRaw.tokens[i] || 0
    }));
  }, [serviceTierDataRaw]);

  console.log("Processed Token Usage Data:", tokenUsageData);
  console.log("Processed Cost By Model Data:", costByModelData);
  console.log("Processed Service Tier Data:", serviceTierData);

  // Prepare pie chart data for service tiers
  const serviceTierPieData = serviceTierData.map((item, index) => ({
    name: `${item.service_tier} tier`,
    value: item.tokens,
    fill: COLORS[index % COLORS.length]
  }));

  return (
    <div className="grid gap-6">
      {/* Token Usage Over Time Line Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Token Usage Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={tokenUsageData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tickFormatter={(value) => {
                  try {
                    return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                  } catch {
                    return value;
                  }
                }}
              />
              <YAxis tickFormatter={(value) => value.toLocaleString()} />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
                formatter={(value: any, name) => [value.toLocaleString(), name]}
              />
              <Line 
                type="monotone" 
                dataKey="input_tokens" 
                stroke="#2563eb" 
                strokeWidth={2}
                name="Input Tokens"
                animationDuration={300}
              />
              <Line 
                type="monotone" 
                dataKey="output_tokens" 
                stroke="#dc2626" 
                strokeWidth={2}
                name="Output Tokens"
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
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={costByModelData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="model" 
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                tickFormatter={(value) => `$${value.toFixed(2)}`}
              />
              <Tooltip 
                formatter={(value: any) => [`$${value.toFixed(4)}`, "Cost"]}
                labelFormatter={(label) => `Model: ${label}`}
              />
              <Bar 
                dataKey="cost" 
                fill="#16a34a"
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