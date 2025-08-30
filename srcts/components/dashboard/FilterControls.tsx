import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useShinyInput, useShinyOutput } from "shiny-react";

export function FilterControls() {
  // Input controls for filtering
  const [selectedWorkspace, setSelectedWorkspace] = useShinyInput<string>("filter_workspace_id", "all");
  const [selectedApiKey, setSelectedApiKey] = useShinyInput<string>("filter_api_key_id", "all");
  const [selectedModel, setSelectedModel] = useShinyInput<string>("filter_model", "all");
  const [selectedGranularity, setSelectedGranularity] = useShinyInput<string>("filter_granularity", "1d");

  // Available options from backend
  const [availableWorkspaces] = useShinyOutput<string[]>("available_workspaces", []);
  const [availableApiKeys] = useShinyOutput<string[]>("available_api_keys", []);
  const [availableModels] = useShinyOutput<string[]>("available_models", []);

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

  const getWorkspaceDisplayName = (workspaceId: string) => {
    if (workspaceId === "all") return "All Workspaces";
    return workspaceId.length > 20 ? `${workspaceId.substring(0, 20)}...` : workspaceId;
  };

  const getApiKeyDisplayName = (apiKeyId: string) => {
    if (apiKeyId === "all") return "All API Keys";
    return apiKeyId.length > 20 ? `${apiKeyId.substring(0, 20)}...` : apiKeyId;
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Workspace Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Workspace</label>
            <Select value={selectedWorkspace} onValueChange={handleWorkspaceChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select workspace..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Workspaces</SelectItem>
                {availableWorkspaces?.map((workspace) => (
                  <SelectItem key={workspace} value={workspace}>
                    {getWorkspaceDisplayName(workspace)}
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
              <SelectContent>
                <SelectItem value="all">All API Keys</SelectItem>
                {availableApiKeys?.map((apiKey) => (
                  <SelectItem key={apiKey} value={apiKey}>
                    {getApiKeyDisplayName(apiKey)}
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
              <SelectContent>
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
          </div>
          {selectedWorkspace === "all" && selectedApiKey === "all" && selectedModel === "all" && (
            <div className="text-sm text-muted-foreground">No filters applied - showing all data</div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}