"use client"

import * as React from "react"
import {
  BarChart3,
  Database,
  Home,
  LineChart,
  PieChart,
  Settings2,
  Table,
  TrendingUp,
  Users,
  Activity,
} from "lucide-react"

import { NavMain } from "./nav-main"
import { NavProjects } from "./nav-projects"
import { NavUser } from "./nav-user"
import { TeamSwitcher } from "./team-switcher"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar"

// Dashboard navigation data
const data = {
  user: {
    name: "Dashboard User",
    email: "user@example.com",
    avatar: "",
  },
  teams: [
    {
      name: "Analytics Inc",
      logo: BarChart3,
      plan: "Pro",
    },
    {
      name: "Data Corp",
      logo: Database,
      plan: "Enterprise",
    },
    {
      name: "Insights Co",
      logo: TrendingUp,
      plan: "Starter",
    },
  ],
  navMain: [
    {
      title: "Dashboard",
      url: "#",
      icon: Home,
      isActive: true,
      items: [
        {
          title: "Overview",
          url: "#",
        },
        {
          title: "Analytics",
          url: "#",
        },
        {
          title: "Reports",
          url: "#",
        },
      ],
    },
    {
      title: "Visualizations",
      url: "#",
      icon: BarChart3,
      items: [
        {
          title: "Charts",
          url: "#",
        },
        {
          title: "Graphs",
          url: "#",
        },
        {
          title: "Custom Reports",
          url: "#",
        },
      ],
    },
    {
      title: "Data Management",
      url: "#",
      icon: Database,
      items: [
        {
          title: "Tables",
          url: "#",
        },
        {
          title: "Import/Export",
          url: "#",
        },
        {
          title: "Data Sources",
          url: "#",
        },
      ],
    },
    {
      title: "Settings",
      url: "#",
      icon: Settings2,
      items: [
        {
          title: "General",
          url: "#",
        },
        {
          title: "Preferences",
          url: "#",
        },
        {
          title: "API Keys",
          url: "#",
        },
        {
          title: "Team Settings",
          url: "#",
        },
      ],
    },
  ],
  projects: [
    {
      name: "Sales Analytics",
      url: "#",
      icon: TrendingUp,
    },
    {
      name: "User Insights",
      url: "#",
      icon: Users,
    },
    {
      name: "Performance Metrics",
      url: "#",
      icon: Activity,
    },
  ],
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
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}