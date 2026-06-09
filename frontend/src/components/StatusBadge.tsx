import type { HealthResponse } from "../api/client";

type Props = {
  health: HealthResponse | null;
  error: string | null;
};

export function StatusBadge({ health, error }: Props) {
  if (error) {
    return (
      <span className="rounded-full bg-red-500/20 px-3 py-1 text-xs font-medium text-red-300">
        offline
      </span>
    );
  }
  if (!health) {
    return (
      <span className="rounded-full bg-zinc-800 px-3 py-1 text-xs text-zinc-500">…</span>
    );
  }
  const colors = {
    ok: "bg-emerald-500/20 text-emerald-300",
    degraded: "bg-amber-500/20 text-amber-300",
    error: "bg-red-500/20 text-red-300",
  } as const;
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-medium ${colors[health.status]}`}>
      {health.status}
    </span>
  );
}
