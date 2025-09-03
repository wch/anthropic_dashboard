import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Switch } from "@/components/ui/switch";
import { useShinyInput, useShinyOutput } from "@posit/shiny-react";
import { AlertTriangle, CheckCircle, HelpCircle, XCircle } from "lucide-react";
import React from "react";

export function DemoModeToggle() {
  const [demoMode, setDemoMode] = useShinyInput<boolean>(
    "use_demo_mode",
    false
  );
  const [apiStatus] = useShinyOutput<{
    status: string;
    message: string;
    last_update: string;
  }>("api_status", undefined);

  const handleToggle = (checked: boolean) => {
    setDemoMode(checked);
  };

  // Get status icon with colors
  const getStatusIcon = () => {
    if (demoMode) {
      return <AlertTriangle className='h-3 w-3 text-yellow-600' />;
    }

    if (!apiStatus) {
      return (
        <div className='h-2 w-2 bg-gray-400 rounded-full animate-pulse'></div>
      );
    }

    switch (apiStatus.status) {
      case "connected":
        return <CheckCircle className='h-3 w-3 text-green-600' />;
      case "partial":
        return <AlertTriangle className='h-3 w-3 text-yellow-600' />;
      case "demo":
        return <AlertTriangle className='h-3 w-3 text-yellow-600' />;
      case "error":
        return <XCircle className='h-3 w-3 text-red-600' />;
      default:
        return <div className='h-2 w-2 bg-gray-400 rounded-full'></div>;
    }
  };

  // Determine status badge colors based on API status
  const getBadgeColor = () => {
    if (demoMode) {
      return "bg-yellow-100 text-yellow-800 hover:bg-yellow-200";
    }

    if (!apiStatus) return "bg-gray-100 text-gray-800 hover:bg-gray-200";

    switch (apiStatus.status) {
      case "connected":
        return "bg-green-100 text-green-800 hover:bg-green-200";
      case "partial":
        return "bg-yellow-100 text-yellow-800 hover:bg-yellow-200";
      case "demo":
        return "bg-yellow-100 text-yellow-800 hover:bg-yellow-200";
      case "error":
        return "bg-red-100 text-red-800 hover:bg-red-200";
      default:
        return "bg-gray-100 text-gray-800 hover:bg-gray-200";
    }
  };

  const getStatusText = () => {
    if (demoMode) return "Demo Data";
    if (!apiStatus) return "Loading...";

    switch (apiStatus.status) {
      case "connected":
        return "Live Data";
      case "partial":
        return "Partial Data";
      case "error":
        return "API Error";
      case "demo":
        return "Demo Data";
      default:
        return apiStatus.status;
    }
  };

  return (
    <div className='space-y-3'>
      <div className='flex items-center justify-between'>
        <div className='flex items-center space-x-2'>
          <Switch
            id='demo-mode'
            checked={demoMode}
            onCheckedChange={handleToggle}
          />
          <Label htmlFor='demo-mode' className='text-sm font-medium'>
            Use Demo Data
          </Label>
        </div>
        <Popover>
          <PopoverTrigger asChild>
            <HelpCircle className='h-3 w-3 text-muted-foreground hover:text-foreground cursor-pointer' />
          </PopoverTrigger>
          <PopoverContent className='w-64 text-sm' side='left' align='start'>
            <p>
              When enabled, displays sample data instead of live API data. Use
              this when the Anthropic API is unavailable or to preview dashboard
              functionality.
            </p>
          </PopoverContent>
        </Popover>
      </div>

      <div className='flex items-center space-x-2'>
        {getStatusIcon()}
        <Badge className={`${getBadgeColor()} text-xs py-0 px-1`}>
          {getStatusText()}
        </Badge>
      </div>

      {/* Show API status message for non-connected states */}
      {apiStatus && apiStatus.status !== "connected" && !demoMode && (
        <p className='text-xs text-muted-foreground leading-tight'>
          {apiStatus.message}
        </p>
      )}
    </div>
  );
}
