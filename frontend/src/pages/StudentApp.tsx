import { useEffect, useState } from "react";
import { AuthPage } from "../components/AuthPage";
import { QueryAssistantPanel } from "../components/QueryAssistantPanel";
import { StudentCampusPanel } from "../components/StudentCampusPanel";
import { StatusBadge } from "../components/StatusBadge";
import { UserMenu } from "../components/UserMenu";
import { AuthProvider, useAuth } from "../contexts/AuthContext";
import { fetchHealth, type HealthResponse } from "../api/client";
import { STUDENT_PORTAL_NAME } from "../lib/branding";

type Tab = "campus" | "jarvis";

function StudentShell({ children }: { children: React.ReactNode }) {
  const { profileError, refreshProfile } = useAuth();
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  return (
    <div className="min-h-screen bg-[#08080d]">
      <header className="sticky top-0 z-40 border-b border-zinc-800 bg-zinc-900/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-sky-400">
              AcadMind · Student
            </p>
            <h1 className="text-xl font-bold text-zinc-100">{STUDENT_PORTAL_NAME}</h1>
          </div>
          <div className="flex items-center gap-4">
            <StatusBadge health={health} error={null} />
            <UserMenu />
          </div>
        </div>
      </header>

      {profileError && (
        <div className="mx-auto max-w-6xl px-6 pt-4">
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-300">
            {profileError}{" "}
            <button type="button" onClick={() => refreshProfile()} className="underline">
              Retry
            </button>
          </div>
        </div>
      )}

      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}

function StudentDashboard() {
  const [tab, setTab] = useState<Tab>("campus");
  const tabs: { id: Tab; label: string }[] = [
    { id: "campus", label: "Campus" },
    { id: "jarvis", label: "ASK Jarvis" },
  ];

  return (
    <StudentShell>
      <nav className="mb-6 flex gap-2 border-b border-zinc-800 pb-4">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              tab === t.id
                ? "bg-indigo-600 text-white"
                : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "campus" && (
        <section>
          <h2 className="mb-4 text-lg font-semibold text-zinc-100">Campus notices</h2>
          <StudentCampusPanel />
        </section>
      )}
      {tab === "jarvis" && <QueryAssistantPanel />}
    </StudentShell>
  );
}

function StudentGate() {
  const { session, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#08080d] text-zinc-500">
        Loading…
      </div>
    );
  }
  if (!session) return <AuthPage />;
  return <StudentDashboard />;
}

export function StudentApp() {
  return (
    <AuthProvider portal="student">
      <StudentGate />
    </AuthProvider>
  );
}
