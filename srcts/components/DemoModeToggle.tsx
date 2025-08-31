import React from "react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useShinyInput, useShinyOutput } from "shiny-react";

export function DemoModeToggle() {
  const [demoMode, setDemoMode] = useShinyInput<boolean>("use_demo_mode", false);
  const [apiStatus] = useShinyOutput<{
    status: string;
    message: string;
    last_update: string;
  }>("api_status", undefined);

  const handleToggle = (checked: boolean) => {
    setDemoMode(checked);
  };

  // Determine status badge variant based on API status
  const getBadgeVariant = () => {
    if (demoMode) return "secondary";
    if (!apiStatus) return "secondary";
    
    switch (apiStatus.status) {
      case "connected": return "default";
      case "partial": return "secondary";
      case "error": return "destructive";
      case "demo": return "secondary";
      default: return "secondary";
    }
  };

  const getStatusText = () => {
    if (demoMode) return "Demo Data";
    if (!apiStatus) return "Loading...";
    
    switch (apiStatus.status) {
      case "connected": return "Live Data";
      case "partial": return "Partial Data";
      case "error": return "API Error";
      case "demo": return "Demo Data";
      default: return apiStatus.status;
    }
  };

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center space-x-2">
        <Switch
          id="demo-mode"
          checked={demoMode}
          onCheckedChange={handleToggle}
        />
        <Label htmlFor="demo-mode" className="text-sm font-medium">
          Demo Mode
        </Label>
      </div>
      
      <Badge variant={getBadgeVariant()}>
        {getStatusText()}
      </Badge>
    </div>
  );
}