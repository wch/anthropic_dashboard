import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { useShinyInput } from "shiny-react";

interface ErrorStateProps {
  title?: string;
  message: string;
  showDemoModeButton?: boolean;
  showRetryButton?: boolean;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Data Unavailable",
  message,
  showDemoModeButton = true,
  showRetryButton = false,
  onRetry,
}: ErrorStateProps) {
  const [, setDemoMode] = useShinyInput<boolean>("use_demo_mode", false);

  const handleEnableDemoMode = () => {
    setDemoMode(true);
  };

  const handleRetry = () => {
    if (onRetry) {
      onRetry();
    }
    // Force a refresh by briefly toggling demo mode off and on
    // This will trigger the backend to retry API calls
    window.location.reload();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-destructive" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{message}</AlertDescription>
        </Alert>

        <div className="flex flex-col sm:flex-row gap-2">
          {showDemoModeButton && (
            <Button 
              onClick={handleEnableDemoMode}
              variant="default"
              className="flex-1"
            >
              View Demo Data
            </Button>
          )}
          
          {showRetryButton && (
            <Button
              onClick={handleRetry}
              variant="outline"
              className="flex-1"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}