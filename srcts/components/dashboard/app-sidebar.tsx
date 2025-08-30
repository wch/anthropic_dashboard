"use client"

import * as React from "react"
import {
  BarChart3,
  DollarSign,
  Home,
  LineChart,
  PieChart,
  Settings2,
  Table,
  TrendingUp,
  Zap,
  Activity,
  Clock,
  Cpu,
  FileText,
} from "lucide-react"

import { NavMain } from "./nav-main"
import { NavProjects } from "./nav-projects"
import { NavUser } from "./nav-user"
import { TeamSwitcher } from "./team-switcher"
import { Badge } from "@/components/ui/badge"
import { useShinyOutput } from "shiny-react"
import { CheckCircle, AlertTriangle, XCircle } from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar"

// Anthropic API Dashboard navigation data
const data = {
  user: {
    name: "API User",
    email: "admin@company.com",
    avatar: "",
  },
  teams: [
    {
      name: "Anthropic Claude",
      logo: Zap,
      plan: "Enterprise",
    },
    {
      name: "AI Development",
      logo: Cpu,
      plan: "Pro",
    },
    {
      name: "Cost Management",
      logo: DollarSign,
      plan: "Standard",
    },
  ],
  navMain: [
    {
      title: "Usage Overview",
      url: "#",
      icon: Home,
      isActive: true,
      items: [
        {
          title: "Dashboard",
          url: "#",
        },
        {
          title: "Real-time Metrics",
          url: "#",
        },
        {
          title: "Summary Reports",
          url: "#",
        },
      ],
    },
    {
      title: "Token Analytics",
      url: "#",
      icon: BarChart3,
      items: [
        {
          title: "Usage Trends",
          url: "#",
        },
        {
          title: "Token Breakdown",
          url: "#",
        },
        {
          title: "Context Windows",
          url: "#",
        },
      ],
    },
    {
      title: "Cost Analysis",
      url: "#",
      icon: DollarSign,
      items: [
        {
          title: "Spending Overview",
          url: "#",
        },
        {
          title: "Model Costs",
          url: "#",
        },
        {
          title: "Cost Forecasting",
          url: "#",
        },
      ],
    },
    {
      title: "Reports",
      url: "#",
      icon: FileText,
      items: [
        {
          title: "Usage Reports",
          url: "#",
        },
        {
          title: "Cost Reports",
          url: "#",
        },
        {
          title: "Export Data",
          url: "#",
        },
        {
          title: "Scheduled Reports",
          url: "#",
        },
      ],
    },
  ],
  projects: [
    {
      name: "Claude 3.5 Sonnet",
      url: "#",
      icon: Zap,
    },
    {
      name: "Claude 3 Haiku",
      url: "#",
      icon: Activity,
    },
    {
      name: "Batch Processing",
      url: "#",
      icon: Clock,
    },
  ],
}

function ApiStatus() {
  const [apiStatus] = useShinyOutput<{
    status: "connected" | "demo" | "error";
    message: string;
    last_update?: string;
  } | undefined>("api_status", undefined);

  if (!apiStatus) {
    return (
      <div className="px-3 py-2 border-t">
        <div className="flex items-center space-x-2 text-xs">
          <div className="h-2 w-2 bg-gray-400 rounded-full animate-pulse"></div>
          <span className="text-muted-foreground">Checking API...</span>
        </div>
      </div>
    );
  }

  const getStatusIcon = () => {
    switch (apiStatus.status) {
      case "connected":
        return <CheckCircle className="h-3 w-3 text-green-600" />;
      case "demo":
        return <AlertTriangle className="h-3 w-3 text-yellow-600" />;
      case "error":
        return <XCircle className="h-3 w-3 text-red-600" />;
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
    <div className="px-3 py-2 border-t">
      <div className="flex items-center space-x-2 mb-1">
        {getStatusIcon()}
        <Badge className={`${getStatusColor()} text-xs py-0 px-1`}>
          {getStatusText()}
        </Badge>
      </div>
      {apiStatus.status !== "connected" && (
        <p className="text-xs text-muted-foreground leading-tight">
          {apiStatus.message}
        </p>
      )}
    </div>
  );
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={data.teams} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavProjects projects={data.projects} />
      </SidebarContent>
      <ApiStatus />
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}