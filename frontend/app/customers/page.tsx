"use client";
import { useQuery } from "@tanstack/react-query";
import { Users } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/hooks/useAuth";
import { dashboardApi } from "@/lib/api";
import { formatRupeesRaw } from "@/lib/utils";

export default function CustomersPage() {
  const { user, loading } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["inactive-customers"],
    queryFn: () => dashboardApi.inactiveCustomers().then((r) => r.data),
    enabled: !!user,
  });

  if (loading) return null;
  const customers = data?.customers ?? [];

  return (
    <AppShell>
      <div className="px-4 lg:px-8 py-6 max-w-5xl mx-auto">
        <h1 className="flex items-center gap-2 mb-2">
          <Users size={20} className="text-brand-600" />
          Customers
        </h1>
        <p className="text-sm text-muted-foreground mb-6">
          {data?.inactive_count ?? 0} inactive customers (>{data?.cadence_multiplier_used ?? 2}× their own buying cadence)
          &nbsp;·&nbsp; {data?.total_eligible ?? 0} total eligible
        </p>

        {isLoading ? (
          <div className="space-y-2">{[1,2,3,4,5].map(i => <div key={i} className="h-14 bg-muted rounded-xl animate-pulse" />)}</div>
        ) : customers.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-10 text-center text-sm text-muted-foreground">
            No inactive customers found.
          </div>
        ) : (
          <div className="bg-card border border-border rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted text-xs text-muted-foreground uppercase">
                    <th className="text-left px-4 py-3">Customer</th>
                    <th className="text-right px-4 py-3">Days Inactive</th>
                    <th className="text-right px-4 py-3">Own Cadence</th>
                    <th className="text-right px-4 py-3">Overdue By</th>
                    <th className="text-right px-4 py-3">Avg Order</th>
                    <th className="text-right px-4 py-3">Orders</th>
                    <th className="text-center px-4 py-3">SMS Consent</th>
                  </tr>
                </thead>
                <tbody>
                  {customers.slice(0, 50).map((c: {
                    customer_id: string; name: string; days_since_last_purchase: number;
                    median_cadence_days: number; overdue_by_days: number;
                    avg_order_value_paise: number; total_orders: number; sms_consent: boolean;
                  }) => (
                    <tr key={c.customer_id} className="border-b border-border hover:bg-muted/50">
                      <td className="px-4 py-3 font-medium">{c.name}</td>
                      <td className="px-4 py-3 text-right text-danger font-semibold">{c.days_since_last_purchase}d</td>
                      <td className="px-4 py-3 text-right text-muted-foreground">{c.median_cadence_days?.toFixed(0)}d</td>
                      <td className="px-4 py-3 text-right text-warning font-medium">{c.overdue_by_days?.toFixed(0)}d</td>
                      <td className="px-4 py-3 text-right rupee">{formatRupeesRaw(c.avg_order_value_paise / 100)}</td>
                      <td className="px-4 py-3 text-right">{c.total_orders}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={c.sms_consent ? "text-success text-xs" : "text-danger text-xs"}>
                          {c.sms_consent ? "✓" : "✗"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
