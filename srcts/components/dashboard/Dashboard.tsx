import React from "react";
import { AppSidebar } from "./app-sidebar";
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { StatsCards } from "./StatsCards";
import { ChartsSection } from "./ChartsSection";
import { DataTableSection } from "./DataTableSection";
import { TextInputCard } from "../TextInputCard";
import { ButtonEventCard } from "../ButtonEventCard";
import { PlotCard } from "../PlotCard";

export function Dashboard() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem className="hidden md:block">
                  <BreadcrumbLink href="#">Dashboard</BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator className="hidden md:block" />
                <BreadcrumbItem>
                  <BreadcrumbPage>Overview</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-6 p-4 pt-0">
          {/* KPI Stats Cards */}
          <StatsCards />

          {/* Charts Section */}
          <ChartsSection />

          {/* Interactive Components (existing) */}
          <div className="grid gap-6 md:grid-cols-2">
            <TextInputCard />
            <ButtonEventCard />
          </div>

          {/* Data Section */}
          <div className="grid gap-6 md:grid-cols-2">
            <DataTableSection />
            <PlotCard />
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}