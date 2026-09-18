"use client";

/**
 * Persistent "Sandbox · Synthetic Demo Data" indicator.
 * Visible on every page — required by spec.
 */
export function SandboxBanner() {
  return (
    <div
      className="w-full bg-sandbox-bg border-b border-sandbox-border px-4 py-1.5 text-center z-50"
      role="banner"
      aria-label="Sandbox mode indicator"
    >
      <span className="text-xs font-medium text-sandbox-text inline-flex items-center gap-1.5">
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" aria-hidden="true" />
        <strong>Sandbox</strong>
        <span aria-hidden="true">·</span>
        Synthetic Demo Data — No real Paytm data or money movement
        <span aria-hidden="true">·</span>
        Independent hackathon prototype
      </span>
    </div>
  );
}
