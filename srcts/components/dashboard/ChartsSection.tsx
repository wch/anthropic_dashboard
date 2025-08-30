import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useShinyOutput } from "shiny-react";
import { Bar, BarChart, Line, LineChart, Pie, PieChart, Cell, CartesianGrid, XAxis, YAxis, ResponsiveContainer } from "recharts";
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";

interface MonthlyData {
  month: string;
  desktop: number;
  mobile: number;
  revenue: number;
}

interface TrendData {
  date: string;
  users: number;
  revenue: number;
}

interface CategoryData {
  category: string;
  score: number;
  count: number;
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042"];

export function ChartsSection() {
  // Connect to Shiny outputs for chart data (they come as column-major objects)
  const [monthlyDataRaw] = useShinyOutput<any>("monthly_chart_data", {});
  const [trendDataRaw] = useShinyOutput<any>("trend_chart_data", {});
  const [categoryDataRaw] = useShinyOutput<any>("category_chart_data", {});

  // Debug logging
  console.log("Monthly Data Raw:", monthlyDataRaw);
  console.log("Trend Data Raw:", trendDataRaw);
  console.log("Category Data Raw:", categoryDataRaw);

  // Convert column-major data to row-major arrays for recharts
  const monthlyData: MonthlyData[] = React.useMemo(() => {
    if (!monthlyDataRaw || typeof monthlyDataRaw !== 'object' || !monthlyDataRaw.month) return [];
    
    const length = monthlyDataRaw.month.length || 0;
    return Array.from({ length }, (_, i) => ({
      month: monthlyDataRaw.month[i],
      desktop: monthlyDataRaw.desktop[i],
      mobile: monthlyDataRaw.mobile[i],
      revenue: monthlyDataRaw.revenue[i]
    }));
  }, [monthlyDataRaw]);

  const trendData: TrendData[] = React.useMemo(() => {
    if (!trendDataRaw || typeof trendDataRaw !== 'object' || !trendDataRaw.date) return [];
    
    const length = trendDataRaw.date.length || 0;
    return Array.from({ length }, (_, i) => ({
      date: trendDataRaw.date[i],
      users: trendDataRaw.users[i],
      revenue: trendDataRaw.revenue[i]
    }));
  }, [trendDataRaw]);

  const categoryData: CategoryData[] = React.useMemo(() => {
    if (!categoryDataRaw || typeof categoryDataRaw !== 'object' || !categoryDataRaw.category) return [];
    
    const length = categoryDataRaw.category.length || 0;
    return Array.from({ length }, (_, i) => ({
      category: categoryDataRaw.category[i],
      score: categoryDataRaw.score[i],
      count: categoryDataRaw.count[i]
    }));
  }, [categoryDataRaw]);

  console.log("Processed Monthly Data:", monthlyData);
  console.log("Processed Trend Data:", trendData);
  console.log("Processed Category Data:", categoryData);

  // Chart configurations for shadcn/ui charts
  const barChartConfig = {
    desktop: {
      label: "Desktop",
      color: "#2563eb",
    },
    mobile: {
      label: "Mobile", 
      color: "#60a5fa",
    },
  } satisfies ChartConfig;

  const lineChartConfig = {
    users: {
      label: "Users",
      color: "#8884d8",
    },
    revenue: {
      label: "Revenue",
      color: "#82ca9d",
    },
  } satisfies ChartConfig;

  const pieChartConfig = {
    A: {
      label: "Category A",
      color: COLORS[0],
    },
    B: {
      label: "Category B", 
      color: COLORS[1],
    },
    C: {
      label: "Category C",
      color: COLORS[2],
    },
  } satisfies ChartConfig;

  // Prepare pie chart data
  const pieData = categoryData.map((item, index) => ({
    name: `Category ${item.category}`,
    value: item.count,
    fill: COLORS[index % COLORS.length]
  }));

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {/* Monthly Revenue Bar Chart */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Monthly Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Bar dataKey="desktop" fill="#2563eb" />
              <Bar dataKey="mobile" fill="#60a5fa" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Category Distribution Pie Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Category Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* User Growth Trend Line Chart */}
      <Card className="lg:col-span-3">
        <CardHeader>
          <CardTitle>Growth Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Line 
                type="monotone" 
                dataKey="users" 
                stroke="#8884d8" 
                strokeWidth={2}
              />
              <Line 
                type="monotone" 
                dataKey="revenue" 
                stroke="#82ca9d" 
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}