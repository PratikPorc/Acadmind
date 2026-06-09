import { type FormEvent, useEffect, useRef, useState } from "react";
import {
  createPost,
  fetchBatchDetail,
  fetchBatches,
  type BatchResponse,
  type SubjectResponse,
} from "../api/faculty";
import { Card } from "./ui/Card";

export function PostComposer({ onPosted }: { onPosted?: () => void }) {
  const [batches, setBatches] = useState<BatchResponse[]>([]);
  const [subjects, setSubjects] = useState<SubjectResponse[]>([]);
  const [batchId, setBatchId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [content, setContent] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchBatches().then(setBatches).catch(() => setBatches([]));
  }, []);

  useEffect(() => {
    if (!batchId) {
      setSubjects([]);
      setSubjectId("");
      return;
    }
    fetchBatchDetail(batchId)
      .then((d) => {
        setSubjects(d.subjects);
        setSubjectId(d.subjects[0]?.id ?? "");
      })
      .catch(() => setSubjects([]));
  }, [batchId]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!batchId || !subjectId) {
      setError("Select batch and subject");
      return;
    }
    if (!content.trim() && !file) {
      setError("Write something or attach a file");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await createPost(batchId, subjectId, content, file);
      setContent("");
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      onPosted?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to post");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="p-5">
      <h3 className="font-semibold text-zinc-100">Create announcement</h3>
      <p className="mt-1 text-sm text-zinc-500">
        Like DigiCampus — post notices, exams, assignments & resources
      </p>

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <div className="grid gap-3 sm:grid-cols-2">
          <select
            value={batchId}
            onChange={(e) => setBatchId(e.target.value)}
            required
            className="rounded-xl border border-zinc-700 bg-zinc-800/80 px-4 py-2.5 text-sm text-zinc-100 outline-none focus:border-indigo-500"
          >
            <option value="">Select batch</option>
            {batches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.code} — {b.name}
              </option>
            ))}
          </select>
          <select
            value={subjectId}
            onChange={(e) => setSubjectId(e.target.value)}
            required
            disabled={!batchId}
            className="rounded-xl border border-zinc-700 bg-zinc-800/80 px-4 py-2.5 text-sm text-zinc-100 outline-none focus:border-indigo-500 disabled:opacity-50"
          >
            <option value="">Select subject</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.code} — {s.name}
              </option>
            ))}
          </select>
        </div>

        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={3}
          placeholder="CN exam on 15th July · Assignment 4 of SE due 5th June…"
          className="w-full resize-none rounded-xl border border-zinc-700 bg-zinc-800/50 px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-600 outline-none focus:border-indigo-500"
        />

        {file && (
          <p className="text-xs text-indigo-300">📎 {file.name}</p>
        )}

        <div className="flex items-center justify-between gap-3">
          <div className="flex gap-2">
            <input
              ref={fileRef}
              type="file"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              className="flex items-center gap-2 rounded-xl border border-zinc-700 bg-zinc-800 px-4 py-2 text-sm text-zinc-300 hover:border-indigo-500 hover:text-indigo-300"
            >
              <span>📎</span> Upload
            </button>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="rounded-xl bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {loading ? "Publishing…" : "Post"}
          </button>
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}
      </form>
    </Card>
  );
}
