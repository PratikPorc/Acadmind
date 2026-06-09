import { useAuth } from "../contexts/AuthContext";

export function UserMenu() {
  const { profile, signOut } = useAuth();

  if (!profile) return null;

  const roleColors = {
    student: "bg-sky-500/20 text-sky-300",
    faculty: "bg-violet-500/20 text-violet-300",
    admin: "bg-amber-500/20 text-amber-300",
  } as const;

  return (
    <div className="flex items-center gap-3">
      <div className="text-right">
        <p className="text-sm font-medium text-zinc-100">
          {profile.full_name ?? profile.email}
        </p>
        <span
          className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium capitalize ${roleColors[profile.role]}`}
        >
          {profile.role}
        </span>
        {profile.role === "student" && profile.enrollment_id && (
          <p className="mt-0.5 font-mono text-xs text-zinc-500">ID: {profile.enrollment_id}</p>
        )}
      </div>
      <button
        type="button"
        onClick={() => signOut()}
        className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-800"
      >
        Sign out
      </button>
    </div>
  );
}
