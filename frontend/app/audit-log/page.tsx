"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Shield, CheckCircle, XCircle, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { SimulatedBadge } from "@/components/ui/SimulatedBadge";
import { useAuth } from "@/hooks/useAuth";
import { auditApi } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import { cn } from "@/lib/utils";

export default function AuditLogPage() {
  const { user, loading: authLoading } = useAuth();
  const [limit, setLimit] = useState(50);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["audit-log", limit],
    queryFn: () => auditApi.list({ limit }).then((r) => r.data),
    enabled: !!user,
  });

  const { data: chainData, refetch: refetchChain } = useQuery({
    queryKey: ["audit-chain"],
    queryFn: () => auditApi.verify().then((r) => r.data),
    enabled: !!user,
  });

  if (authLoading) return null;

  const entries = data?.entries ?? [];
  const chainValid = chainData?.valid;

  return (
    <AppShell>
      <div className="px-4 lg:px-8 py-6 max-w-5xl mx-auto">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="flex items-center gap-2">
              <Shield size={20} className="text-brand-600" aria-hidden="true" />
              Audit Trail
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Append-only, hash-chained audit log of all AI actions
            </p>
          </div>
          <button
            onClick={() => { refetch(); refetchChain(); }}
            className="p-2 rounded-lg border border-border hover:bg-muted text-muted-foreground"
            aria-label="Refresh audit log"
          >
            <RefreshCw size={15} />
          </button>
        </div>

        {/* Chain verification status */}
        <div
          className={cn(
            "rounded-xl p-3 mb-5 flex items-center gap-3 text-sm font-medium",
            chainData == null
              ? "bg-muted text-muted-foreground"
              : chainValid
              ? "bg-success-light text-success-dark border border-green-200"
              : "bg-danger-light text-danger-dark border border-red-200"
          )}
          role="status"
          aria-live="polite"
        >
          {chainData == null ? (
            <Shield size={16} aria-hidden="true" />
          ) : chainValid ? (
            <CheckCircle size={16} aria-hidden="true" />
          ) : (
            <XCircle size={16} aria-hidden="true" />
          )}
          {chainData == null
            ? "Verifying audit chain..."
            : chainValid
            ? `Audit chain verified ✓ — ${chainData.entries_checked ?? 0} entries checked`
            : `Chain integrity failure at sequence ${chainData.first_tampered_seq ?? "?"}`}
        </div>

        {/* Timeline */}
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-muted rounded-xl animate-pulse" />
            ))}
          </div>
        ) : entries.length === 0 ? (
          <div className="bg-card border border-border rounded-xl p-10 text-center text-sm text-muted-foreground">
            No audit entries yet. Actions will appear here once taken.
          </div>
        ) : (
          <div className="relative" role="log" aria-label="Audit timeline">
            {/* Vertical line */}
            <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-border" aria-hidden="true" />

            <div className="space-y-3">
              {entries.map((entry: {
                id: string;
                sequence_number: number;
                timestamp: string;
                actor_type: string;
                actor_name?: string;
                intent?: string;
                tool?: string;
                final_result?: string;
                policy_result?: string;
                approval_status?: string;
                execution_status?: string;
                verification_status?: string;
                simulated: boolean;
                hash?: string;
                prev_hash?: string;
              }) => (
                <div key={entry.id} className="flex gap-4 pl-10 relative">
                  {/* Timeline dot */}
                  <div
                    className={cn(
                      "absolute left-3.5 top-2 w-3 h-3 rounded-full border-2 border-background flex-shrink-0",
                      entry.final_result === "VERIFIED" || entry.final_result === "EXECUTED"
                        ? "bg-success"
                        : entry.final_result === "REJECTED" || entry.final_result === "BLOCKED"
                        ? "bg-danger"
                        : "bg-brand-500"
                    )}
                    aria-hidden="true"
                  />

                  <div className="flex-1 bg-card border border-border rounded-xl p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-mono text-muted-foreground">
                            {entry.timestamp ? formatDateTime(entry.timestamp) : ""}
                          </span>
                          <span className="text-xs font-medium capitalize text-foreground">
                            {entry.actor_type === "system" ? "GrowthPilot AI"
                              : entry.actor_type === "merchant" ? "Merchant"
                              : "System"}
                          </span>
                          {entry.simulated && <SimulatedBadge />}
                        </div>
                        <p className="text-sm mt-0.5">
                          {entry.intent ?? (entry.tool ? entry.tool.replace(/_/g, " ") : "System event")}
                        </p>
                        {entry.tool && (
                          <p className="text-xs text-muted-foreground mt-0.5">
                            Tool: <span className="font-mono">{entry.tool}</span>
                          </p>
                        )}
                      </div>
                      <div className="flex-shrink-0">
                        {entry.final_result && (
                          <span
                            className={cn(
                              "text-xs px-2 py-0.5 rounded-full font-medium",
                              entry.final_result === "VERIFIED" || entry.final_result === "EXECUTED"
                                ? "bg-success-light text-success-dark"
                                : entry.final_result === "REJECTED" || entry.final_result === "BLOCKED"
                                ? "bg-danger-light text-danger-dark"
                                : "bg-muted text-muted-foreground"
                            )}
                          >
                            {entry.final_result}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Hash preview */}
                    <div className="mt-2 pt-2 border-t border-border flex items-center gap-2 text-xs text-muted-foreground font-mono">
                      <span>#{entry.sequence_number}</span>
                      <span>·</span>
                      <span>{entry.hash}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {entries.length >= limit && (
          <button
            onClick={() => setLimit((l) => l + 50)}
            className="w-full mt-4 py-2.5 border border-border rounded-xl text-sm text-brand-600 hover:bg-muted transition-colors"
          >
            Load more
          </button>
        )}
      </div>
    </AppShell>
  );
}
