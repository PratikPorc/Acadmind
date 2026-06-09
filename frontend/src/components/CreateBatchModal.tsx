import { type FormEvent, useState } from "react";

type Props = {
  onClose: () => void;
  onCreate: (data: { name: string; code: string; semester: string; branch: string }) => Promise<void>;
};

export function CreateBatchModal({ onClose, onCreate }: Props) {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [semester, setSemester] = useState("VI");
  const [branch, setBranch] = useState("CSE");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onCreate({ name, code, semester, branch });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
        <h3 className="text-lg font-semibold text-zinc-100">Create batch</h3>
        <form onSubmit={handleSubmit} className="mt-4 space-y-3">
          <input
            placeholder="Batch name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="input-dark w-full"
          />
          <input
            placeholder="Code (CSE6A)"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            required
            className="input-dark w-full"
          />
          <div className="grid grid-cols-2 gap-3">
            <input
              placeholder="Semester"
              value={semester}
              onChange={(e) => setSemester(e.target.value)}
              className="input-dark w-full"
            />
            <input
              placeholder="Branch"
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              className="input-dark w-full"
            />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-zinc-400">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white disabled:opacity-50"
            >
              {loading ? "Creating…" : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
