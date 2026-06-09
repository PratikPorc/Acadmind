import { type ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-2xl border border-zinc-800 bg-zinc-900/80 backdrop-blur-sm ${className}`}
    >
      {children}
    </div>
  );
}

export function Badge({
  children,
  variant = "default",
}: {
  children: ReactNode;
  variant?: "default" | "exam" | "assignment" | "resource" | "notice";
}) {
  const colors = {
    default: "bg-indigo-500/20 text-indigo-300",
    exam: "bg-red-500/20 text-red-300",
    assignment: "bg-amber-500/20 text-amber-300",
    resource: "bg-emerald-500/20 text-emerald-300",
    notice: "bg-sky-500/20 text-sky-300",
  };
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[variant]}`}>
      {children}
    </span>
  );
}
