"use client";

import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp, TrendingDown, Users, CreditCard, BarChart2,
  Package, AlertTriangle, RefreshCw, Zap
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { KpiCard } from "@/components/ui/KpiCard";
import { OpportunityCard } from "@/components/ui/OpportunityCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { useAuth } from "@/hooks/useAuth";
import { dashboardApi, opportunitiesApi, actionsApi } from "@/lib/api";
import { formatRupeesRaw, formatRupees, formatDateTime } from "@/lib/utils";
import { useRouter } from "next/navigation";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart
} from "recharts";

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const { data: kpis, isLoading: kpisLoading, refetch: refetchKpis } = useQuery({
    queryKey: ["dashboard-kpis"],
    queryFn: () => dashboardApi.kpis().then((r) => r.data),
    enabled: !!user,
    staleTime: 60_000,
  });

  const { data: oppsData, isLoading: oppsLoading } = useQuery({
    queryKey: ["opportunities"],
    queryFn: () => opportunitiesApi.list().then((r) => r.data),
    enabled: !!user,
  });

  const { data: actionsData } = useQuery({
    queryKey: ["actions-pending"],
    queryFn: () => actionsApi.list("AWAITING_APPROVAL").then((r) => r.data),
    enabled: !!user,
  });

  const { data: invRisks } = useQuery({
    queryKey: ["inventory-risks"],
    queryFn: () => dashboardApi.inventoryRisks().then((r) => r.data),
    enabled: !!user,
  });

  if (authLoading) return null;

  const rev = kpis?.revenue_30d;
  const rev7 = kpis?.revenue_7d;
  const dailyData = rev?.daily_revenue?.slice(-14) ?? [];

  const topOpps = (oppsData?.opportunities ?? []).slice(0, 3);
  const pendingActions = actionsData?.actions ?? [];
  const stockoutItems = (invRisks?.risks ?? []).filter((r: { status: string }) => r.status === "STOCKOUT_RISK");

  const overduePaise = kpis?.overdue_paise ?? 0;
  const totalCustomers = kpis?.total_customers ?? 0;

  const merchantName = user?.merchant_name ?? "your store";
  const firstName = user?.full_name?.split(" ")[0] ?? "Merchant";
  const now = new Date();
  const hour = now.getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <AppShell>
      <div className="px-4 lg:px-8 py-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-xl font-semibold">
              {greeting}, {firstName} 👋
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              {merchantName} — here&apos;s what needs your attention today
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => { refetchKpis(); }}
              className="p-2 rounded-lg border border-border hover:bg-muted text-muted-foreground transition-colors"
              aria-label="Refresh dashboard"
            >
              <RefreshCw size={15} />
            </button>
            <button
              onClick={() => router.push("/command-center")}
              className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              <Zap size={14} aria-hidden="true" />
              Grow my business
            </button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          <KpiCard
            title="Revenue (30d)"
            value={rev ? formatRupeesRaw(rev.gmv_rupees ?? 0) : "—"}
            change={rev?.growth_pct != null ? `${Math.abs(rev.growth_pct).toFixed(1)}%` : undefined}
            changePositive={(rev?.growth_pct ?? 0) >= 0}
            icon={TrendingUp}
            loading={kpisLoading}
          />
          <KpiCard
            title="Transactions (30d)"
            value={rev?.transaction_count?.toLocaleString("en-IN") ?? "—"}
            subtitle="successful payments"
            icon={BarChart2}
            loading={kpisLoading}
          />
          <KpiCard
            title="Total Customers"
            value={totalCustomers.toLocaleString("en-IN")}
            icon={Users}
            loading={kpisLoading}
          />
          <KpiCard
            title="Pending Collections"
            value={overduePaise ? formatRupees(overduePaise) : "₹0"}
            change={kpis?.overdue_count ? `${kpis.overdue_count} overdue` : undefined}
            changePositive={false}
            icon={CreditCard}
            loading={kpisLoading}
          />
        </div>

        {/* Revenue Chart */}
        {dailyData.length > 0 && (
          <div className="bg-card border border-border rounded-xl p-5 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="font-semibold">Revenue Trend (last 14 days)</h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {rev?.growth_pct != null && (
                    <span className={rev.growth_pct >= 0 ? "text-success" : "text-danger"}>
                      {rev.growth_pct >= 0 ? "▲" : "▼"} {Math.abs(rev.growth_pct).toFixed(1)}% vs prior 30d
                    </span>
                  )}
                </p>
              </div>
            </div>
            <div className="h-40" role="img" aria-label="Revenue trend chart">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={dailyData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10 }}
                    tickFormatter={(v) => new Date(v).toLocaleDateString("en-IN", { day: "2-digit", month: "short" })}
                  />
                  <YAxis
                    tick={{ fontSize: 10 }}
                    tickFormatter={(v) => `₹${(v / 100).toLocaleString("en-IN")}`}
                  />
                  <Tooltip
                    formatter={(v: number) => [`₹${(v / 100).toLocaleString("en-IN")}`, "Revenue"]}
                    labelFormatter={(l) => new Date(l).toLocaleDateString("en-IN", { day: "2-digit", month: "short" })}
                  />
                  <Area
                    type="monotone"
                    dataKey="revenue_paise"
                    stroke="#2563eb"
                    strokeWidth={2}
                    fill="url(#revenueGrad)"
                    dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Growth Opportunities */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold">Growth Opportunities</h2>
              <button
                onClick={() => router.push("/growth")}
                className="text-sm text-brand-600 hover:underline"
              >
                View all →
              </button>
            </div>
            {oppsLoading ? (
              <div className="space-y-3">
                {[1, 2].map((i) => (
                  <div key={i} className="h-32 bg-muted rounded-xl animate-pulse" />
                ))}
              </div>
            ) : topOpps.length === 0 ? (
              <div className="bg-card border border-border rounded-xl p-8 text-center text-muted-foreground text-sm">
                No opportunities found. Run &quot;Grow my business&quot; to discover them.
              </div>
            ) : (
              <div className="space-y-3">
                {topOpps.map((opp) => (
                  <OpportunityCard
                    key={opp.id}
                    opportunity={opp}
                    onAction={() => router.push(`/growth?opp=${opp.id}`)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Right column: Actions + Inventory */}
          <div className="space-y-6">
            {/* Pending Actions */}
            {pendingActions.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h2 className="font-semibold flex items-center gap-2">
                    <span className="w-2 h-2 bg-warning rounded-full animate-pulse" aria-hidden="true" />
                    Action Required
                    <span className="text-xs bg-warning-light text-warning-dark px-1.5 py-0.5 rounded-full">
                      {pendingActions.length}
                    </span>
                  </h2>
                  <button
                    onClick={() => router.push("/actions")}
                    className="text-sm text-brand-600 hover:underline"
                  >
                    View all →
                  </button>
                </div>
                <div className="space-y-2">
                  {pendingActions.slice(0, 3).map((action: { id: string; action_type: string; status: string; estimated_impact_rupees: number }) => (
                    <div
                      key={action.id}
                      className="bg-card border border-border rounded-xl p-3 flex items-center justify-between cursor-pointer hover:bg-muted transition-colors"
                      onClick={() => router.push(`/actions/${action.id}`)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === "Enter" && router.push(`/actions/${action.id}`)}
                    >
                      <div>
                        <p className="text-sm font-medium capitalize">
                          {action.action_type.replace(/_/g, " ")}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Est. ₹{action.estimated_impact_rupees?.toLocaleString("en-IN") ?? 0}
                        </p>
                      </div>
                      <StatusBadge status={action.status} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Inventory Risks */}
            {stockoutItems.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h2 className="font-semibold flex items-center gap-2">
                    <AlertTriangle size={15} className="text-warning" aria-hidden="true" />
                    Inventory Risk
                  </h2>
                  <button
                    onClick={() => router.push("/inventory")}
                    className="text-sm text-brand-600 hover:underline"
                  >
                    View all →
                  </button>
                </div>
                <div className="space-y-2">
                  {stockoutItems.slice(0, 3).map((item: { product_id: string; product_name: string; days_until_stockout: number; restock_quantity: number }) => (
                    <div
                      key={item.product_id}
                      className="bg-card border border-border rounded-xl p-3 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-2">
                        <Package size={14} className="text-warning" aria-hidden="true" />
                        <div>
                          <p className="text-sm font-medium">{item.product_name}</p>
                          <p className="text-xs text-danger">
                            Stock-out in ~{item.days_until_stockout.toFixed(0)} days
                          </p>
                        </div>
                      </div>
                      <span className="text-xs bg-danger-light text-danger-dark px-2 py-0.5 rounded-full">
                        Restock {item.restock_quantity}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Data freshness */}
        {kpis?.revenue_30d?.data_as_of && (
          <p className="mt-6 text-xs text-muted-foreground text-right">
            Data as of {formatDateTime(kpis.revenue_30d.data_as_of)} IST
          </p>
        )}
      </div>
    </AppShell>
  );
}
