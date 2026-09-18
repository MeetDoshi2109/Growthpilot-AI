import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format paise as ₹ with Indian lakh/crore grouping */
export function formatRupees(paise: number, decimals = 0): string {
  const rupees = paise / 100;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(rupees);
}

/** Format a raw rupee float with Indian grouping */
export function formatRupeesRaw(rupees: number, decimals = 0): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(rupees);
}

/** Format count with Indian grouping (1,00,000) */
export function formatIndianNumber(n: number): string {
  return new Intl.NumberFormat("en-IN").format(n);
}

/** Format date as DD MMM YYYY in IST */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  });
}

/** Format datetime as HH:mm:ss IST */
export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: "Asia/Kolkata",
    hour12: false,
  });
}

/** Format datetime full */
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Kolkata",
  });
}

/** Confidence level to color class */
export function confidenceColor(c: number): string {
  if (c >= 0.75) return "text-success";
  if (c >= 0.55) return "text-brand-600";
  if (c >= 0.35) return "text-warning";
  return "text-danger";
}

/** Confidence level label */
export function confidenceLabel(c: number): string {
  if (c >= 0.75) return "High";
  if (c >= 0.55) return "Medium";
  if (c >= 0.35) return "Low";
  return "Very Low";
}

/** Risk tier to badge variant */
export function riskTierBadge(tier: string): string {
  const map: Record<string, string> = {
    L0: "bg-muted text-muted-foreground",
    L1: "bg-muted text-muted-foreground",
    L2: "bg-warning-light text-warning-dark",
    L3: "bg-danger-light text-danger-dark",
    L4: "bg-danger text-white",
  };
  return map[tier] ?? "bg-muted text-muted-foreground";
}

/** Action status to color */
export function actionStatusColor(status: string): string {
  const map: Record<string, string> = {
    PROPOSED: "text-muted-foreground",
    POLICY_CHECKED: "text-brand-600",
    AWAITING_APPROVAL: "text-warning",
    APPROVED: "text-brand-600",
    EXECUTING: "text-brand-500",
    EXECUTED: "text-success",
    VERIFIED: "text-success",
    REJECTED: "text-danger",
    BLOCKED: "text-danger",
    FAILED: "text-danger",
    ROLLED_BACK: "text-warning",
    EXPIRED: "text-muted-foreground",
  };
  return map[status] ?? "text-muted-foreground";
}

export function opportunityTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    CUSTOMER_WINBACK: "Customer Win-back",
    CROSS_SELL: "Cross-sell",
    UPSELL: "Upsell",
    PRODUCT_PROMOTION: "Product Promotion",
    INVENTORY_RISK: "Inventory Risk",
    PAYMENT_RECOVERY: "Payment Recovery",
    CUSTOMER_RETENTION: "Customer Retention",
    REVENUE_DECLINE: "Revenue Decline",
    HIGH_VALUE_CUSTOMER: "High-Value Customer",
    SEASONAL_OPPORTUNITY: "Seasonal Opportunity",
  };
  return labels[type] ?? type;
}
