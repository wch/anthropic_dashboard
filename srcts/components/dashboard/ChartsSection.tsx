import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ChevronDown, ChevronUp, Info } from "lucide-react";
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
import { useShinyInput, useShinyOutput } from "shiny-react";
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

interface WorkspaceCostData {
  workspace: string;
  cost: number;
}

interface ApiKeyUsageData {
  api_key: string;
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

// Helper function to format dates as YYYY-MM-DD
function formatDate(dateString: string): string {
  try {
    return new Date(dateString).toISOString().split("T")[0];
  } catch {
    return dateString;
  }
}

// Sortable table header component
interface SortableHeaderProps {
  children: React.ReactNode;
  column: string;
  currentSort: { column: string; direction: "asc" | "desc" };
  onSort: (column: any) => void;
  className?: string;
}

function SortableHeader({
  children,
  column,
  currentSort,
  onSort,
  className,
}: SortableHeaderProps) {
  return (
    <TableHead
      className={`cursor-pointer hover:bg-muted/50 select-none ${className || ""}`}
      onClick={() => onSort(column)}
    >
      <div className='flex items-center gap-1'>
        {children}
        {currentSort.column === column &&
          (currentSort.direction === "asc" ? (
            <ChevronUp className='h-4 w-4' />
          ) : (
            <ChevronDown className='h-4 w-4' />
          ))}
      </div>
    </TableHead>
  );
}

export function ChartsSection() {
  // Sorting state for tables
  const [workspaceTableSort, setWorkspaceTableSort] = React.useState<{
    column:
      | "workspace"
      | "cost"
      | "input_tokens"
      | "output_tokens"
      | "total_tokens"
      | "creation_time";
    direction: "asc" | "desc";
  }>({ column: "cost", direction: "desc" });

  const [apiKeyTableSort, setApiKeyTableSort] = React.useState<{
    column:
      | "api_key"
      | "workspace"
      | "input_tokens"
      | "output_tokens"
      | "total_tokens"
      | "creation_time";
    direction: "asc" | "desc";
  }>({ column: "total_tokens", direction: "desc" });

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

  // New data outputs for workspace costs and API key usage
  const [workspaceCostDataRaw] = useShinyOutput<any>(
    "workspace_cost_chart_data",
    {}
  );
  const [workspaceCostTableRaw] = useShinyOutput<any>(
    "workspace_cost_table_data",
    {}
  );
  const [apiKeyUsageDataRaw] = useShinyOutput<any>(
    "api_key_usage_chart_data",
    {}
  );
  const [apiKeyUsageTableRaw] = useShinyOutput<any>(
    "api_key_usage_table_data",
    {}
  );

  // Get current granularity setting to format dates appropriately
  const [granularity] = useShinyOutput<string>("current_granularity", "1d");

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

  // Debug logging
  console.log("Token Usage Data Raw:", tokenUsageDataRaw);
  console.log("Cost By Model Data Raw:", costByModelDataRaw);
  console.log("Service Tier Data Raw:", serviceTierDataRaw);
  console.log("Workspace Cost Data Raw:", workspaceCostDataRaw);
  console.log("Workspace Cost Table Raw:", workspaceCostTableRaw);
  console.log("API Key Usage Data Raw:", apiKeyUsageDataRaw);
  console.log("API Key Usage Table Raw:", apiKeyUsageTableRaw);

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

  const workspaceCostData: WorkspaceCostData[] = React.useMemo(() => {
    if (
      !workspaceCostDataRaw ||
      typeof workspaceCostDataRaw !== "object" ||
      !workspaceCostDataRaw.workspace
    )
      return [];

    const length = workspaceCostDataRaw.workspace.length || 0;
    return Array.from({ length }, (_, i) => ({
      workspace: workspaceCostDataRaw.workspace[i] || "Unknown",
      cost: workspaceCostDataRaw.cost[i] || 0,
    }));
  }, [workspaceCostDataRaw]);

  const apiKeyUsageData: ApiKeyUsageData[] = React.useMemo(() => {
    if (
      !apiKeyUsageDataRaw ||
      typeof apiKeyUsageDataRaw !== "object" ||
      !apiKeyUsageDataRaw.api_key
    )
      return [];

    const length = apiKeyUsageDataRaw.api_key.length || 0;
    return Array.from({ length }, (_, i) => ({
      api_key: apiKeyUsageDataRaw.api_key[i] || "Unknown",
      tokens: apiKeyUsageDataRaw.tokens[i] || 0,
    }));
  }, [apiKeyUsageDataRaw]);

  // Process workspace cost table data (includes totals)
  const workspaceCostTableData = React.useMemo(() => {
    if (
      !workspaceCostTableRaw ||
      typeof workspaceCostTableRaw !== "object" ||
      !workspaceCostTableRaw.workspace
    )
      return { rows: [], total: 0 };

    const length = workspaceCostTableRaw.workspace.length || 0;
    const rows = Array.from({ length }, (_, i) => ({
      workspace: workspaceCostTableRaw.workspace[i] || "Unknown",
      cost: workspaceCostTableRaw.cost[i] || 0,
      input_tokens: workspaceCostTableRaw.input_tokens[i] || 0,
      output_tokens: workspaceCostTableRaw.output_tokens[i] || 0,
      total_tokens: workspaceCostTableRaw.total_tokens[i] || 0,
      creation_time:
        workspaceCostTableRaw.creation_time[i] || "1970-01-01T00:00:00Z",
    }));

    return {
      rows,
      total: workspaceCostTableRaw.total || 0,
    };
  }, [workspaceCostTableRaw]);

  // Process API key usage table data
  const apiKeyUsageTableData = React.useMemo(() => {
    if (
      !apiKeyUsageTableRaw ||
      typeof apiKeyUsageTableRaw !== "object" ||
      !apiKeyUsageTableRaw.api_key
    )
      return [];

    const length = apiKeyUsageTableRaw.api_key.length || 0;
    return Array.from({ length }, (_, i) => ({
      api_key: apiKeyUsageTableRaw.api_key[i] || "Unknown",
      workspace: apiKeyUsageTableRaw.workspace[i] || "Unknown",
      input_tokens: apiKeyUsageTableRaw.input_tokens[i] || 0,
      output_tokens: apiKeyUsageTableRaw.output_tokens[i] || 0,
      total_tokens: apiKeyUsageTableRaw.total_tokens[i] || 0,
      creation_time:
        apiKeyUsageTableRaw.creation_time[i] || "1970-01-01T00:00:00Z",
    }));
  }, [apiKeyUsageTableRaw]);

  // Sorting functions
  const handleWorkspaceSortChange = (
    column:
      | "workspace"
      | "cost"
      | "input_tokens"
      | "output_tokens"
      | "total_tokens"
      | "creation_time"
  ) => {
    setWorkspaceTableSort((prev) => ({
      column,
      direction:
        prev.column === column && prev.direction === "asc" ? "desc" : "asc",
    }));
  };

  const handleApiKeySortChange = (
    column:
      | "api_key"
      | "workspace"
      | "input_tokens"
      | "output_tokens"
      | "total_tokens"
      | "creation_time"
  ) => {
    setApiKeyTableSort((prev) => ({
      column,
      direction:
        prev.column === column && prev.direction === "asc" ? "desc" : "asc",
    }));
  };

  // Sorted table data
  const sortedWorkspaceCostTableData = React.useMemo(() => {
    const sortedRows = [...workspaceCostTableData.rows].sort((a, b) => {
      let aVal: any = a[workspaceTableSort.column];
      let bVal: any = b[workspaceTableSort.column];

      // Convert to comparable values
      if (
        ["cost", "input_tokens", "output_tokens", "total_tokens"].includes(
          workspaceTableSort.column
        )
      ) {
        aVal = Number(aVal);
        bVal = Number(bVal);
      } else if (workspaceTableSort.column === "creation_time") {
        aVal = new Date(aVal);
        bVal = new Date(bVal);
      } else {
        aVal = String(aVal).toLowerCase();
        bVal = String(bVal).toLowerCase();
      }

      if (workspaceTableSort.direction === "asc") {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    return { ...workspaceCostTableData, rows: sortedRows };
  }, [workspaceCostTableData, workspaceTableSort]);

  const sortedApiKeyUsageTableData = React.useMemo(() => {
    return [...apiKeyUsageTableData].sort((a, b) => {
      let aVal: any = a[apiKeyTableSort.column];
      let bVal: any = b[apiKeyTableSort.column];

      // Convert to comparable values
      if (
        ["input_tokens", "output_tokens", "total_tokens"].includes(
          apiKeyTableSort.column
        )
      ) {
        aVal = Number(aVal);
        bVal = Number(bVal);
      } else if (apiKeyTableSort.column === "creation_time") {
        aVal = new Date(aVal);
        bVal = new Date(bVal);
      } else {
        aVal = String(aVal).toLowerCase();
        bVal = String(bVal).toLowerCase();
      }

      if (apiKeyTableSort.direction === "asc") {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });
  }, [apiKeyUsageTableData, apiKeyTableSort]);

  console.log("Processed Token Usage Data:", tokenUsageData);
  console.log("Processed Cost By Model Data:", costByModelData);
  console.log("Processed Service Tier Data:", serviceTierData);
  console.log("Processed Workspace Cost Data:", workspaceCostData);
  console.log(
    "Processed Workspace Cost Table Data:",
    sortedWorkspaceCostTableData
  );
  console.log("Processed API Key Usage Data:", apiKeyUsageData);
  console.log(
    "Processed API Key Usage Table Data:",
    sortedApiKeyUsageTableData
  );

  // Show error state if API is in error state and all data arrays are empty
  if (
    apiStatus?.status === "error" &&
    tokenUsageData.length === 0 &&
    costByModelData.length === 0 &&
    serviceTierData.length === 0 &&
    workspaceCostData.length === 0 &&
    apiKeyUsageData.length === 0
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

      {/* Workspace Cost Bar Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Cost by Workspace</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width='100%' height={300}>
            {sortedWorkspaceCostTableData.rows.length > 0 ? (
              <BarChart
                data={sortedWorkspaceCostTableData.rows}
                margin={{ left: 20, right: 20, top: 20, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray='3 3' />
                <XAxis
                  dataKey='workspace'
                  angle={-45}
                  textAnchor='end'
                  height={80}
                  tick={{ fontSize: 10 }}
                  interval={0}
                />
                <YAxis
                  tickFormatter={(value) => `$${value.toFixed(2)}`}
                  width={80}
                />
                <Tooltip
                  formatter={(value: any) => [`$${value.toFixed(2)}`, "Cost"]}
                  labelFormatter={(label) => `Workspace: ${label}`}
                />
                <Bar
                  dataKey='cost'
                  fill='#f59e0b'
                  radius={[4, 4, 0, 0]}
                  animationDuration={300}
                />
              </BarChart>
            ) : (
              <div className='flex items-center justify-center h-full text-muted-foreground'>
                No workspace cost data available
              </div>
            )}
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Workspace Cost Table */}
      <Card>
        <CardHeader>
          <CardTitle>Workspace Cost Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <SortableHeader
                  column='workspace'
                  currentSort={workspaceTableSort}
                  onSort={handleWorkspaceSortChange}
                >
                  Workspace
                </SortableHeader>
                <SortableHeader
                  column='cost'
                  currentSort={workspaceTableSort}
                  onSort={handleWorkspaceSortChange}
                  className='text-right'
                >
                  Cost
                </SortableHeader>
                <SortableHeader
                  column='input_tokens'
                  currentSort={workspaceTableSort}
                  onSort={handleWorkspaceSortChange}
                  className='text-right'
                >
                  Input Tokens
                </SortableHeader>
                <SortableHeader
                  column='output_tokens'
                  currentSort={workspaceTableSort}
                  onSort={handleWorkspaceSortChange}
                  className='text-right'
                >
                  Output Tokens
                </SortableHeader>
                <SortableHeader
                  column='total_tokens'
                  currentSort={workspaceTableSort}
                  onSort={handleWorkspaceSortChange}
                  className='text-right'
                >
                  Total Tokens
                </SortableHeader>
                <SortableHeader
                  column='creation_time'
                  currentSort={workspaceTableSort}
                  onSort={handleWorkspaceSortChange}
                  className='text-right'
                >
                  Created
                </SortableHeader>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedWorkspaceCostTableData.rows.map((row, index) => (
                <TableRow key={index}>
                  <TableCell className='font-medium'>{row.workspace}</TableCell>
                  <TableCell className='text-right'>
                    ${row.cost.toFixed(2)}
                  </TableCell>
                  <TableCell className='text-right'>
                    {row.input_tokens.toLocaleString()}
                  </TableCell>
                  <TableCell className='text-right'>
                    {row.output_tokens.toLocaleString()}
                  </TableCell>
                  <TableCell className='text-right font-medium'>
                    {row.total_tokens.toLocaleString()}
                  </TableCell>
                  <TableCell className='text-right text-sm text-muted-foreground'>
                    {formatDate(row.creation_time)}
                  </TableCell>
                </TableRow>
              ))}
              {sortedWorkspaceCostTableData.rows.length > 1 && (
                <TableRow className='font-bold border-t-2'>
                  <TableCell>Total</TableCell>
                  <TableCell className='text-right'>
                    ${sortedWorkspaceCostTableData.total.toFixed(2)}
                  </TableCell>
                  <TableCell className='text-right'>
                    {sortedWorkspaceCostTableData.rows
                      .reduce((sum, row) => sum + row.input_tokens, 0)
                      .toLocaleString()}
                  </TableCell>
                  <TableCell className='text-right'>
                    {sortedWorkspaceCostTableData.rows
                      .reduce((sum, row) => sum + row.output_tokens, 0)
                      .toLocaleString()}
                  </TableCell>
                  <TableCell className='text-right'>
                    {sortedWorkspaceCostTableData.rows
                      .reduce((sum, row) => sum + row.total_tokens, 0)
                      .toLocaleString()}
                  </TableCell>
                  <TableCell></TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          {sortedWorkspaceCostTableData.rows.length === 0 && (
            <p className='text-center text-muted-foreground py-4'>
              No workspace cost data available
            </p>
          )}
        </CardContent>
      </Card>

      {/* API Key Token Usage Bar Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Token Usage by API Key</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width='100%' height={300}>
            {sortedApiKeyUsageTableData.length > 0 ? (
              <BarChart data={sortedApiKeyUsageTableData}>
                <CartesianGrid strokeDasharray='3 3' />
                <XAxis
                  dataKey='api_key'
                  angle={-45}
                  textAnchor='end'
                  height={140}
                  tick={{ fontSize: 11 }}
                />
                <YAxis
                  tickFormatter={(value) => value.toLocaleString()}
                  width={100}
                />
                <Tooltip
                  formatter={(value: any) => [value.toLocaleString(), "Tokens"]}
                  labelFormatter={(label) => `API Key: ${label}`}
                />
                <Bar
                  dataKey='total_tokens'
                  fill='#8b5cf6'
                  radius={[4, 4, 0, 0]}
                  animationDuration={300}
                />
              </BarChart>
            ) : (
              <div className='flex items-center justify-center h-full text-muted-foreground'>
                No API key usage data available
              </div>
            )}
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* API Key Usage Table */}
      <Card>
        <CardHeader>
          <CardTitle>API Key Usage Details</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <SortableHeader
                  column='api_key'
                  currentSort={apiKeyTableSort}
                  onSort={handleApiKeySortChange}
                >
                  API Key
                </SortableHeader>
                <SortableHeader
                  column='workspace'
                  currentSort={apiKeyTableSort}
                  onSort={handleApiKeySortChange}
                >
                  Workspace
                </SortableHeader>
                <SortableHeader
                  column='input_tokens'
                  currentSort={apiKeyTableSort}
                  onSort={handleApiKeySortChange}
                  className='text-right'
                >
                  Input Tokens
                </SortableHeader>
                <SortableHeader
                  column='output_tokens'
                  currentSort={apiKeyTableSort}
                  onSort={handleApiKeySortChange}
                  className='text-right'
                >
                  Output Tokens
                </SortableHeader>
                <SortableHeader
                  column='total_tokens'
                  currentSort={apiKeyTableSort}
                  onSort={handleApiKeySortChange}
                  className='text-right'
                >
                  Total Tokens
                </SortableHeader>
                <SortableHeader
                  column='creation_time'
                  currentSort={apiKeyTableSort}
                  onSort={handleApiKeySortChange}
                  className='text-right'
                >
                  Created
                </SortableHeader>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedApiKeyUsageTableData.map((row, index) => (
                <TableRow key={index}>
                  <TableCell className='font-medium'>{row.api_key}</TableCell>
                  <TableCell>{row.workspace}</TableCell>
                  <TableCell className='text-right'>
                    {row.input_tokens.toLocaleString()}
                  </TableCell>
                  <TableCell className='text-right'>
                    {row.output_tokens.toLocaleString()}
                  </TableCell>
                  <TableCell className='text-right font-medium'>
                    {row.total_tokens.toLocaleString()}
                  </TableCell>
                  <TableCell className='text-right text-sm text-muted-foreground'>
                    {formatDate(row.creation_time)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {sortedApiKeyUsageTableData.length === 0 && (
            <p className='text-center text-muted-foreground py-4'>
              No API key usage data available
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Cost Breakdown by Model</CardTitle>
        </CardHeader>
        <CardContent>
          {currentFilters?.api_key_id !== "all" && (
            <Alert className='mb-4'>
              <Info className='h-4 w-4' />
              <AlertDescription>
                <strong>Note:</strong> Cost data shows workspace-level totals.
                Individual API key cost breakdowns are not available from the
                Anthropic API.
              </AlertDescription>
            </Alert>
          )}
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
