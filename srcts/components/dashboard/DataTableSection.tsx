import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { useShinyOutput } from "shiny-react";

interface SampleData {
  id: number;
  age: number;
  score: number;
  category: string;
}

export function DataTableSection() {
  // Connect to existing Shiny output for table data
  const [tableData] = useShinyOutput<Record<string, any[]> | undefined>("table_data", undefined);

  // Convert column-major data to row-major for display
  const processTableData = (): SampleData[] => {
    if (!tableData) return [];
    
    const columnNames = Object.keys(tableData);
    const numRows = columnNames.length > 0 ? tableData[columnNames[0]].length : 0;

    return Array.from({ length: numRows }, (_, rowIndex) => {
      const row: any = {};
      columnNames.forEach(colName => {
        row[colName] = tableData[colName][rowIndex];
      });
      return row as SampleData;
    });
  };

  const rows = processTableData();

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "A":
        return "bg-blue-100 text-blue-800 hover:bg-blue-200";
      case "B":
        return "bg-green-100 text-green-800 hover:bg-green-200";
      case "C":
        return "bg-orange-100 text-orange-800 hover:bg-orange-200";
      default:
        return "bg-gray-100 text-gray-800 hover:bg-gray-200";
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sample Data Table</CardTitle>
      </CardHeader>
      <CardContent>
        {rows.length > 0 ? (
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-16">ID</TableHead>
                  <TableHead>Age</TableHead>
                  <TableHead>Score</TableHead>
                  <TableHead>Category</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell className="font-medium">{row.id}</TableCell>
                    <TableCell>{row.age}</TableCell>
                    <TableCell>
                      <span className="font-mono">
                        {typeof row.score === "number"
                          ? row.score.toFixed(1)
                          : row.score}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge className={getCategoryColor(row.category)}>
                        Category {row.category}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          <div className="text-center text-muted-foreground py-8">
            Loading table data...
          </div>
        )}
      </CardContent>
    </Card>
  );
}