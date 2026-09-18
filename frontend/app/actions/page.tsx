"use client";

import { useQuery } from "@tanstack/react-query";
import { CheckSquare, Clock, Filter } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { SimulatedBadge } from "@/components/ui/SimulatedBadge";
import { useAuth } from "@/hooks/useAuth";
import { actionsApi } from "@/lib/api";
import { formatRupeesRaw, formatDateTime } from "@/lib/utils";
import { useRouter } from "next/navigation";

const STATUS_FILTERS = [
  { label: "All", value: "" },
  { label: "Needs Approval", value: "AWAITING_APPROVAL" },
  { label: "Verified", value: "VERIFIED" },
  { label: "Rejected", value: "REJECTED" },
];

export default function ActionsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["actions", statusFilter],
    queryFn: () => actionsApi.list(statusFilter || undefined).then((r) => r.data),
    enabled: !!user,
  });

  if (authLoading) return null;

  const actions = data?.actions ?? [];
  const pendingCount = actions.filter((a: { status: string }) => a.status === "AWAITING_APPROVAL").length;

  return (
    <AppShell>
      <div className="px-4 lg:px-8 py-6 max-w-5xl mx-auto">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="flex items-center gap-2">
              <CheckSquare size={20} className="text-brand-600" aria-hidden="true" />
              AI Action Center
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Review, approve, and track all AI-proposed actions
            </p>
          </div>
          {pendingCount > 0 && (
            <span className="flex items-center gap-1.5 bg-warning-light text-warning-dark text-sm font-medium px-3 py-1.5 rounded-full">
              <Clock size={13} aria-hidden="true" />
              {pendingCount} pending
            </span>
          )}
        </div>

        {/* Status filter */}
        <div className="flex gap-2 mb-4 overflow-x-auto pb-1" role="group" aria-label="Filter actions by status">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setStatusFilter(f.value)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                statusFilter === f.value
                  ? "bg-brand-600 text-white"
                  : "bg-muted text-muted-foreground hover:bg-accent"
              }`}
              aria-pressed={statusFilter === f.value}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Actions list */}
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 bg-muted rounded-xl animate-pulse" />
            ))}
          </div>
        ) : actions.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-12 text-center">
            <CheckSquare size={36} className="text-muted-foreground mx-auto mb-3" />
            <p className="font-medium">No actions found</p>
            <p className="text-sm text-muted-foreground mt-1">
              Actions are created from Growth Opportunities.
            </p>
          </div>
        ) : (
          <div className="space-y-3" role="list">
            {actions.map((action: {
              id: string;
              action_type: string;
              risk_tier: string;
              status: string;
              estimated_impact_rupees: number;
              simulated: boolean;
              proposed_at: string;
              verified_at?: string;
            }) => (
              <div
                key={action.id}
                className="bg-card border border-border rounded-xl p-4 cursor-pointer hover:shadow-sm transition-shadow"
                onClick={() => router.push(`/actions/${action.id}`)}
                role="listitem"
                tabIndex={0}
                onKeyDown={(e) => e.key === "Enter" && router.push(`/actions/${action.id}`)}
                aria-label={`Action: ${action.action_type.replace(/_/g, " ")}, status: ${action.status}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-medium capitalize text-sm">
                        {action.action_type.replace(/_/g, " ")}
                      </p>
                      <span className="text-xs px-1.5 py-0.5 bg-muted rounded font-mono">{action.risk_tier}</span>
                      {action.simulated && <SimulatedBadge />}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {action.proposed_at ? `Proposed ${formatDateTime(action.proposed_at)}` : ""}
                      {action.verified_at ? ` · Verified ${formatDateTime(action.verified_at)}` : ""}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                    <StatusBadge status={action.status} />
                    {action.estimated_impact_rupees > 0 && (
                      <span className="text-xs text-success font-medium rupee">
                        ₹{action.estimated_impact_rupees.toLocaleString("en-IN")}
                      </span>
                    )}
                  </div>
                </div>
                {action.status === "AWAITING_APPROVAL" && (
                  <div className="mt-3 pt-3 border-t border-border flex gap-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); router.push(`/actions/${action.id}`); }}
                      className="flex-1 bg-brand-600 hover:bg-brand-700 text-white py-1.5 rounded-lg text-xs font-medium transition-colors"
                    >
                      Review & Approve
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); router.push(`/actions/${action.id}`); }}
                      className="px-3 py-1.5 border border-border rounded-lg text-xs text-muted-foreground hover:bg-muted transition-colors"
                    >
                      View details
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
