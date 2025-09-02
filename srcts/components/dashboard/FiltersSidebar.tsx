import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { CalendarIcon, ChevronDown, Filter } from "lucide-react";
import React from "react";
import { useShinyInput, useShinyOutput } from "shiny-react";

export function FiltersSidebar() {
  // Input controls for filtering
  const [selectedWorkspace, setSelectedWorkspace] = useShinyInput<string>(
    "filter_workspace_id",
    "all"
  );
  const [selectedApiKey, setSelectedApiKey] = useShinyInput<string>(
    "filter_api_key_id",
    "all"
  );
  const [selectedModel, setSelectedModel] = useShinyInput<string>(
    "filter_model",
    "all"
  );
  const [selectedGranularity, setSelectedGranularity] = useShinyInput<string>(
    "filter_granularity",
    "1d"
  );

  // Date range inputs for the Shiny backend
  const [startDate, setStartDate] = useShinyInput<string>("date_start", "");
  const [endDate, setEndDate] = useShinyInput<string>("date_end", "");

  // Available options from backend
  const [availableWorkspaces] = useShinyOutput<{ id: string; name: string }[]>(
    "available_workspaces",
    []
  );
  const [availableApiKeys] = useShinyOutput<{ id: string; name: string }[]>(
    "available_api_keys",
    []
  );
  const [availableModels] = useShinyOutput<string[]>("available_models", []);

  // Local state for the calendar pickers and collapsible sections
  const [startDateObj, setStartDateObj] = React.useState<Date>();
  const [endDateObj, setEndDateObj] = React.useState<Date>();
  const [isFiltersOpen, setIsFiltersOpen] = React.useState(true);
  const [isDateRangeOpen, setIsDateRangeOpen] = React.useState(true);

  // Initialize with default date range (last 7 days)
  React.useEffect(() => {
    const today = new Date();
    const lastWeek = new Date();
    lastWeek.setDate(today.getDate() - 7);

    setStartDateObj(lastWeek);
    setEndDateObj(today);

    // Send ISO format to Shiny backend
    setStartDate(lastWeek.toISOString().split("T")[0] + "T00:00:00Z");
    setEndDate(today.toISOString().split("T")[0] + "T23:59:59Z");
  }, [setStartDate, setEndDate]);

  const granularityOptions = [
    { value: "1m", label: "Per Minute", description: "1 minute buckets" },
    { value: "1h", label: "Hourly", description: "1 hour buckets" },
    { value: "1d", label: "Daily", description: "1 day buckets" },
  ];

  const handleWorkspaceChange = (value: string) => {
    setSelectedWorkspace(value);
    // Reset API key selection when workspace changes
    setSelectedApiKey("all");
  };

  const handleStartDateSelect = (date: Date | undefined) => {
    setStartDateObj(date);
    if (date) {
      const isoString = date.toISOString().split("T")[0] + "T00:00:00Z";
      setStartDate(isoString);
    }
  };

  const handleEndDateSelect = (date: Date | undefined) => {
    setEndDateObj(date);
    if (date) {
      const isoString = date.toISOString().split("T")[0] + "T23:59:59Z";
      setEndDate(isoString);
    }
  };

  const setPresetRange = (days: number) => {
    const today = new Date();
    const pastDate = new Date();
    pastDate.setDate(today.getDate() - days);

    setStartDateObj(pastDate);
    setEndDateObj(today);

    setStartDate(pastDate.toISOString().split("T")[0] + "T00:00:00Z");
    setEndDate(today.toISOString().split("T")[0] + "T23:59:59Z");
  };

  const getWorkspaceDisplayName = (workspaceId: string) => {
    if (workspaceId === "all") return "All Workspaces";
    const workspace = availableWorkspaces?.find((ws) => ws.id === workspaceId);
    return workspace ? workspace.name : workspaceId;
  };

  const getApiKeyDisplayName = (apiKeyId: string) => {
    if (apiKeyId === "all") return "All API Keys";
    const apiKey = availableApiKeys?.find((key) => key.id === apiKeyId);
    return apiKey ? apiKey.name : apiKeyId;
  };

  const getModelDisplayName = (model: string) => {
    if (model === "all") return "All Models";
    return model
      .replace("claude-", "")
      .replace("-20241022", "")
      .replace("-20240307", "");
  };

  // Count active filters
  const activeFilterCount = [
    selectedWorkspace !== "all",
    selectedApiKey !== "all",
    selectedModel !== "all",
  ].filter(Boolean).length;

  return (
    <div className='space-y-3'>
      <Separator />
      {/* Date Range Section */}
      <Collapsible open={isDateRangeOpen} onOpenChange={setIsDateRangeOpen}>
        <CollapsibleTrigger asChild>
          <Button
            variant='ghost'
            className='w-full justify-between p-2 h-auto font-medium text-sm'
          >
            <div className='flex items-center gap-2'>
              <CalendarIcon className='h-4 w-4' />
              Date Range
            </div>
            <ChevronDown
              className={cn(
                "h-4 w-4 transition-transform",
                isDateRangeOpen && "rotate-180"
              )}
            />
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className='space-y-2 px-2'>
          {/* Preset buttons */}
          <div className='flex flex-wrap gap-1'>
            <Button
              variant='outline'
              size='sm'
              onClick={() => setPresetRange(7)}
              className='text-xs px-2 py-1 h-6'
            >
              7d
            </Button>
            <Button
              variant='outline'
              size='sm'
              onClick={() => setPresetRange(30)}
              className='text-xs px-2 py-1 h-6'
            >
              30d
            </Button>
            <Button
              variant='outline'
              size='sm'
              onClick={() => setPresetRange(90)}
              className='text-xs px-2 py-1 h-6'
            >
              90d
            </Button>
          </div>

          {/* Date pickers */}
          <div className='space-y-2'>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant='outline'
                  size='sm'
                  className={cn(
                    "w-full justify-start text-left font-normal text-xs h-8",
                    !startDateObj && "text-muted-foreground"
                  )}
                >
                  <CalendarIcon className='mr-2 h-3 w-3' />
                  {startDateObj ? format(startDateObj, "MMM dd") : "Start Date"}
                </Button>
              </PopoverTrigger>
              <PopoverContent className='w-auto p-0' align='start'>
                <Calendar
                  mode='single'
                  selected={startDateObj}
                  onSelect={handleStartDateSelect}
                  initialFocus
                />
              </PopoverContent>
            </Popover>

            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant='outline'
                  size='sm'
                  className={cn(
                    "w-full justify-start text-left font-normal text-xs h-8",
                    !endDateObj && "text-muted-foreground"
                  )}
                >
                  <CalendarIcon className='mr-2 h-3 w-3' />
                  {endDateObj ? format(endDateObj, "MMM dd") : "End Date"}
                </Button>
              </PopoverTrigger>
              <PopoverContent className='w-auto p-0' align='start'>
                <Calendar
                  mode='single'
                  selected={endDateObj}
                  onSelect={handleEndDateSelect}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>
        </CollapsibleContent>
      </Collapsible>

      <Separator />

      {/* Filters Section */}
      <Collapsible open={isFiltersOpen} onOpenChange={setIsFiltersOpen}>
        <CollapsibleTrigger asChild>
          <Button
            variant='ghost'
            className='w-full justify-between p-2 h-auto font-medium text-sm'
          >
            <div className='flex items-center gap-2'>
              <Filter className='h-4 w-4' />
              Filters
              {activeFilterCount > 0 && (
                <Badge variant='secondary' className='h-5 min-w-5 text-xs px-1'>
                  {activeFilterCount}
                </Badge>
              )}
            </div>
            <ChevronDown
              className={cn(
                "h-4 w-4 transition-transform",
                isFiltersOpen && "rotate-180"
              )}
            />
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className='space-y-3 px-2'>
          {/* Workspace Filter */}
          <div className='space-y-1'>
            <label className='text-xs font-medium text-muted-foreground'>
              Workspace
            </label>
            <Select
              value={selectedWorkspace}
              onValueChange={handleWorkspaceChange}
            >
              <SelectTrigger className='h-8 text-xs'>
                <SelectValue />
              </SelectTrigger>
              <SelectContent className='max-h-[200px]'>
                <SelectItem value='all'>All Workspaces</SelectItem>
                {availableWorkspaces?.map((workspace) => (
                  <SelectItem key={workspace.id} value={workspace.id}>
                    {workspace.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* API Key Filter */}
          <div className='space-y-1'>
            <label className='text-xs font-medium text-muted-foreground'>
              API Key
            </label>
            <Select value={selectedApiKey} onValueChange={setSelectedApiKey}>
              <SelectTrigger className='h-8 text-xs'>
                <SelectValue />
              </SelectTrigger>
              <SelectContent className='max-h-[200px]'>
                <SelectItem value='all'>All API Keys</SelectItem>
                {availableApiKeys?.map((apiKey) => (
                  <SelectItem key={apiKey.id} value={apiKey.id}>
                    {apiKey.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Model Filter */}
          <div className='space-y-1'>
            <label className='text-xs font-medium text-muted-foreground'>
              Model
            </label>
            <Select value={selectedModel} onValueChange={setSelectedModel}>
              <SelectTrigger className='h-8 text-xs'>
                <SelectValue />
              </SelectTrigger>
              <SelectContent className='max-h-[200px]'>
                <SelectItem value='all'>All Models</SelectItem>
                {availableModels?.map((model) => (
                  <SelectItem key={model} value={model}>
                    {getModelDisplayName(model)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Granularity Control */}
          <div className='space-y-1'>
            <label className='text-xs font-medium text-muted-foreground'>
              Granularity
            </label>
            <Select
              value={selectedGranularity}
              onValueChange={setSelectedGranularity}
            >
              <SelectTrigger className='h-8 text-xs'>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {granularityOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    <div className='flex flex-col'>
                      <span className='text-xs'>{option.label}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Active Filters Summary */}
          {activeFilterCount > 0 && (
            <div className='space-y-2 pt-2'>
              <div className='text-xs font-medium text-muted-foreground'>
                Active:
              </div>
              <div className='flex flex-col gap-1'>
                {selectedWorkspace !== "all" && (
                  <Badge variant='secondary' className='text-xs py-0 px-1 h-5'>
                    {getWorkspaceDisplayName(selectedWorkspace)}
                  </Badge>
                )}
                {selectedApiKey !== "all" && (
                  <Badge variant='secondary' className='text-xs py-0 px-1 h-5'>
                    {getApiKeyDisplayName(selectedApiKey)}
                  </Badge>
                )}
                {selectedModel !== "all" && (
                  <Badge variant='secondary' className='text-xs py-0 px-1 h-5'>
                    {getModelDisplayName(selectedModel)}
                  </Badge>
                )}
              </div>
            </div>
          )}
        </CollapsibleContent>
      </Collapsible>
      <Separator />
    </div>
  );
}
