"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, TrendingUp, Zap, CheckSquare, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

const MOBILE_NAV = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/growth", label: "Growth", icon: TrendingUp },
  { href: "/command-center", label: "Mission", icon: Zap },
  { href: "/actions", label: "Actions", icon: CheckSquare },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav
      className="lg:hidden fixed bottom-0 left-0 right-0 bg-card border-t border-border z-50 safe-bottom"
      aria-label="Mobile navigation"
    >
      <ul className="flex items-center justify-around px-2 py-2" role="list">
        {MOBILE_NAV.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  "flex flex-col items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium min-w-[44px] min-h-[44px] justify-center transition-colors",
                  active ? "text-brand-600" : "text-muted-foreground"
                )}
                aria-current={active ? "page" : undefined}
              >
                <item.icon size={20} aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
