import type { ReactNode } from "react";

export function Badge({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex rounded-full border border-border bg-white/60 px-3 py-1 font-mono text-[11px] uppercase tracking-[0.24em] text-muted">
      {children}
    </span>
  );
}
