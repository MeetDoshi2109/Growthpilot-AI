"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, TrendingUp, Users, Package, CreditCard,
  Zap, MessageSquare, Settings, Shield, BarChart2,
  FileText, CheckSquare, LogOut, Bot
} from "lucide-react";
import { cn } from "@/lib/utils";
import { authApi } from "@/lib/api";
import { clearUser } from "@/lib/auth";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/growth", label: "Growth", icon: TrendingUp },
  { href: "/command-center", label: "AI Command Center", icon: Zap },
  { href: "/actions", label: "Action Center", icon: CheckSquare },
  { href: "/customers", label: "Customers", icon: Users },
  { href: "/inventory", label: "Inventory", icon: Package },
  { href: "/collections", label: "Collections", icon: CreditCard },
  { href: "/analytics", label: "Analytics", icon: BarChart2 },
  { href: "/financial-readiness", label: "Financial Readiness", icon: FileText },
  { href: "/ai-assistant", label: "AI Assistant", icon: Bot },
  { href: "/audit-log", label: "Audit Log", icon: Shield },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {}
    clearUser();
    router.push("/login");
    toast.success("Logged out");
  };

  return (
    <aside className="hidden lg:flex flex-col w-60 bg-card border-r border-border h-screen sticky top-0 z-40">
      {/* Logo */}
      <div className="px-5 py-4 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <Zap size={16} className="text-white" />
          </div>
          <div>
            <p className="font-bold text-sm leading-none">GrowthPilot AI</p>
            <p className="text-xs text-muted-foreground mt-0.5">Paytm Merchant Intelligence</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto" aria-label="Main navigation">
        <ul className="space-y-0.5" role="list">
          {NAV_ITEMS.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    active
                      ? "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                  aria-current={active ? "page" : undefined}
                >
                  <item.icon size={16} aria-hidden="true" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Logout */}
      <div className="px-3 pb-4 border-t border-border pt-3">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          aria-label="Log out"
        >
          <LogOut size={16} aria-hidden="true" />
          Logout
        </button>
      </div>
    </aside>
  );
}
