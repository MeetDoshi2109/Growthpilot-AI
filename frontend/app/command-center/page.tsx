"use client";

import { useState, useEffect, useRef } from "react";
import { Zap, CheckCircle, Circle, Clock, AlertCircle, ChevronRight, Bot } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/hooks/useAuth";
import { missionsApi, opportunitiesApi } from "@/lib/api";
import { formatRupeesRaw } from "@/lib/utils";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { SimulatedBadge } from "@/components/ui/SimulatedBadge";
import { OpportunityCard } from "@/components/ui/OpportunityCard";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

interface MissionStep {
  step_number: number;
  title: string;
  status: string;
  agent_name: string;
}

interface Mission {
  mission_id: string;
  title: string;
  status: string;
  steps: MissionStep[];
}

const STEP_ICONS: Record<string, React.ElementType> = {
  done: CheckCircle,
  running: Clock,
  failed: AlertCircle,
  pending: Circle,
  awaiting_approval: AlertCircle,
};

const STEP_COLORS: Record<string, string> = {
  done: "text-success",
  running: "text-brand-600",
  failed: "text-danger",
  pending: "text-muted-foreground",
  awaiting_approval: "text-warning",
};

export default function CommandCenterPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [mission, setMission] = useState<Mission | null>(null);
  const [liveSteps, setLiveSteps] = useState<MissionStep[]>([]);
  const [starting, setStarting] = useState(false);
  const [phase, setPhase] = useState<"idle" | "analyzing" | "opportunities" | "done">("idle");
  const eventSourceRef = useRef<EventSource | null>(null);

  const { data: oppsData, isLoading: oppsLoading } = useQuery({
    queryKey: ["opportunities"],
    queryFn: () => opportunitiesApi.list().then((r) => r.data),
    enabled: phase === "opportunities" || phase === "done",
  });

  const opps = oppsData?.opportunities ?? [];

  const startMission = async () => {
    if (!user) return;
    setStarting(true);
    setPhase("analyzing");
    setLiveSteps([]);

    try {
      const res = await missionsApi.create("Grow my business", "AI Growth Mission");
      const missionData: Mission = res.data;
      setMission(missionData);

      // Initialize all steps as pending
      const initialSteps: MissionStep[] = missionData.steps.map((s: MissionStep) => ({
        ...s,
        status: "pending",
      }));
      setLiveSteps(initialSteps);

      // Simulate progressive step completion
      simulateProgress(initialSteps, missionData.mission_id);
    } catch (err) {
      toast.error("Failed to start mission");
      setPhase("idle");
    } finally {
      setStarting(false);
    }
  };

  const simulateProgress = (steps: MissionStep[], missionId: string) => {
    let currentStep = 0;
    const interval = setInterval(() => {
      if (currentStep >= steps.length) {
        clearInterval(interval);
        setPhase("opportunities");
        return;
      }

      setLiveSteps((prev) =>
        prev.map((s, i) => ({
          ...s,
          status:
            i < currentStep ? "done"
            : i === currentStep ? "running"
            : "pending",
        }))
      );

      // Immediately mark as done after brief "running"
      setTimeout(() => {
        setLiveSteps((prev) =>
          prev.map((s, i) => ({
            ...s,
            status: i <= currentStep ? "done" : "pending",
          }))
        );
        currentStep++;
        if (currentStep >= steps.length - 2) {
          // Stop before last 2 (campaign execution + measure impact — require approval)
          clearInterval(interval);
          setPhase("opportunities");
        }
      }, 600);
    }, 900);
  };

  const totalImpact = opps.reduce(
    (s: number, o: { estimated_impact_base_rupees: number }) => s + (o.estimated_impact_base_rupees ?? 0),
    0
  );

  if (authLoading) return null;

  return (
    <AppShell>
      <div className="px-4 lg:px-8 py-6 max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="flex items-center gap-2">
            <Zap size={22} className="text-brand-600" aria-hidden="true" />
            AI Command Center
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Set a goal — the AI builds a plan, executes with your approval, and measures results.
          </p>
        </div>

        {/* Idle state — CTA */}
        {phase === "idle" && (
          <div className="bg-gradient-to-br from-brand-600 to-brand-800 rounded-2xl p-8 text-white text-center">
            <Bot size={40} className="mx-auto mb-4 opacity-90" aria-hidden="true" />
            <h2 className="text-2xl font-bold mb-2">What should I do today?</h2>
            <p className="text-brand-100 text-sm mb-6 max-w-sm mx-auto">
              GrowthPilot will analyze your sales, customers, inventory, and collections —
              then surface the top opportunities ranked by revenue impact.
            </p>
            <button
              onClick={startMission}
              disabled={starting}
              className="bg-white text-brand-700 hover:bg-brand-50 font-semibold px-8 py-3 rounded-xl text-base transition-colors disabled:opacity-60 flex items-center gap-2 mx-auto"
            >
              <Zap size={18} aria-hidden="true" />
              {starting ? "Starting mission..." : "Grow my business"}
            </button>
            <div className="mt-4 flex items-center justify-center gap-1">
              <SimulatedBadge />
            </div>
          </div>
        )}

        {/* Analyzing phase — step timeline */}
        {(phase === "analyzing" || phase === "opportunities" || phase === "done") && (
          <div className="space-y-4">
            <div className="bg-card border border-border rounded-xl p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Zap size={16} className="text-white" aria-hidden="true" />
                </div>
                <div>
                  <p className="font-semibold">MISSION CREATED — Goal: Grow my business</p>
                  <p className="text-xs text-muted-foreground">
                    {phase === "analyzing" ? "AI is analyzing your business..." : "Analysis complete"}
                  </p>
                </div>
                <StatusBadge
                  status={phase === "analyzing" ? "running" : "done"}
                  className="ml-auto"
                />
              </div>

              {/* Live step timeline */}
              <ol className="space-y-2" aria-label="Mission progress steps">
                {liveSteps.map((step) => {
                  const StepIcon = STEP_ICONS[step.status] ?? Circle;
                  const colorClass = STEP_COLORS[step.status] ?? "text-muted-foreground";

                  return (
                    <li
                      key={step.step_number}
                      className="flex items-center gap-3 text-sm"
                      aria-label={`Step ${step.step_number}: ${step.title} — ${step.status}`}
                    >
                      <StepIcon
                        size={16}
                        className={`${colorClass} flex-shrink-0 ${step.status === "running" ? "animate-pulse" : ""}`}
                        aria-hidden="true"
                      />
                      <span className={step.status === "done" ? "text-foreground" : "text-muted-foreground"}>
                        {step.status === "done" ? "✓ " : ""}{step.title}
                      </span>
                      {step.status === "awaiting_approval" && (
                        <span className="text-xs text-warning font-medium ml-auto">Waiting for approval</span>
                      )}
                    </li>
                  );
                })}
              </ol>
            </div>

            {/* Opportunities found */}
            {phase === "opportunities" && opps.length > 0 && (
              <div
                className="bg-success-light border border-green-200 rounded-xl p-4 text-center"
                role="status"
                aria-live="polite"
              >
                <p className="font-semibold text-success-dark">
                  {opps.length} opportunities found! &nbsp;·&nbsp; Est. total impact:{" "}
                  <span className="rupee font-bold">{formatRupeesRaw(totalImpact)}</span>
                </p>
              </div>
            )}

            {/* Opportunity cards */}
            {phase === "opportunities" && (
              <div className="space-y-4">
                {oppsLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map((i) => <div key={i} className="h-40 bg-muted rounded-xl animate-pulse" />)}
                  </div>
                ) : (
                  opps.slice(0, 3).map((opp: Parameters<typeof OpportunityCard>[0]["opportunity"]) => (
                    <OpportunityCard
                      key={opp.id}
                      opportunity={opp}
                      onAction={() => router.push(`/growth?opp=${opp.id}`)}
                    />
                  ))
                )}

                {opps.length > 3 && (
                  <button
                    onClick={() => router.push("/growth")}
                    className="w-full py-3 border border-border rounded-xl text-sm text-brand-600 hover:bg-muted transition-colors flex items-center justify-center gap-1"
                  >
                    View all {opps.length} opportunities
                    <ChevronRight size={14} aria-hidden="true" />
                  </button>
                )}
              </div>
            )}

            {/* Restart */}
            <button
              onClick={() => { setPhase("idle"); setMission(null); setLiveSteps([]); }}
              className="text-sm text-muted-foreground hover:text-foreground underline"
            >
              Start a new mission
            </button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
