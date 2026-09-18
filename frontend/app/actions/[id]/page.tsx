"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { CheckCircle, XCircle, AlertTriangle, ArrowLeft, Shield } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { SimulatedBadge } from "@/components/ui/SimulatedBadge";
import { useAuth } from "@/hooks/useAuth";
import { actionsApi } from "@/lib/api";
import { formatDateTime, formatRupeesRaw } from "@/lib/utils";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

export default function ActionDetailPage({ params }: { params: { id: string } }) {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();
  const [rejecting, setRejecting] = useState(false);
  const [rejectReason, setRejectReason] = useState("");

  const { data: action, isLoading } = useQuery({
    queryKey: ["action", params.id],
    queryFn: () => actionsApi.get(params.id).then((r) => r.data),
    enabled: !!user,
    refetchInterval: (data) =>
      data?.status === "EXECUTING" || data?.status === "APPROVED" ? 2000 : false,
  });

  const approveMutation = useMutation({
    mutationFn: () => actionsApi.approve(params.id),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["action", params.id] });
      qc.invalidateQueries({ queryKey: ["actions"] });
      const result = res.data.execution_result;
      if (result?.checklist) {
        toast.success("Action executed and verified! ✓");
      } else {
        toast.success("Action approved!");
      }
    },
    onError: (err: { response?: { data?: { detail?: unknown } } }) => {
      const detail = err?.response?.data?.detail;
      if (typeof detail === "object" && detail !== null && "message" in detail) {
        toast.error(String((detail as Record<string, unknown>).message));
      } else {
        toast.error("Failed to approve action");
      }
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () => actionsApi.reject(params.id, rejectReason || "Rejected by merchant"),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["action", params.id] });
      qc.invalidateQueries({ queryKey: ["actions"] });
      toast.success("Action rejected");
      setRejecting(false);
    },
    onError: () => toast.error("Failed to reject action"),
  });

  if (authLoading || isLoading) {
    return (
      <AppShell>
        <div className="px-4 lg:px-8 py-6 max-w-2xl mx-auto">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-muted rounded w-48" />
            <div className="h-48 bg-muted rounded-xl" />
          </div>
        </div>
      </AppShell>
    );
  }

  if (!action) return null;

  const afterState = action.after_state;
  const checklist: string[] = afterState?.checklist ?? [];
  const isVerified = action.status === "VERIFIED";
  const isAwaitingApproval = action.status === "AWAITING_APPROVAL";
  const isTerminal = ["VERIFIED", "REJECTED", "BLOCKED", "FAILED", "ROLLED_BACK"].includes(action.status);

  return (
    <AppShell>
      <div className="px-4 lg:px-8 py-6 max-w-2xl mx-auto">
        {/* Back */}
        <button
          onClick={() => router.push("/actions")}
          className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-5 transition-colors"
        >
          <ArrowLeft size={14} aria-hidden="true" />
          Back to Actions
        </button>

        {/* Header */}
        <div className="bg-card border border-border rounded-xl p-5 mb-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h1 className="capitalize font-semibold">
                {action.action_type?.replace(/_/g, " ")}
              </h1>
              <p className="text-xs text-muted-foreground mt-1">
                ID: {action.id}
              </p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <StatusBadge status={action.status} />
              <SimulatedBadge />
            </div>
          </div>

          {/* Risk tier */}
          <div className="mt-3 flex items-center gap-2 text-sm">
            <Shield size={13} className="text-muted-foreground" aria-hidden="true" />
            <span className="text-muted-foreground">Risk tier:</span>
            <span className="font-mono font-medium text-xs px-2 py-0.5 bg-muted rounded">
              {action.risk_tier}
            </span>
          </div>

          {/* Impact */}
          {action.estimated_impact_rupees > 0 && (
            <div className="mt-3 p-3 bg-success-light rounded-lg">
              <p className="text-sm text-success-dark">
                <span className="font-semibold">Estimated impact:</span>{" "}
                <span className="rupee font-bold">
                  {formatRupeesRaw(action.estimated_impact_rupees)}
                </span>
              </p>
            </div>
          )}

          {/* Timeline */}
          <div className="mt-4 text-xs text-muted-foreground space-y-1 border-t border-border pt-3">
            {action.proposed_at && <p>Proposed: {formatDateTime(action.proposed_at)}</p>}
            {action.approved_at && <p>Approved: {formatDateTime(action.approved_at)}</p>}
            {action.executed_at && <p>Executed: {formatDateTime(action.executed_at)}</p>}
            {action.verified_at && (
              <p className="text-success font-medium">✓ Verified: {formatDateTime(action.verified_at)}</p>
            )}
          </div>
        </div>

        {/* Execution checklist (after approval) */}
        {checklist.length > 0 && (
          <div className="bg-card border border-border rounded-xl p-5 mb-4">
            <h2 className="font-semibold mb-3 flex items-center gap-2">
              <CheckCircle size={16} className="text-success" aria-hidden="true" />
              Execution Checklist
            </h2>
            <ul className="space-y-2">
              {checklist.map((item: string, i: number) => (
                <li key={i} className="flex items-center gap-2 text-sm">
                  <CheckCircle size={14} className="text-success flex-shrink-0" aria-hidden="true" />
                  {item}
                </li>
              ))}
            </ul>
            {isVerified && (
              <div className="mt-3 p-3 bg-success-light rounded-lg text-success-dark text-sm font-medium flex items-center gap-2">
                <CheckCircle size={14} aria-hidden="true" />
                Impact verified ✓ — Audit entry recorded
              </div>
            )}
          </div>
        )}

        {/* Action buttons */}
        {isAwaitingApproval && (
          <div className="bg-card border border-border rounded-xl p-5 space-y-3">
            <div className="flex items-start gap-2">
              <AlertTriangle size={16} className="text-warning mt-0.5 flex-shrink-0" aria-hidden="true" />
              <div>
                <p className="font-semibold text-sm">ACTION REQUIRED</p>
                <p className="text-sm text-muted-foreground mt-0.5">
                  This action requires your approval before execution.
                </p>
              </div>
            </div>

            {!rejecting ? (
              <div className="flex gap-2 pt-1">
                <button
                  onClick={() => approveMutation.mutate()}
                  disabled={approveMutation.isPending}
                  className="flex-1 bg-success hover:bg-success-dark disabled:opacity-60 text-white py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                >
                  <CheckCircle size={14} aria-hidden="true" />
                  {approveMutation.isPending ? "Approving..." : "Approve & Execute"}
                </button>
                <button
                  onClick={() => setRejecting(true)}
                  className="px-4 py-2.5 border border-danger rounded-lg text-sm font-medium text-danger hover:bg-danger-light transition-colors flex items-center gap-2"
                >
                  <XCircle size={14} aria-hidden="true" />
                  Reject
                </button>
              </div>
            ) : (
              <div className="space-y-2 pt-1">
                <textarea
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Reason for rejection (optional)"
                  className="w-full px-3 py-2 border border-border rounded-lg text-sm bg-background resize-none"
                  rows={2}
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => rejectMutation.mutate()}
                    disabled={rejectMutation.isPending}
                    className="flex-1 bg-danger hover:bg-danger-dark disabled:opacity-60 text-white py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    {rejectMutation.isPending ? "Rejecting..." : "Confirm Reject"}
                  </button>
                  <button
                    onClick={() => setRejecting(false)}
                    className="px-4 py-2 border border-border rounded-lg text-sm text-muted-foreground hover:bg-muted transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Params display */}
        {action.params && (
          <div className="bg-card border border-border rounded-xl p-4 mt-4">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Parameters</p>
            <pre className="text-xs overflow-x-auto text-foreground">
              {JSON.stringify(action.params, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </AppShell>
  );
}
