import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#08080d] px-4">
      <div className="max-w-2xl text-center">
        <p className="text-xs font-semibold uppercase tracking-widest text-indigo-400">
          Techno India University
        </p>
        <h1 className="mt-3 bg-gradient-to-r from-indigo-300 to-violet-400 bg-clip-text text-5xl font-bold text-transparent">
          AcadMind
        </h1>
        <p className="mt-4 text-zinc-400">
          AI-powered campus platform — notices, deadlines, resources & intelligent Q&A
        </p>

        <div className="mt-12 grid gap-4 sm:grid-cols-2">
          <Link
            to="/faculty"
            className="group rounded-2xl border border-zinc-800 bg-zinc-900/80 p-8 transition hover:border-violet-500/50 hover:shadow-lg hover:shadow-violet-950/30"
          >
            <p className="text-sm font-semibold uppercase text-violet-400">Faculty</p>
            <p className="mt-2 text-xl font-bold text-zinc-100">Campus Manager</p>
            <p className="mt-2 text-sm text-zinc-500">
              Batches · subjects · announcements · resources
            </p>
          </Link>

          <Link
            to="/student"
            className="group rounded-2xl border border-zinc-800 bg-zinc-900/80 p-8 transition hover:border-sky-500/50 hover:shadow-lg hover:shadow-sky-950/30"
          >
            <p className="text-sm font-semibold uppercase text-sky-400">Student</p>
            <p className="mt-2 text-xl font-bold text-zinc-100">DigiCampus</p>
            <p className="mt-2 text-sm text-zinc-500">
              Feed · deadlines · AI assistant · Jarvis
            </p>
          </Link>
        </div>

        <p className="mt-10 text-xs text-zinc-600">
          Open both portals in separate tabs to test faculty & student in parallel
        </p>
      </div>
    </div>
  );
}
