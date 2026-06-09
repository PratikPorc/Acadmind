import { type FormEvent, useState } from "react";
import { useAuth } from "../contexts/AuthContext";

type Mode = "signin" | "signup";

export function AuthPage() {
  const { portal, signIn, signUp } = useAuth();

  const [mode, setMode] = useState<Mode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [enrollmentId, setEnrollmentId] = useState("");
  const [semester, setSemester] = useState("VI");
  const [branch, setBranch] = useState("CSE");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const portalLabel = portal === "faculty" ? "Faculty Portal" : "Student Portal";
  const accent = portal === "faculty" ? "text-violet-400" : "text-sky-400";

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setInfo(null);
    setLoading(true);

    try {
      if (mode === "signin") {
        await signIn(email, password);
      } else {
        if (portal === "student" && !/^\d{12}$/.test(enrollmentId.trim())) {
          throw new Error("Student ID must be exactly 12 digits (e.g. 231003003137)");
        }
        await signUp({
          email,
          password,
          fullName,
          role: portal === "faculty" ? "faculty" : "student",
          enrollmentId: enrollmentId.trim() || undefined,
          semester: semester || undefined,
          branch: branch || undefined,
        });
        setInfo(
          portal === "student"
            ? "Account created! Share your Student ID with faculty so they can add you to a batch."
            : "Account created. Welcome!",
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#08080d] px-4">
      <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-900/90 p-8 shadow-2xl shadow-indigo-950/20">
        <p className={`text-xs font-semibold uppercase tracking-wider ${accent}`}>{portalLabel}</p>
        <h1 className="mt-1 text-2xl font-bold text-zinc-100">
          {mode === "signin" ? "Sign in" : "Create account"}
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          {portal === "faculty"
            ? "Manage batches & campus announcements"
            : "Access notices, deadlines & AI assistant"}
        </p>

        <div className="mt-6 flex gap-2 rounded-xl bg-zinc-800/80 p-1">
          {(["signin", "signup"] as Mode[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={`flex-1 rounded-lg py-2 text-sm font-medium capitalize ${
                mode === m ? "bg-zinc-700 text-zinc-100" : "text-zinc-500"
              }`}
            >
              {m === "signin" ? "Sign in" : "Sign up"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          {mode === "signup" && (
            <>
              <input
                type="text"
                placeholder="Full name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                className="input-dark w-full"
              />
              {portal === "student" && (
                <>
                  <input
                    type="text"
                    placeholder="231003003137"
                    value={enrollmentId}
                    onChange={(e) =>
                      setEnrollmentId(e.target.value.replace(/\D/g, "").slice(0, 12))
                    }
                    required
                    minLength={12}
                    maxLength={12}
                    inputMode="numeric"
                    pattern="\d{12}"
                    title="12-digit Student ID"
                    className="input-dark w-full font-mono"
                  />
                  <p className="-mt-2 text-xs text-zinc-600">
                    Full 12-digit ID — faculty adds this to connect you to your batch (
                    {enrollmentId.length}/12)
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    <input
                      type="text"
                      placeholder="Semester"
                      value={semester}
                      onChange={(e) => setSemester(e.target.value)}
                      className="input-dark w-full"
                    />
                    <input
                      type="text"
                      placeholder="Branch"
                      value={branch}
                      onChange={(e) => setBranch(e.target.value)}
                      className="input-dark w-full"
                    />
                  </div>
                </>
              )}
            </>
          )}

          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="input-dark w-full"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            className="input-dark w-full"
          />

          {error && <p className="text-sm text-red-400">{error}</p>}
          {info && <p className="text-sm text-emerald-400">{info}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-indigo-600 py-3 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
          >
            {loading ? "Please wait…" : mode === "signin" ? "Sign in" : "Create account"}
          </button>
        </form>
      </div>
    </div>
  );
}
