import React from "react";
import { CalendarIcon } from "lucide-react";
import { format } from "date-fns";
import { Calendar } from "@/components/ui/calendar";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useShinyInput } from "shiny-react";
import { cn } from "@/lib/utils";

export function DateRangeSelector() {
  // Date range inputs for the Shiny backend
  const [startDate, setStartDate] = useShinyInput<string>("date_start", "");
  const [endDate, setEndDate] = useShinyInput<string>("date_end", "");

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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Date Range</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col space-y-4">
          {/* Preset buttons */}
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPresetRange(1)}
              className="text-xs"
            >
              Today
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPresetRange(7)}
              className="text-xs"
            >
              Last 7 days
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPresetRange(30)}
              className="text-xs"
            >
              Last 30 days
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPresetRange(90)}
              className="text-xs"
            >
              Last 90 days
            </Button>
          </div>

          {/* Custom date pickers */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Start Date</label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !startDateObj && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {startDateObj ? format(startDateObj, "yyyy-MM-dd") : "Pick a date"}
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
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">End Date</label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full justify-start text-left font-normal",
                      !endDateObj && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {endDateObj ? format(endDateObj, "yyyy-MM-dd") : "Pick a date"}
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

          {/* Current selection display */}
          <div className="text-sm text-muted-foreground">
            <p>Current range: {startDateObj && endDateObj ? 
              `${format(startDateObj, "yyyy-MM-dd")} - ${format(endDateObj, "yyyy-MM-dd")}` : 
              "No range selected"
            }</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}