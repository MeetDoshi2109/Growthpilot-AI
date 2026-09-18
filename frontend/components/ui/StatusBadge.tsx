import { cn } from "@/lib/utils";

const STATUS_STYLES: Record<string, string> = {
  // Action states
  PROPOSED:         "bg-muted text-muted-foreground",
  POLICY_CHECKED:   "bg-blue-50 text-blue-700",
  AWAITING_APPROVAL:"bg-warning-light text-warning-dark",
  APPROVED:         "bg-blue-50 text-blue-700",
  EXECUTING:        "bg-blue-100 text-blue-800 animate-pulse",
  EXECUTED:         "bg-success-light text-success-dark",
  VERIFIED:         "bg-success-light text-success-dark",
  REJECTED:         "bg-danger-light text-danger-dark",
  BLOCKED:          "bg-danger-light text-danger-dark",
  FAILED:           "bg-danger-light text-danger-dark",
  ROLLED_BACK:      "bg-warning-light text-warning-dark",
  EXPIRED:          "bg-muted text-muted-foreground",
  // Mission steps
  pending:          "bg-muted text-muted-foreground",
  running:          "bg-blue-100 text-blue-800 animate-pulse",
  awaiting_approval:"bg-warning-light text-warning-dark",
  done:             "bg-success-light text-success-dark",
  failed:           "bg-danger-light text-danger-dark",
  skipped:          "bg-muted text-muted-foreground",
  // General
  active:           "bg-success-light text-success-dark",
  actioned:         "bg-blue-50 text-blue-700",
  dismissed:        "bg-muted text-muted-foreground",
  expired:          "bg-muted text-muted-foreground",
};

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const style = STATUS_STYLES[status] ?? "bg-muted text-muted-foreground";
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium",
        style,
        className
      )}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}
