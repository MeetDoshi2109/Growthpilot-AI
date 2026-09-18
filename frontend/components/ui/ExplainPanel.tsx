"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Info } from "lucide-react";
import { cn, formatRupeesRaw, confidenceLabel, confidenceColor } from "@/lib/utils";

interface Evidence {
  type: string;
  value: number | string;
  description: string;
}

interface ExpectedImpact {
  low_rupees?: number;
  base_rupees?: number;
  high_rupees?: number;
}

interface ExplainData {
  what?: string;
  why?: string;
  evidence?: Evidence[];
  expected_impact?: ExpectedImpact;
  confidence?: number;
  confidence_label?: string;
  what_happens_if_approve?: string;
  risks_and_limits?: string;
  data_as_of?: string;
}

interface ExplainPanelProps {
  data: ExplainData;
  defaultOpen?: boolean;
  className?: string;
}

export function ExplainPanel({ data, defaultOpen = false, className }: ExplainPanelProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={cn("border border-border rounded-xl overflow-hidden", className)}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-muted hover:bg-accent transition-colors text-sm font-medium"
        aria-expanded={open}
      >
        <span className="flex items-center gap-2">
          <Info size={14} className="text-brand-600" aria-hidden="true" />
          Why this recommendation?
        </span>
        {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {open && (
        <div className="p-4 space-y-4 text-sm">
          {/* WHAT */}
          {data.what && (
            <div>
              <p className="font-semibold text-xs uppercase tracking-wide text-muted-foreground mb-1">What</p>
              <p>{data.what}</p>
            </div>
          )}

          {/* WHY */}
          {data.why && (
            <div>
              <p className="font-semibold text-xs uppercase tracking-wide text-muted-foreground mb-1">Why</p>
              <p className="text-muted-foreground">{data.why}</p>
            </div>
          )}

          {/* EVIDENCE */}
          {data.evidence && data.evidence.length > 0 && (
            <div>
              <p className="font-semibold text-xs uppercase tracking-wide text-muted-foreground mb-2">Evidence</p>
              <ul className="space-y-1">
                {data.evidence.map((e, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="mt-1 w-1.5 h-1.5 rounded-full bg-brand-500 flex-shrink-0" aria-hidden="true" />
                    <span>{e.description}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* IMPACT RANGE */}
          {data.expected_impact && (
            <div>
              <p className="font-semibold text-xs uppercase tracking-wide text-muted-foreground mb-2">Expected Impact</p>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-muted rounded-lg p-2">
                  <p className="text-xs text-muted-foreground">Low</p>
                  <p className="font-semibold rupee text-sm">
                    {data.expected_impact.low_rupees != null
                      ? formatRupeesRaw(data.expected_impact.low_rupees)
                      : "—"}
                  </p>
                </div>
                <div className="bg-brand-50 rounded-lg p-2 border border-brand-100">
                  <p className="text-xs text-brand-600">Base (est.)</p>
                  <p className="font-semibold rupee text-sm text-brand-700">
                    {data.expected_impact.base_rupees != null
                      ? formatRupeesRaw(data.expected_impact.base_rupees)
                      : "—"}
                  </p>
                </div>
                <div className="bg-muted rounded-lg p-2">
                  <p className="text-xs text-muted-foreground">High</p>
                  <p className="font-semibold rupee text-sm">
                    {data.expected_impact.high_rupees != null
                      ? formatRupeesRaw(data.expected_impact.high_rupees)
                      : "—"}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* CONFIDENCE */}
          {data.confidence != null && (
            <div>
              <p className="font-semibold text-xs uppercase tracking-wide text-muted-foreground mb-1">Confidence</p>
              <div className="flex items-center gap-3">
                <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-brand-500 rounded-full transition-all"
                    style={{ width: `${Math.round(data.confidence * 100)}%` }}
                  />
                </div>
                <span className={cn("text-sm font-medium", confidenceColor(data.confidence))}>
                  {Math.round(data.confidence * 100)}% — {confidenceLabel(data.confidence)}
                </span>
              </div>
            </div>
          )}

          {/* IF I APPROVE */}
          {data.what_happens_if_approve && (
            <div>
              <p className="font-semibold text-xs uppercase tracking-wide text-muted-foreground mb-1">If you approve</p>
              <p className="text-muted-foreground">{data.what_happens_if_approve}</p>
            </div>
          )}

          {/* RISKS */}
          {data.risks_and_limits && (
            <div>
              <p className="font-semibold text-xs uppercase tracking-wide text-muted-foreground mb-1">Risks & Limits</p>
              <p className="text-warning text-xs">{data.risks_and_limits}</p>
            </div>
          )}

          {/* DATA AS OF */}
          {data.data_as_of && (
            <p className="text-xs text-muted-foreground border-t border-border pt-3">
              Data as of {new Date(data.data_as_of).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })} IST
            </p>
          )}
        </div>
      )}
    </div>
  );
}
