"use client";

import { useState } from "react";
import { Settings, Shield, Bell, Eye, Trash2, Download } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/hooks/useAuth";
import { SimulatedBadge } from "@/components/ui/SimulatedBadge";
import toast from "react-hot-toast";

const AUTONOMY_LEVELS = [
  { value: "off", label: "Off", description: "No AI suggestions" },
  { value: "recommend", label: "Recommend only", description: "AI suggests, you decide everything (default)" },
  { value: "semi_auto", label: "Semi-automatic", description: "Auto-approve low-risk (L0/L1), ask for L2+" },
  { value: "full_auto", label: "Full automatic", description: "Auto-approve all except L3/L4" },
];

export default function SettingsPage() {
  const { user } = useAuth();
  const [autonomy, setAutonomy] = useState("recommend");
  const [killSwitch, setKillSwitch] = useState(false);
  const [quietStart, setQuietStart] = useState(21);
  const [quietEnd, setQuietEnd] = useState(9);

  const handleKillSwitch = () => {
    const next = !killSwitch;
    setKillSwitch(next);
    toast(next ? "⚠ Kill switch ON — all AI actions paused" : "Kill switch OFF — AI actions resumed", {
      icon: next ? "🛑" : "✅",
    });
  };

  const handleReset = () => {
    toast("Demo reset — this would delete and re-seed the database (run make reset-demo)");
  };

  if (!user) return null;

  return (
    <AppShell>
      <div className="px-4 lg:px-8 py-6 max-w-2xl mx-auto">
        <h1 className="flex items-center gap-2 mb-6">
          <Settings size={20} className="text-brand-600" aria-hidden="true" />
          Settings
        </h1>

        {/* Autonomy Dial */}
        <section className="bg-card border border-border rounded-xl p-5 mb-4" aria-labelledby="autonomy-heading">
          <h2 id="autonomy-heading" className="font-semibold mb-1">AI Autonomy Level</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Control how much the AI can do without asking you first.
          </p>
          <div className="space-y-2" role="radiogroup" aria-labelledby="autonomy-heading">
            {AUTONOMY_LEVELS.map((level) => (
              <label
                key={level.value}
                className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${
                  autonomy === level.value
                    ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20"
                    : "border-border hover:bg-muted"
                }`}
              >
                <input
                  type="radio"
                  name="autonomy"
                  value={level.value}
                  checked={autonomy === level.value}
                  onChange={() => setAutonomy(level.value)}
                  className="mt-0.5"
                  aria-describedby={`autonomy-${level.value}-desc`}
                />
                <div>
                  <p className="font-medium text-sm">{level.label}</p>
                  <p id={`autonomy-${level.value}-desc`} className="text-xs text-muted-foreground">
                    {level.description}
                  </p>
                </div>
              </label>
            ))}
          </div>
        </section>

        {/* Kill Switch */}
        <section className="bg-card border border-border rounded-xl p-5 mb-4" aria-labelledby="killswitch-heading">
          <div className="flex items-center justify-between">
            <div>
              <h2 id="killswitch-heading" className="font-semibold flex items-center gap-2">
                <Shield size={15} className={killSwitch ? "text-danger" : "text-muted-foreground"} aria-hidden="true" />
                Kill Switch
              </h2>
              <p className="text-sm text-muted-foreground mt-0.5">
                Pause all AI actions immediately
              </p>
            </div>
            <button
              onClick={handleKillSwitch}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                killSwitch ? "bg-danger" : "bg-muted"
              }`}
              role="switch"
              aria-checked={killSwitch}
              aria-labelledby="killswitch-heading"
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                  killSwitch ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>
          {killSwitch && (
            <div className="mt-3 p-2 bg-danger-light rounded-lg text-danger-dark text-xs font-medium">
              🛑 All AI actions are currently paused
            </div>
          )}
        </section>

        {/* Quiet Hours */}
        <section className="bg-card border border-border rounded-xl p-5 mb-4" aria-labelledby="quiet-heading">
          <h2 id="quiet-heading" className="font-semibold mb-1">Quiet Hours</h2>
          <p className="text-sm text-muted-foreground mb-3">
            No outbound messages sent during these hours (IST)
          </p>
          <div className="flex items-center gap-3">
            <div>
              <label htmlFor="quiet-start" className="text-xs text-muted-foreground block mb-1">From</label>
              <select
                id="quiet-start"
                value={quietStart}
                onChange={(e) => setQuietStart(Number(e.target.value))}
                className="border border-border rounded-lg px-3 py-1.5 text-sm bg-background"
              >
                {Array.from({ length: 24 }, (_, i) => (
                  <option key={i} value={i}>{String(i).padStart(2, "0")}:00</option>
                ))}
              </select>
            </div>
            <span className="text-muted-foreground mt-4">—</span>
            <div>
              <label htmlFor="quiet-end" className="text-xs text-muted-foreground block mb-1">Until</label>
              <select
                id="quiet-end"
                value={quietEnd}
                onChange={(e) => setQuietEnd(Number(e.target.value))}
                className="border border-border rounded-lg px-3 py-1.5 text-sm bg-background"
              >
                {Array.from({ length: 24 }, (_, i) => (
                  <option key={i} value={i}>{String(i).padStart(2, "0")}:00</option>
                ))}
              </select>
            </div>
          </div>
        </section>

        {/* Demo management */}
        <section className="bg-card border border-border rounded-xl p-5 mb-4" aria-labelledby="demo-heading">
          <h2 id="demo-heading" className="font-semibold mb-1 flex items-center gap-2">
            Reset Demo
            <SimulatedBadge />
          </h2>
          <p className="text-sm text-muted-foreground mb-3">
            Deletes the database and re-seeds with fresh synthetic data
          </p>
          <div className="flex gap-2">
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-4 py-2 border border-danger rounded-lg text-sm text-danger hover:bg-danger-light transition-colors"
            >
              <Trash2 size={13} aria-hidden="true" />
              Reset Demo Data
            </button>
            <button
              onClick={() => toast("Exporting data (simulated)")}
              className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg text-sm text-muted-foreground hover:bg-muted transition-colors"
            >
              <Download size={13} aria-hidden="true" />
              Export Data
            </button>
          </div>
        </section>

        <p className="text-xs text-muted-foreground text-center mt-4">
          GrowthPilot AI · Sandbox · Independent hackathon prototype
        </p>
      </div>
    </AppShell>
  );
}
