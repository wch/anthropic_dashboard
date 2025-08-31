import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Info } from "lucide-react";
import React from "react";
import { useShinyInput, useShinyOutput } from "shiny-react";

interface UsageData {
  date: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  service_tier: string;
}

interface CostData {
  date: string;
  description: string;
  amount: number;
  model: string;
}

export function DataTableSection() {
  // Connect to Shiny outputs for usage and cost table data
  const [usageTableDataRaw] = useShinyOutput<Record<string, any[]> | undefined>(
    "usage_table_data",
    undefined
  );
  const [costTableDataRaw] = useShinyOutput<Record<string, any[]> | undefined>(
    "cost_table_data",
    undefined
  );

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

  // Convert column-major data to row-major for usage data
  const processUsageData = (): UsageData[] => {
    if (!usageTableDataRaw) return [];

    const columnNames = Object.keys(usageTableDataRaw);
    const numRows =
      columnNames.length > 0 ? usageTableDataRaw[columnNames[0]].length : 0;

    return Array.from({ length: numRows }, (_, rowIndex) => {
      const row: any = {};
      columnNames.forEach((colName) => {
        row[colName] = usageTableDataRaw[colName][rowIndex];
      });
      return row as UsageData;
    });
  };

  // Convert column-major data to row-major for cost data
  const processCostData = (): CostData[] => {
    if (!costTableDataRaw) return [];

    const columnNames = Object.keys(costTableDataRaw);
    const numRows =
      columnNames.length > 0 ? costTableDataRaw[columnNames[0]].length : 0;

    return Array.from({ length: numRows }, (_, rowIndex) => {
      const row: any = {};
      columnNames.forEach((colName) => {
        row[colName] = costTableDataRaw[colName][rowIndex];
      });
      return row as CostData;
    });
  };

  const usageRows = processUsageData();
  const costRows = processCostData();

  const getModelColor = (model: string) => {
    if (model.includes("sonnet")) {
      return "bg-purple-100 text-purple-800 hover:bg-purple-200";
    } else if (model.includes("haiku")) {
      return "bg-green-100 text-green-800 hover:bg-green-200";
    } else if (model.includes("opus")) {
      return "bg-blue-100 text-blue-800 hover:bg-blue-200";
    } else {
      return "bg-gray-100 text-gray-800 hover:bg-gray-200";
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case "batch":
        return "bg-orange-100 text-orange-800 hover:bg-orange-200";
      case "standard":
        return "bg-blue-100 text-blue-800 hover:bg-blue-200";
      default:
        return "bg-gray-100 text-gray-800 hover:bg-gray-200";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>API Usage & Cost Details</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue='usage' className='w-full'>
          <TabsList className='grid w-full grid-cols-2'>
            <TabsTrigger value='usage'>Token Usage</TabsTrigger>
            <TabsTrigger value='cost'>Cost Breakdown</TabsTrigger>
          </TabsList>

          <TabsContent value='usage'>
            {usageRows.length > 0 ? (
              <div className='rounded-md border'>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Model</TableHead>
                      <TableHead>Input Tokens</TableHead>
                      <TableHead>Output Tokens</TableHead>
                      <TableHead>Total Tokens</TableHead>
                      <TableHead>Service Tier</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {usageRows.map((row, index) => (
                      <TableRow key={`${row.date}-${row.model}-${index}`}>
                        <TableCell className='font-medium'>
                          {new Date(row.date).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Badge className={getModelColor(row.model)}>
                            {row.model.replace("claude-", "")}
                          </Badge>
                        </TableCell>
                        <TableCell className='font-mono text-right'>
                          {row.input_tokens.toLocaleString()}
                        </TableCell>
                        <TableCell className='font-mono text-right'>
                          {row.output_tokens.toLocaleString()}
                        </TableCell>
                        <TableCell className='font-mono text-right font-semibold'>
                          {(
                            row.input_tokens + row.output_tokens
                          ).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <Badge className={getTierColor(row.service_tier)}>
                            {row.service_tier}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className='text-center text-muted-foreground py-8'>
                Loading usage data...
              </div>
            )}
          </TabsContent>

          <TabsContent value='cost'>
            {currentFilters?.api_key_id !== "all" && (
              <Alert className='mb-4'>
                <Info className='h-4 w-4' />
                <AlertDescription>
                  <strong>Cost Limitation:</strong> Cost data shows
                  workspace-level totals only. The Anthropic Cost API doesn't
                  provide per-API-key breakdowns.
                </AlertDescription>
              </Alert>
            )}
            {costRows.length > 0 ? (
              <div className='rounded-md border'>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Model</TableHead>
                      <TableHead className='text-right'>Amount</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {costRows.map((row, index) => (
                      <TableRow key={`${row.date}-${row.description}-${index}`}>
                        <TableCell className='font-medium'>
                          {new Date(row.date).toLocaleDateString()}
                        </TableCell>
                        <TableCell>{row.description}</TableCell>
                        <TableCell>
                          <Badge className={getModelColor(row.model)}>
                            {row.model.replace("claude-", "")}
                          </Badge>
                        </TableCell>
                        <TableCell className='font-mono text-right font-semibold'>
                          ${row.amount.toFixed(4)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            ) : (
              <div className='text-center text-muted-foreground py-8'>
                Loading cost data...
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
