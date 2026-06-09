import { useEffect, useState } from "react";
import { fetchBatches, type BatchResponse } from "../api/student";
import { AuthPage } from "../components/AuthPage";
import { CampusFeed } from "../components/CampusFeed";
import { JarvisPanel } from "../components/JarvisPanel";
import { QueryAssistantPanel } from "../components/QueryAssistantPanel";
import { StatusBadge } from "../components/StatusBadge";
import { UserMenu } from "../components/UserMenu";
import { Card } from "../components/ui/Card";
import { AuthProvider, useAuth } from "../contexts/AuthContext";
import { fetchHealth, type HealthResponse } from "../api/client";

type Tab = "campus" | "ai" | "jarvis";

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
            <h1 className="text-xl font-bold text-zinc-100">DigiCampus</h1>
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

function MyBatches() {
  const [batches, setBatches] = useState<BatchResponse[]>([]);

  useEffect(() => {
    fetchBatches().then(setBatches).catch(() => setBatches([]));
  }, []);

  if (batches.length === 0) {
    return (
      <Card className="p-6 text-center text-sm text-zinc-500">
        Not enrolled in any batch yet. Ask faculty to add your Student ID.
      </Card>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {batches.map((b) => (
        <Card key={b.id} className="p-4">
          <p className="text-xs font-semibold uppercase text-sky-400">{b.code}</p>
          <p className="font-medium text-zinc-100">{b.name}</p>
          <p className="mt-1 text-xs text-zinc-500">
            {b.subject_count} subjects · Sem {b.semester}
          </p>
        </Card>
      ))}
    </div>
  );
}

function StudentDashboard() {
  const [tab, setTab] = useState<Tab>("campus");
  const tabs: { id: Tab; label: string }[] = [
    { id: "campus", label: "Campus" },
    { id: "ai", label: "Ask AI" },
    { id: "jarvis", label: "Jarvis" },
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
        <div className="space-y-8">
          <section>
            <h2 className="mb-3 text-lg font-semibold text-zinc-100">My batches</h2>
            <MyBatches />
          </section>
          <section>
            <h2 className="mb-3 text-lg font-semibold text-zinc-100">Announcements & deadlines</h2>
            <CampusFeed api="student" />
          </section>
        </div>
      )}
      {tab === "ai" && <QueryAssistantPanel />}
      {tab === "jarvis" && <JarvisPanel />}
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
