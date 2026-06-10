import { useEffect, useState } from "react";
import { AuthPage } from "../components/AuthPage";
import { BatchDetail } from "../components/BatchDetail";
import { BatchGrid } from "../components/BatchGrid";
import { CampusFeed } from "../components/CampusFeed";
import { PostComposer } from "../components/PostComposer";
import { StatusBadge } from "../components/StatusBadge";
import { UserMenu } from "../components/UserMenu";
import { AuthProvider, useAuth } from "../contexts/AuthContext";
import { fetchHealth, type HealthResponse } from "../api/client";

function FacultyShell({ children }: { children: React.ReactNode }) {
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
            <p className="text-xs font-semibold uppercase tracking-wider text-violet-400">
              AcadMind · Faculty
            </p>
            <h1 className="text-xl font-bold text-zinc-100">Campus Manager</h1>
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

function FacultyDashboard() {
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const [feedKey, setFeedKey] = useState(0);

  if (selectedBatchId) {
    return (
      <FacultyShell>
        <BatchDetail batchId={selectedBatchId} onBack={() => setSelectedBatchId(null)} />
      </FacultyShell>
    );
  }

  return (
    <FacultyShell>
      <div className="space-y-8">
        <PostComposer onPosted={() => setFeedKey((k) => k + 1)} />
        <div className="grid gap-8 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <h2 className="mb-4 text-lg font-semibold text-zinc-100">Your batches</h2>
            <BatchGrid onSelectBatch={setSelectedBatchId} />
          </div>
          <div className="lg:col-span-2">
            <h2 className="mb-4 text-lg font-semibold text-zinc-100">Campus feed</h2>
            <CampusFeed api="faculty" refreshKey={feedKey} sectioned />
          </div>
        </div>
      </div>
    </FacultyShell>
  );
}

function FacultyGate() {
  const { session, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#08080d] text-zinc-500">
        Loading…
      </div>
    );
  }
  if (!session) return <AuthPage />;
  return <FacultyDashboard />;
}

export function FacultyApp() {
  return (
    <AuthProvider portal="faculty">
      <FacultyGate />
    </AuthProvider>
  );
}
