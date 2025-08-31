import React from "react";
import { CalendarIcon } from "lucide-react";
import { format } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useShinyInput, useShinyOutput } from "shiny-react";
import { cn } from "@/lib/utils";

export function FilterControls() {
  // Input controls for filtering
  const [selectedWorkspace, setSelectedWorkspace] = useShinyInput<string>("filter_workspace_id", "all");
  const [selectedApiKey, setSelectedApiKey] = useShinyInput<string>("filter_api_key_id", "all");
  const [selectedModel, setSelectedModel] = useShinyInput<string>("filter_model", "all");
  const [selectedGranularity, setSelectedGranularity] = useShinyInput<string>("filter_granularity", "1d");
  
  // Date range inputs for the Shiny backend
  const [startDate, setStartDate] = useShinyInput<string>("date_start", "");
  const [endDate, setEndDate] = useShinyInput<string>("date_end", "");

  // Available options from backend
  const [availableWorkspaces] = useShinyOutput<{id: string, name: string}[]>("available_workspaces", []);
  const [availableApiKeys] = useShinyOutput<{id: string, name: string}[]>("available_api_keys", []);
  const [availableModels] = useShinyOutput<string[]>("available_models", []);
  
  // Local state for the calendar pickers
  const [startDateObj, setStartDateObj] = React.useState<Date>();
  const [endDateObj, setEndDateObj] = React.useState<Date>();

  // Initialize with default date range (last 7 days)
  React.useEffect(() => {
    const today = new Date();
    const lastWeek = new Date();
    lastWeek.setDate(today.getDate() - 7);
    
    setStartDateObj(lastWeek);
    setEndDateObj(today);
    
    // Send ISO format to Shiny backend
    setStartDate(lastWeek.toISOString().split('T')[0] + "T00:00:00Z");
    setEndDate(today.toISOString().split('T')[0] + "T23:59:59Z");
  }, [setStartDate, setEndDate]);

  const granularityOptions = [
    { value: "1h", label: "Hourly", description: "1 hour buckets" },
    { value: "1d", label: "Daily", description: "1 day buckets" },
    { value: "7d", label: "Weekly", description: "7 day buckets" },
    { value: "30d", label: "Monthly", description: "30 day buckets" }
  ];

  const handleWorkspaceChange = (value: string) => {
    setSelectedWorkspace(value);
    // Reset API key selection when workspace changes
    setSelectedApiKey("all");
  };

  const handleStartDateSelect = (date: Date | undefined) => {
    setStartDateObj(date);
    if (date) {
      const isoString = date.toISOString().split('T')[0] + "T00:00:00Z";
      setStartDate(isoString);
    }
  };

  const handleEndDateSelect = (date: Date | undefined) => {
    setEndDateObj(date);
    if (date) {
      const isoString = date.toISOString().split('T')[0] + "T23:59:59Z";
      setEndDate(isoString);
    }
  };

  const setPresetRange = (days: number) => {
    const today = new Date();
    const pastDate = new Date();
    pastDate.setDate(today.getDate() - days);
    
    setStartDateObj(pastDate);
    setEndDateObj(today);
    
    setStartDate(pastDate.toISOString().split('T')[0] + "T00:00:00Z");
    setEndDate(today.toISOString().split('T')[0] + "T23:59:59Z");
  };

  const getWorkspaceDisplayName = (workspaceId: string) => {
    if (workspaceId === "all") return "All Workspaces";
    const workspace = availableWorkspaces?.find(ws => ws.id === workspaceId);
    return workspace ? workspace.name : workspaceId;
  };

  const getApiKeyDisplayName = (apiKeyId: string) => {
    if (apiKeyId === "all") return "All API Keys";
    const apiKey = availableApiKeys?.find(key => key.id === apiKeyId);
    return apiKey ? apiKey.name : apiKeyId;
  };

  const getModelDisplayName = (model: string) => {
    if (model === "all") return "All Models";
    return model.replace("claude-", "").replace("-20241022", "").replace("-20240307", "");
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Filters & Grouping</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Workspace Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Workspace</label>
            <Select value={selectedWorkspace} onValueChange={handleWorkspaceChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select workspace..." />
              </SelectTrigger>
              <SelectContent className="max-h-[300px]">
                <SelectItem value="all">All Workspaces</SelectItem>
                {availableWorkspaces?.map((workspace) => (
                  <SelectItem key={workspace.id} value={workspace.id}>
                    {workspace.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* API Key Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">API Key</label>
            <Select value={selectedApiKey} onValueChange={setSelectedApiKey}>
              <SelectTrigger>
                <SelectValue placeholder="Select API key..." />
              </SelectTrigger>
              <SelectContent className="max-h-[300px]">
                <SelectItem value="all">All API Keys</SelectItem>
                {availableApiKeys?.map((apiKey) => (
                  <SelectItem key={apiKey.id} value={apiKey.id}>
                    {apiKey.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Model Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Model</label>
            <Select value={selectedModel} onValueChange={setSelectedModel}>
              <SelectTrigger>
                <SelectValue placeholder="Select model..." />
              </SelectTrigger>
              <SelectContent className="max-h-[300px]">
                <SelectItem value="all">All Models</SelectItem>
                {availableModels?.map((model) => (
                  <SelectItem key={model} value={model}>
                    {getModelDisplayName(model)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Granularity Control */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Granularity</label>
            <Select value={selectedGranularity} onValueChange={setSelectedGranularity}>
              <SelectTrigger>
                <SelectValue placeholder="Select granularity..." />
              </SelectTrigger>
              <SelectContent>
                {granularityOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    <div className="flex flex-col">
                      <span>{option.label}</span>
                      <span className="text-xs text-muted-foreground">{option.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Date Range Control */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Date Range</label>
            <div className="flex flex-col space-y-2">
              {/* Preset buttons */}
              <div className="flex flex-wrap gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPresetRange(7)}
                  className="text-xs px-2 py-1 h-6"
                >
                  7d
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPresetRange(30)}
                  className="text-xs px-2 py-1 h-6"
                >
                  30d
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPresetRange(90)}
                  className="text-xs px-2 py-1 h-6"
                >
                  90d
                </Button>
              </div>
              
              {/* Date pickers row */}
              <div className="grid grid-cols-2 gap-1">
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      className={cn(
                        "justify-start text-left font-normal text-xs h-8",
                        !startDateObj && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-1 h-3 w-3" />
                      {startDateObj ? format(startDateObj, "MM-dd") : "Start"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={startDateObj}
                      onSelect={handleStartDateSelect}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>

                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      className={cn(
                        "justify-start text-left font-normal text-xs h-8",
                        !endDateObj && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon className="mr-1 h-3 w-3" />
                      {endDateObj ? format(endDateObj, "MM-dd") : "End"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={endDateObj}
                      onSelect={handleEndDateSelect}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>
          </div>
        </div>

        {/* Current Filter Summary */}
        <div className="mt-4 space-y-2">
          <div className="text-sm font-medium">Active Filters:</div>
          <div className="flex flex-wrap gap-2">
            {selectedWorkspace !== "all" && (
              <Badge variant="secondary">
                Workspace: {getWorkspaceDisplayName(selectedWorkspace)}
              </Badge>
            )}
            {selectedApiKey !== "all" && (
              <Badge variant="secondary">
                API Key: {getApiKeyDisplayName(selectedApiKey)}
              </Badge>
            )}
            {selectedModel !== "all" && (
              <Badge variant="secondary">
                Model: {getModelDisplayName(selectedModel)}
              </Badge>
            )}
            <Badge variant="outline">
              Granularity: {granularityOptions.find(opt => opt.value === selectedGranularity)?.label || selectedGranularity}
            </Badge>
            {startDateObj && endDateObj && (
              <Badge variant="outline">
                Date Range: {format(startDateObj, "MM-dd")} - {format(endDateObj, "MM-dd")}
              </Badge>
            )}
          </div>
          {selectedWorkspace === "all" && selectedApiKey === "all" && selectedModel === "all" && (
            <div className="text-sm text-muted-foreground">No filters applied - showing all data</div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}