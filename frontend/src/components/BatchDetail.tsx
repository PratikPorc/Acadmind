import { type FormEvent, useEffect, useState } from "react";
import {
  addStudentToBatch,
  addSubjectToBatch,
  fetchBatchDetail,
  fetchBatchPosts,
  removeStudentFromBatch,
  type BatchDetail,
  type PostSummary,
} from "../api/faculty";
import { Card } from "./ui/Card";

type Props = {
  batchId: string;
  onBack: () => void;
};

type Tab = "posts" | "students" | "subjects";

export function BatchDetail({ batchId, onBack }: Props) {
  const [batch, setBatch] = useState<BatchDetail | null>(null);
  const [posts, setPosts] = useState<PostSummary[]>([]);
  const [tab, setTab] = useState<Tab>("posts");
  const [error, setError] = useState<string | null>(null);
  const [enrollmentId, setEnrollmentId] = useState("");
  const [subName, setSubName] = useState("");
  const [subCode, setSubCode] = useState("");
  const [loading, setLoading] = useState(false);

  const STUDENT_ID_PATTERN = /^\d{12}$/;

  function normalizeStudentId(value: string) {
    return value.replace(/\D/g, "").slice(0, 12);
  }

  async function load() {
    try {
      const [detail, postList] = await Promise.all([
        fetchBatchDetail(batchId),
        fetchBatchPosts(batchId),
      ]);
      setBatch(detail);
      setPosts(postList);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load batch");
    }
  }

  useEffect(() => {
    load();
  }, [batchId]);

  async function handleAddStudent(e: FormEvent) {
    e.preventDefault();
    const id = enrollmentId.trim();
    if (!STUDENT_ID_PATTERN.test(id)) {
      setError("Enter the full 12-digit Student ID (e.g. 231003003137)");
      return;
    }
    setLoading(true);
    try {
      await addStudentToBatch(batchId, id);
      setEnrollmentId("");
      setError(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add student");
    } finally {
      setLoading(false);
    }
  }

  async function handleRemoveStudent(id: string) {
    if (!confirm(`Remove ${id} from this batch?`)) return;
    setLoading(true);
    try {
      await removeStudentFromBatch(batchId, id);
      setError(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove student");
    } finally {
      setLoading(false);
    }
  }

  async function handleAddSubject(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await addSubjectToBatch(batchId, { name: subName, code: subCode });
      setSubName("");
      setSubCode("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add subject");
    } finally {
      setLoading(false);
    }
  }

  if (!batch) return <p className="text-sm text-zinc-500">Loading batch…</p>;

  const tabs: { id: Tab; label: string }[] = [
    { id: "posts", label: "Notices" },
    { id: "subjects", label: "Subjects" },
    { id: "students", label: "Students" },
  ];

  return (
    <section>
      <button type="button" onClick={onBack} className="mb-4 text-sm text-violet-400 hover:underline">
        ← Back to dashboard
      </button>

      <div className="mb-6">
        <p className="text-xs font-semibold uppercase text-violet-400">{batch.code}</p>
        <h2 className="text-2xl font-bold text-zinc-100">{batch.name}</h2>
        <p className="text-sm text-zinc-500">
          Sem {batch.semester} · {batch.branch} · {batch.subject_count} subjects ·{" "}
          {batch.student_count} students
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="mb-6 flex flex-wrap gap-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              tab === t.id ? "bg-indigo-600 text-white" : "bg-zinc-800 text-zinc-400"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "posts" && (
        <div className="space-y-3">
          {posts.length === 0 ? (
            <Card className="p-6 text-center text-sm text-zinc-500">No posts yet.</Card>
          ) : (
            posts.map((p) => (
              <Card key={p.id} className="p-4">
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-indigo-500/20 px-2 py-0.5 text-xs text-indigo-300">
                    {p.post_type}
                  </span>
                  <span className="rounded-full bg-zinc-700/80 px-2 py-0.5 text-xs text-zinc-400">
                    {p.event_category || "academic"}
                  </span>
                  {p.subject_code && (
                    <span className="text-xs text-zinc-500">{p.subject_code}</span>
                  )}
                  {p.due_date && (
                    <span className="ml-auto text-xs text-amber-400">Due {p.due_date}</span>
                  )}
                </div>
                <p className="mt-2 text-sm text-zinc-300">{p.content}</p>
              </Card>
            ))
          )}
        </div>
      )}

      {tab === "subjects" && (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-2">
            {batch.subjects.map((s) => (
              <Card key={s.id} className="px-4 py-3">
                <span className="font-medium text-violet-400">{s.code}</span>
                <span className="text-zinc-400"> — {s.name}</span>
              </Card>
            ))}
          </div>
          <Card className="p-4">
            <h4 className="font-medium text-zinc-100">Add subject</h4>
            <form onSubmit={handleAddSubject} className="mt-3 space-y-2">
              <input
                placeholder="Name"
                value={subName}
                onChange={(e) => setSubName(e.target.value)}
                required
                className="input-dark w-full"
              />
              <input
                placeholder="Code (CN)"
                value={subCode}
                onChange={(e) => setSubCode(e.target.value)}
                required
                className="input-dark w-full"
              />
              <button
                type="submit"
                disabled={loading}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white"
              >
                Add
              </button>
            </form>
          </Card>
        </div>
      )}

      {tab === "students" && (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-2">
            {batch.student_enrollment_ids.length === 0 ? (
              <Card className="p-4 text-sm text-zinc-500">No students added yet.</Card>
            ) : (
              batch.student_enrollment_ids.map((id) => (
                <Card key={id} className="flex items-center justify-between px-4 py-2">
                  <span className="font-mono text-sm text-zinc-300">{id}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveStudent(id)}
                    disabled={loading}
                    className="rounded-lg px-2 py-1 text-xs text-red-400 hover:bg-red-500/10 disabled:opacity-50"
                  >
                    Remove
                  </button>
                </Card>
              ))
            )}
          </div>
          <Card className="p-4">
            <h4 className="font-medium text-zinc-100">Add student by ID</h4>
            <p className="mt-1 text-xs text-zinc-500">
              Enter the full 12-digit Student ID from signup (e.g. 231003003137). This links the
              student to the batch so they can see notices and ASK Jarvis about batch content.
            </p>
            <form onSubmit={handleAddStudent} className="mt-3 space-y-2">
              <input
                placeholder="231003003137"
                value={enrollmentId}
                onChange={(e) => setEnrollmentId(normalizeStudentId(e.target.value))}
                required
                minLength={12}
                maxLength={12}
                inputMode="numeric"
                pattern="\d{12}"
                title="12-digit Student ID"
                className="input-dark w-full font-mono"
              />
              <p className="text-xs text-zinc-600">
                {enrollmentId.length}/12 digits
                {enrollmentId.length === 12 ? " — ready to add" : ""}
              </p>
              <button
                type="submit"
                disabled={loading || enrollmentId.length !== 12}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white disabled:opacity-50"
              >
                Add to batch
              </button>
            </form>
          </Card>
        </div>
      )}
    </section>
  );
}
