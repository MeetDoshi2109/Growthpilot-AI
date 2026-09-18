"use client";
import { FileText, Info } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { useAuth } from "@/hooks/useAuth";
import { SimulatedBadge } from "@/components/ui/SimulatedBadge";

const FACTORS = [
  { label: "Revenue Stability", score: 72, description: "Stable monthly revenue with moderate variability" },
  { label: "Cash Flow Trend", score: 68, description: "Improving trend over last 3 months" },
  { label: "Transaction Consistency", score: 80, description: "Regular daily transactions" },
  { label: "Collection Behavior", score: 55, description: "Some overdue payments present" },
  { label: "Business Growth", score: 62, description: "Mild growth with some seasonal dips" },
  { label: "Payment History", score: 74, description: "Mostly on-time payments" },
];

export default function FinancialReadinessPage() {
  const { user, loading } = useAuth();
  if (loading) return null;

  const overallScore = Math.round(FACTORS.reduce((s, f) => s + f.score, 0) / FACTORS.length);

  return (
    <AppShell>
      <div className="px-4 lg:px-8 py-6 max-w-2xl mx-auto">
        <h1 className="flex items-center gap-2 mb-1">
          <FileText size={20} className="text-brand-600" />
          Financial Readiness
        </h1>
        <div className="flex items-center gap-2 mb-4">
          <SimulatedBadge />
          <span className="text-xs text-muted-foreground">
            Demo eligibility only — not a credit decision
          </span>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-5 flex items-start gap-2">
          <Info size={14} className="text-amber-600 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-amber-800">
            <strong>Demo Eligibility Assessment.</strong> This is a simulated illustration based on your transaction data.
            This is NOT a real credit decision, credit score, or loan offer. No real lenders or financial institutions are involved.
          </p>
        </div>

        {/* Score card */}
        <div className="bg-card border border-border rounded-xl p-6 mb-5 text-center">
          <p className="text-sm text-muted-foreground mb-2">Overall Financial Readiness Score</p>
          <div className="relative inline-flex items-center justify-center w-24 h-24 mb-3">
            <svg className="w-24 h-24 -rotate-90" viewBox="0 0 96 96">
              <circle cx="48" cy="48" r="40" stroke="hsl(var(--muted))" strokeWidth="8" fill="none" />
              <circle
                cx="48" cy="48" r="40"
                stroke="#2563eb"
                strokeWidth="8"
                fill="none"
                strokeDasharray={`${(overallScore / 100) * 251} 251`}
                strokeLinecap="round"
              />
            </svg>
            <span className="absolute text-2xl font-bold">{overallScore}</span>
          </div>
          <p className="font-semibold text-brand-700">Good</p>
          <p className="text-xs text-muted-foreground mt-1">Based on transaction data, Jan–Sep 2026</p>
        </div>

        {/* Factors */}
        <div className="space-y-3 mb-5">
          {FACTORS.map((f) => (
            <div key={f.label} className="bg-card border border-border rounded-xl p-4">
              <div className="flex items-center justify-between mb-1">
                <p className="font-medium text-sm">{f.label}</p>
                <span className={`text-sm font-bold ${f.score >= 70 ? "text-success" : f.score >= 50 ? "text-warning" : "text-danger"}`}>
                  {f.score}/100
                </span>
              </div>
              <div className="h-1.5 bg-muted rounded-full overflow-hidden mb-1.5">
                <div
                  className={`h-full rounded-full ${f.score >= 70 ? "bg-success" : f.score >= 50 ? "bg-warning" : "bg-danger"}`}
                  style={{ width: `${f.score}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground">{f.description}</p>
            </div>
          ))}
        </div>

        {/* Improvements */}
        <div className="bg-card border border-border rounded-xl p-5">
          <h2 className="font-semibold mb-3">Factors that may improve readiness</h2>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <span className="text-brand-600 font-bold mt-0.5">→</span>
              Reduce overdue payments by sending timely reminders
            </li>
            <li className="flex items-start gap-2">
              <span className="text-brand-600 font-bold mt-0.5">→</span>
              Maintain consistent monthly transaction volume
            </li>
            <li className="flex items-start gap-2">
              <span className="text-brand-600 font-bold mt-0.5">→</span>
              Improve payment success rate (currently ~{92}%)
            </li>
          </ul>
        </div>
      </div>
    </AppShell>
  );
}
