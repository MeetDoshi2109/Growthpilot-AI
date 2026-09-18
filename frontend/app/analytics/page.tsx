"use client";
import { useQuery } from "@tanstack/react-query";
import { BarChart2 } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/hooks/useAuth";
import { dashboardApi } from "@/lib/api";
import { formatRupeesRaw } from "@/lib/utils";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function AnalyticsPage() {
  const { user, loading } = useAuth();
  const { data: rev30 } = useQuery({
    queryKey: ["revenue-30"],
    queryFn: () => dashboardApi.revenue(30).then((r) => r.data),
    enabled: !!user,
  });
  const { data: attr } = useQuery({
    queryKey: ["attribution"],
    queryFn: () => dashboardApi.attribution().then((r) => r.data),
    enabled: !!user,
  });
  const { data: ret } = useQuery({
    queryKey: ["retention"],
    queryFn: () => dashboardApi.retention().then((r) => r.data),
    enabled: !!user,
  });

  if (loading) return null;
  const daily = rev30?.daily_revenue ?? [];

  return (
    <AppShell>
      <div className="px-4 lg:px-8 py-6 max-w-5xl mx-auto">
        <h1 className="flex items-center gap-2 mb-6">
          <BarChart2 size={20} className="text-brand-600" />
          Analytics
        </h1>

        <div className="grid lg:grid-cols-3 gap-4 mb-6">
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs text-muted-foreground">GMV (30d)</p>
            <p className="text-xl font-bold rupee">{formatRupeesRaw(rev30?.gmv_rupees ?? 0)}</p>
            {rev30?.growth_pct != null && (
              <p className={`text-xs font-medium ${rev30.growth_pct >= 0 ? "text-success" : "text-danger"}`}>
                {rev30.growth_pct >= 0 ? "▲" : "▼"} {Math.abs(rev30.growth_pct).toFixed(1)}% vs prior
              </p>
            )}
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs text-muted-foreground">Repeat Purchase Rate</p>
            <p className="text-xl font-bold">{ret?.repeat_purchase_rate?.toFixed(1) ?? "—"}%</p>
            <p className="text-xs text-muted-foreground">{ret?.repeat_customers ?? 0} repeat customers</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs text-muted-foreground">Payment Success Rate</p>
            <p className="text-xl font-bold">{rev30?.payment_success_rate?.toFixed(1) ?? "—"}%</p>
            <p className="text-xs text-muted-foreground">{rev30?.transaction_count?.toLocaleString("en-IN")} transactions</p>
          </div>
        </div>

        {daily.length > 0 && (
          <div className="bg-card border border-border rounded-xl p-5 mb-5">
            <h2 className="font-semibold mb-3">Daily Revenue (last 30 days)</h2>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={daily}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }}
                    tickFormatter={(v) => new Date(v).toLocaleDateString("en-IN", { day: "2-digit", month: "short" })} />
                  <YAxis tick={{ fontSize: 10 }}
                    tickFormatter={(v) => `₹${(v / 100).toLocaleString("en-IN")}`} />
                  <Tooltip
                    formatter={(v: number) => [`₹${(v / 100).toLocaleString("en-IN")}`, "Revenue"]}
                    labelFormatter={(l) => new Date(l).toLocaleDateString("en-IN", { day: "2-digit", month: "short" })} />
                  <Area type="monotone" dataKey="revenue_paise" stroke="#2563eb" strokeWidth={2}
                    fill="#2563eb" fillOpacity={0.1} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {attr && !attr.unavailable && (
          <div className="bg-card border border-border rounded-xl p-5">
            <h2 className="font-semibold mb-3">Revenue Change Attribution (last 14d)</h2>
            <p className={`text-sm font-medium mb-3 ${(attr.change_pct ?? 0) >= 0 ? "text-success" : "text-danger"}`}>
              {(attr.change_pct ?? 0) >= 0 ? "▲" : "▼"} {Math.abs(attr.change_pct ?? 0).toFixed(1)}% — Primary driver: {attr.primary_driver?.replace(/_/g, " ")}
            </p>
            <div className="space-y-2">
              {Object.entries(attr.attribution ?? {}).map(([key, val]) => (
                <div key={key} className="flex justify-between text-sm">
                  <span className="text-muted-foreground capitalize">{key.replace(/_/g, " ")}</span>
                  <span className={`font-medium rupee ${(val as number) >= 0 ? "text-success" : "text-danger"}`}>
                    {(val as number) >= 0 ? "+" : ""}{formatRupeesRaw(Math.abs((val as number) / 100))}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
