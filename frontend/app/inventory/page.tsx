"use client";

import { useQuery } from "@tanstack/react-query";
import { Package, AlertTriangle, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/hooks/useAuth";
import { dashboardApi } from "@/lib/api";
import { formatRupeesRaw } from "@/lib/utils";
import { SimulatedBadge } from "@/components/ui/SimulatedBadge";
import { cn } from "@/lib/utils";

export default function InventoryPage() {
  const { user, loading } = useAuth();
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["inventory-risks"],
    queryFn: () => dashboardApi.inventoryRisks().then((r) => r.data),
    enabled: !!user,
  });

  if (loading) return null;
  const risks = data?.risks ?? [];

  return (
    <AppShell>
      <div className="px-4 lg:px-8 py-6 max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="flex items-center gap-2">
              <Package size={20} className="text-brand-600" />
              Inventory Intelligence
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Stock levels, demand velocity, and restock recommendations
            </p>
          </div>
          <button onClick={() => refetch()} className="p-2 rounded-lg border border-border hover:bg-muted text-muted-foreground">
            <RefreshCw size={15} />
          </button>
        </div>

        {/* Summary */}
        {data && (
          <div className="grid grid-cols-3 gap-3 mb-5">
            {[
              { label: "Total Products", value: data.total_products ?? 0, color: "text-foreground" },
              { label: "Stockout Risk", value: data.stockout_risk_count ?? 0, color: "text-danger" },
              { label: "Low Stock", value: data.low_stock_count ?? 0, color: "text-warning" },
            ].map((s) => (
              <div key={s.label} className="bg-card border border-border rounded-xl p-3 text-center">
                <p className="text-xs text-muted-foreground">{s.label}</p>
                <p className={cn("text-2xl font-bold", s.color)}>{s.value}</p>
              </div>
            ))}
          </div>
        )}

        {/* Table */}
        {isLoading ? (
          <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-16 bg-muted rounded-xl animate-pulse" />)}</div>
        ) : risks.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
            No inventory data found. Run <code>make seed</code> to populate.
          </div>
        ) : (
          <div className="bg-card border border-border rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm" role="table">
                <thead>
                  <tr className="border-b border-border bg-muted text-xs text-muted-foreground uppercase">
                    <th className="text-left px-4 py-3 font-medium">Product</th>
                    <th className="text-right px-4 py-3 font-medium">Stock</th>
                    <th className="text-right px-4 py-3 font-medium">Daily Demand</th>
                    <th className="text-right px-4 py-3 font-medium">Days Left</th>
                    <th className="text-right px-4 py-3 font-medium">Revenue at Risk</th>
                    <th className="text-center px-4 py-3 font-medium">Status</th>
                    <th className="text-right px-4 py-3 font-medium">Restock Qty</th>
                  </tr>
                </thead>
                <tbody>
                  {risks.slice(0, 20).map((r: {
                    product_id: string;
                    product_name: string;
                    category?: string;
                    quantity_on_hand: number;
                    avg_daily_demand: number;
                    days_until_stockout: number;
                    revenue_at_risk_rupees: number;
                    status: string;
                    restock_quantity: number;
                  }) => (
                    <tr key={r.product_id} className="border-b border-border hover:bg-muted/50 transition-colors">
                      <td className="px-4 py-3">
                        <p className="font-medium">{r.product_name}</p>
                        {r.category && <p className="text-xs text-muted-foreground">{r.category}</p>}
                      </td>
                      <td className="px-4 py-3 text-right font-mono">{r.quantity_on_hand}</td>
                      <td className="px-4 py-3 text-right font-mono">{r.avg_daily_demand?.toFixed(1)}/day</td>
                      <td className={cn("px-4 py-3 text-right font-semibold", r.days_until_stockout < 7 ? "text-danger" : "text-foreground")}>
                        {r.days_until_stockout?.toFixed(0)} days
                      </td>
                      <td className="px-4 py-3 text-right rupee">
                        {r.revenue_at_risk_rupees > 0 ? formatRupeesRaw(r.revenue_at_risk_rupees) : "—"}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium",
                          r.status === "STOCKOUT_RISK" ? "bg-danger-light text-danger-dark" :
                          r.status === "LOW_STOCK" ? "bg-warning-light text-warning-dark" :
                          "bg-success-light text-success-dark"
                        )}>
                          {r.status.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-semibold">
                        {r.restock_quantity > 0 ? r.restock_quantity : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
          <SimulatedBadge />
          <span>Inventory data from Sandbox · Synthetic Demo Data</span>
        </div>
      </div>
    </AppShell>
  );
}
