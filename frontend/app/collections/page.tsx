"use client";

import { useQuery } from "@tanstack/react-query";
import { CreditCard, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/hooks/useAuth";
import { dashboardApi } from "@/lib/api";
import { formatRupeesRaw, formatDate } from "@/lib/utils";
import { SimulatedBadge } from "@/components/ui/SimulatedBadge";
import { cn } from "@/lib/utils";

export default function CollectionsPage() {
  const { user, loading } = useAuth();
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["overdue-payments"],
    queryFn: () => dashboardApi.overduePayments().then((r) => r.data),
    enabled: !!user,
  });

  if (loading) return null;
  const payments = data?.payments ?? [];

  return (
    <AppShell>
      <div className="px-4 lg:px-8 py-6 max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="flex items-center gap-2">
              <CreditCard size={20} className="text-brand-600" />
              Collections Recovery
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Overdue payments, aging analysis, and recovery probability
            </p>
          </div>
          <button onClick={() => refetch()} className="p-2 rounded-lg border border-border hover:bg-muted text-muted-foreground">
            <RefreshCw size={15} />
          </button>
        </div>

        {/* Summary */}
        {data && (
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-5">
            <div className="bg-card border border-border rounded-xl p-4">
              <p className="text-xs text-muted-foreground">Total Overdue</p>
              <p className="text-xl font-bold rupee text-danger">{formatRupeesRaw(data.total_overdue_rupees ?? 0)}</p>
              <p className="text-xs text-muted-foreground">{data.overdue_count ?? 0} payments</p>
            </div>
            <div className="bg-card border border-border rounded-xl p-4">
              <p className="text-xs text-muted-foreground">Expected Recovery</p>
              <p className="text-xl font-bold rupee text-success">{formatRupeesRaw(data.expected_recovery_rupees ?? 0)}</p>
              <p className="text-xs text-muted-foreground">Probability-weighted</p>
            </div>
            <div className="bg-card border border-border rounded-xl p-4 col-span-2 lg:col-span-1">
              <p className="text-xs text-muted-foreground mb-1">Aging Buckets</p>
              {Object.entries(data.aging_buckets_paise ?? {}).map(([bucket, paise]) => (
                <div key={bucket} className="flex justify-between text-xs py-0.5">
                  <span className="text-muted-foreground">{bucket}</span>
                  <span className="font-medium rupee">{formatRupeesRaw((paise as number) / 100)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Payments list */}
        {isLoading ? (
          <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-16 bg-muted rounded-xl animate-pulse" />)}</div>
        ) : payments.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
            No overdue payments found. Great job staying on top of collections! 🎉
          </div>
        ) : (
          <div className="bg-card border border-border rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm" role="table">
                <thead>
                  <tr className="border-b border-border bg-muted text-xs text-muted-foreground uppercase">
                    <th className="text-left px-4 py-3 font-medium">Customer</th>
                    <th className="text-right px-4 py-3 font-medium">Amount</th>
                    <th className="text-right px-4 py-3 font-medium">Due Date</th>
                    <th className="text-right px-4 py-3 font-medium">Days Overdue</th>
                    <th className="text-right px-4 py-3 font-medium">Recovery Prob.</th>
                    <th className="text-right px-4 py-3 font-medium">Expected</th>
                    <th className="text-center px-4 py-3 font-medium">Bucket</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.slice(0, 20).map((p: {
                    payment_id: string;
                    customer_name: string;
                    amount_rupees: number;
                    due_date: string;
                    days_overdue: number;
                    recovery_probability: number;
                    expected_recovery_paise: number;
                    aging_bucket: string;
                    reminder_sent_count: number;
                  }) => (
                    <tr key={p.payment_id} className="border-b border-border hover:bg-muted/50">
                      <td className="px-4 py-3">
                        <p className="font-medium">{p.customer_name}</p>
                        {p.reminder_sent_count > 0 && (
                          <p className="text-xs text-muted-foreground">{p.reminder_sent_count} reminder(s) sent</p>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right font-semibold rupee">{formatRupeesRaw(p.amount_rupees)}</td>
                      <td className="px-4 py-3 text-right text-muted-foreground">{formatDate(p.due_date)}</td>
                      <td className={cn("px-4 py-3 text-right font-semibold",
                        p.days_overdue > 60 ? "text-danger" : p.days_overdue > 30 ? "text-warning" : "text-foreground"
                      )}>
                        {p.days_overdue}d
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={cn("font-medium",
                          p.recovery_probability > 0.6 ? "text-success" : p.recovery_probability > 0.3 ? "text-warning" : "text-danger"
                        )}>
                          {Math.round(p.recovery_probability * 100)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right rupee text-success font-medium">
                        {formatRupeesRaw(p.expected_recovery_paise / 100)}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-full">
                          {p.aging_bucket}
                        </span>
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
          <span>Recovery probabilities are estimates based on historical patterns</span>
        </div>
      </div>
    </AppShell>
  );
}
