"use client";

import { SandboxBanner } from "@/components/SandboxBanner";
import { Sidebar } from "@/components/layout/Sidebar";
import { MobileNav } from "@/components/layout/MobileNav";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <SandboxBanner />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main
          className="flex-1 overflow-y-auto pb-20 lg:pb-6"
          id="main-content"
          role="main"
        >
          {children}
        </main>
      </div>
      <MobileNav />
    </div>
  );
}
