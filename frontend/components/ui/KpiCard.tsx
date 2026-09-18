"use client";

import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface KpiCardProps {
  title: string;
  value: string;
  change?: string;
  changePositive?: boolean;
  icon?: LucideIcon;
  iconColor?: string;
  subtitle?: string;
  loading?: boolean;
  className?: string;
}

export function KpiCard({
  title,
  value,
  change,
  changePositive,
  icon: Icon,
  iconColor = "text-brand-600",
  subtitle,
  loading,
  className,
}: KpiCardProps) {
  if (loading) {
    return (
      <div className={cn("bg-card border border-border rounded-xl p-5 animate-pulse", className)}>
        <div className="h-4 bg-muted rounded w-24 mb-3" />
        <div className="h-8 bg-muted rounded w-32 mb-2" />
        <div className="h-3 bg-muted rounded w-20" />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "bg-card border border-border rounded-xl p-5 hover:shadow-sm transition-shadow",
        className
      )}
    >
      <div className="flex items-start justify-between">
        <p className="text-sm text-muted-foreground font-medium">{title}</p>
        {Icon && (
          <span className={cn("p-1.5 rounded-lg bg-muted", iconColor)}>
            <Icon size={16} aria-hidden="true" />
          </span>
        )}
      </div>
      <p className="mt-2 text-2xl font-semibold rupee tracking-tight">{value}</p>
      <div className="mt-1 flex items-center gap-2">
        {change && (
          <span
            className={cn(
              "text-xs font-medium px-1.5 py-0.5 rounded-full",
              changePositive
                ? "bg-success-light text-success-dark"
                : "bg-danger-light text-danger-dark"
            )}
          >
            {changePositive ? "+" : ""}{change}
          </span>
        )}
        {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
      </div>
    </div>
  );
}
