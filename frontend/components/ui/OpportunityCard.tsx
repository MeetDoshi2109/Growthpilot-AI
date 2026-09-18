"use client";

import { useState } from "react";
import { TrendingUp, Users, Package, CreditCard, AlertTriangle, ChevronRight } from "lucide-react";
import { cn, formatRupeesRaw, opportunityTypeLabel, confidenceLabel, confidenceColor } from "@/lib/utils";
import { ExplainPanel } from "./ExplainPanel";
import { StatusBadge } from "./StatusBadge";
import { SimulatedBadge } from "./SimulatedBadge";

const OPP_ICONS: Record<string, React.ElementType> = {
  CUSTOMER_WINBACK: Users,
  INVENTORY_RISK: Package,
  PAYMENT_RECOVERY: CreditCard,
  REVENUE_DECLINE: AlertTriangle,
  CUSTOMER_RETENTION: Users,
  HIGH_VALUE_CUSTOMER: TrendingUp,
  CROSS_SELL: TrendingUp,
  UPSELL: TrendingUp,
  PRODUCT_PROMOTION: TrendingUp,
  SEASONAL_OPPORTUNITY: TrendingUp,
};

const OPP_COLORS: Record<string, string> = {
  CUSTOMER_WINBACK: "bg-blue-50 text-blue-700",
  INVENTORY_RISK: "bg-amber-50 text-amber-700",
  PAYMENT_RECOVERY: "bg-green-50 text-green-700",
  REVENUE_DECLINE: "bg-red-50 text-red-700",
  CUSTOMER_RETENTION: "bg-purple-50 text-purple-700",
  HIGH_VALUE_CUSTOMER: "bg-indigo-50 text-indigo-700",
};

interface Opportunity {
  id: string;
  opportunity_type: string;
  title: string;
  description?: string;
  affected_customers?: number;
  estimated_impact_base_rupees: number;
  estimated_impact_low_rupees: number;
  estimated_impact_high_rupees: number;
  confidence: number;
  priority: number;
  recommended_action?: string;
  requires_approval?: boolean;
  explainability?: Record<string, unknown>;
  status: string;
}

interface OpportunityCardProps {
  opportunity: Opportunity;
  onAction?: (opp: Opportunity) => void;
  className?: string;
}

export function OpportunityCard({ opportunity: opp, onAction, className }: OpportunityCardProps) {
  const [showExplain, setShowExplain] = useState(false);
  const Icon = OPP_ICONS[opp.opportunity_type] ?? TrendingUp;
  const colorClass = OPP_COLORS[opp.opportunity_type] ?? "bg-muted text-muted-foreground";

  return (
    <div className={cn("bg-card border border-border rounded-xl overflow-hidden", className)}>
      <div className="p-5">
        <div className="flex items-start gap-3">
          <span className={cn("p-2 rounded-lg flex-shrink-0", colorClass)}>
            <Icon size={18} aria-hidden="true" />
          </span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-muted-foreground font-medium">
                {opportunityTypeLabel(opp.opportunity_type)}
              </span>
              <span className="text-xs text-muted-foreground">·</span>
              <span className="text-xs font-medium">Priority #{opp.priority}</span>
              <SimulatedBadge />
            </div>
            <h3 className="font-semibold mt-1">{opp.title}</h3>
            {opp.description && (
              <p className="text-sm text-muted-foreground mt-0.5 line-clamp-2">{opp.description}</p>
            )}
          </div>
        </div>

        {/* Impact + Confidence row */}
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="bg-muted rounded-lg p-3">
            <p className="text-xs text-muted-foreground">Est. Revenue Impact</p>
            <p className="font-semibold rupee text-lg">
              {formatRupeesRaw(opp.estimated_impact_base_rupees)}
            </p>
            <p className="text-xs text-muted-foreground">
              {formatRupeesRaw(opp.estimated_impact_low_rupees)} –{" "}
              {formatRupeesRaw(opp.estimated_impact_high_rupees)}
            </p>
          </div>
          <div className="bg-muted rounded-lg p-3">
            <p className="text-xs text-muted-foreground">Confidence</p>
            <p className={cn("font-semibold text-lg", confidenceColor(opp.confidence))}>
              {Math.round(opp.confidence * 100)}%
            </p>
            <p className="text-xs text-muted-foreground">{confidenceLabel(opp.confidence)}</p>
          </div>
        </div>

        {/* Affected customers */}
        {opp.affected_customers != null && opp.affected_customers > 0 && (
          <p className="mt-2 text-sm text-muted-foreground">
            <span className="font-medium text-foreground">{opp.affected_customers}</span> customers affected
          </p>
        )}

        {/* Action buttons */}
        <div className="mt-4 flex items-center gap-2 flex-wrap">
          <button
            onClick={() => onAction?.(opp)}
            className="flex-1 bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-1"
            aria-label={`Take action on ${opp.title}`}
          >
            Take Action
            <ChevronRight size={14} aria-hidden="true" />
          </button>
          <button
            onClick={() => setShowExplain(!showExplain)}
            className="px-4 py-2 border border-border rounded-lg text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
            aria-expanded={showExplain}
          >
            {showExplain ? "Hide" : "Why?"}
          </button>
        </div>
      </div>

      {/* Explainability panel */}
      {showExplain && opp.explainability && (
        <div className="border-t border-border">
          <ExplainPanel data={opp.explainability as Parameters<typeof ExplainPanel>[0]["data"]} defaultOpen />
        </div>
      )}
    </div>
  );
}
