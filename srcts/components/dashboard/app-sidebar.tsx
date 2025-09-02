"use client";

import {
  Activity,
  BarChart3,
  Clock,
  Cpu,
  DollarSign,
  FileText,
  Home,
  LineChart,
  PieChart,
  Settings2,
  Table,
  TrendingUp,
  Zap,
} from "lucide-react";
import * as React from "react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar";
import { DemoModeToggle } from "../DemoModeToggle";
import { FiltersSidebar } from "./FiltersSidebar";
import { NavMain } from "./nav-main";
import { NavProjects } from "./nav-projects";
import { NavUser } from "./nav-user";
import { TeamSwitcher } from "./team-switcher";

// Anthropic API Dashboard navigation data
const data = {
  user: {
    name: "API User",
    email: "admin@company.com",
    avatar: "",
  },
  teams: [
    {
      name: "Anthropic",
      logo: Zap,
      plan: "API Analytics",
    },
    // {
    //   name: "AI Development",
    //   logo: Cpu,
    //   plan: "Pro",
    // },
    // {
    //   name: "Cost Management",
    //   logo: DollarSign,
    //   plan: "Standard",
    // },
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
};


export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible='icon' {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={data.teams} />
      </SidebarHeader>
      <SidebarContent>
        <div className='mb-auto'>
          <FiltersSidebar />
        </div>
        {/* <NavMain items={data.navMain} /> */}
        {/* <NavProjects projects={data.projects} /> */}
      </SidebarContent>
      <SidebarFooter>
        <div className='px-3 py-2 border-t'>
          <DemoModeToggle />
        </div>
        {/* <NavUser user={data.user} /> */}
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
