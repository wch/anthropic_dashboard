import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useShinyOutput } from "shiny-react";
import { AlertTriangle, CheckCircle, XCircle } from "lucide-react";

export function ApiStatusCard() {
  // Connect to a Shiny output that indicates API status
  const [apiStatus] = useShinyOutput<{
    status: "connected" | "demo" | "error";
    message: string;
    last_update?: string;
  } | undefined>("api_status", undefined);

  if (!apiStatus) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">API Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2">
            <div className="h-2 w-2 bg-gray-400 rounded-full animate-pulse"></div>
            <span className="text-sm text-muted-foreground">Checking...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getStatusIcon = () => {
    switch (apiStatus.status) {
      case "connected":
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "demo":
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case "error":
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <div className="h-2 w-2 bg-gray-400 rounded-full"></div>;
    }
  };

  const getStatusColor = () => {
    switch (apiStatus.status) {
      case "connected":
        return "bg-green-100 text-green-800 hover:bg-green-200";
      case "demo":
        return "bg-yellow-100 text-yellow-800 hover:bg-yellow-200";
      case "error":
        return "bg-red-100 text-red-800 hover:bg-red-200";
      default:
        return "bg-gray-100 text-gray-800 hover:bg-gray-200";
    }
  };

  const getStatusText = () => {
    switch (apiStatus.status) {
      case "connected":
        return "Live Data";
      case "demo":
        return "Demo Data";
      case "error":
        return "API Error";
      default:
        return "Unknown";
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">API Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            {getStatusIcon()}
            <Badge className={getStatusColor()}>
              {getStatusText()}
            </Badge>
          </div>
          
          {apiStatus.status !== "connected" && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription className="text-sm">
                {apiStatus.message}
              </AlertDescription>
            </Alert>
          )}
          
          {apiStatus.last_update && (
            <p className="text-xs text-muted-foreground">
              Last update: {new Date(apiStatus.last_update).toLocaleString()}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}