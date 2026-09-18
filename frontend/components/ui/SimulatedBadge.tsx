import { cn } from "@/lib/utils";

export function SimulatedBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-xs bg-sandbox-bg text-sandbox-text border border-sandbox-border",
        className
      )}
    >
      <span className="w-1 h-1 rounded-full bg-amber-500" aria-hidden="true" />
      Simulated
    </span>
  );
}
