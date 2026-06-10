import { type FormEvent, useEffect, useState } from "react";
import {
  createPost,
  fetchBatchDetail,
  fetchBatches,
  fetchCampusOptions,
  type BatchResponse,
  type CampusOptions,
  type SubjectResponse,
} from "../api/faculty";
import { Card } from "./ui/Card";

type EventCategory = "academic" | "cultural" | "technical" | "global";

const CATEGORIES: { id: EventCategory; label: string; hint: string }[] = [
  { id: "academic", label: "Academic", hint: "Select batch and subject" },
  { id: "cultural", label: "Cultural", hint: "Select club from the list" },
  { id: "technical", label: "Technical", hint: "Select domain from the list" },
  { id: "global", label: "Global", hint: "Campus-wide — select scope: academic, cultural, or technical" },
];

const selectClass =
  "rounded-xl border border-zinc-700 bg-zinc-800/80 px-4 py-2.5 text-sm text-zinc-100 outline-none focus:border-indigo-500 disabled:opacity-50";

export function PostComposer({ onPosted }: { onPosted?: () => void }) {
  const [batches, setBatches] = useState<BatchResponse[]>([]);
  const [subjects, setSubjects] = useState<SubjectResponse[]>([]);
  const [options, setOptions] = useState<CampusOptions | null>(null);
  const [batchId, setBatchId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [category, setCategory] = useState<EventCategory>("academic");
  const [clubName, setClubName] = useState("");
  const [domainName, setDomainName] = useState("");
  const [globalScope, setGlobalScope] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchBatches()
      .then((list) => {
        setBatches(list);
        const demo = list.find((b) => b.code === "CSE6A") ?? list[0];
        if (demo) setBatchId(demo.id);
      })
      .catch(() => setBatches([]));
    fetchCampusOptions().then(setOptions).catch(() => setOptions(null));
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

  useEffect(() => {
    setClubName("");
    setDomainName("");
    setGlobalScope("");
    setSubjectId(subjects[0]?.id ?? "");
  }, [category, subjects]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!batchId) {
      setError("Select a batch");
      return;
    }
    if (category === "academic" && !subjectId) {
      setError("Select a subject");
      return;
    }
    if (category === "cultural" && !clubName) {
      setError("Select a club");
      return;
    }
    if (category === "technical" && !domainName) {
      setError("Select a domain");
      return;
    }
    if (category === "global" && !globalScope) {
      setError("Select global scope: academic, cultural, or technical");
      return;
    }
    if (!content.trim()) {
      setError("Write a notice to seed the knowledge graph");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await createPost({
        batchId,
        subjectId: category === "academic" ? subjectId : null,
        content,
        eventCategory: category,
        groupName: category === "cultural" ? clubName : category === "technical" ? domainName : null,
        globalScope: category === "global" ? globalScope : null,
      });
      setContent("");
      setClubName("");
      setDomainName("");
      setGlobalScope("");
      setSuccess(result.message ?? "Notice posted — Jarvis can answer questions about it.");
      onPosted?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to post");
    } finally {
      setLoading(false);
    }
  }

  const clubs = options?.clubs ?? [];
  const domains = options?.domains ?? [];
  const scopes = options?.global_scopes ?? [];

  return (
    <Card className="p-5">
      <h3 className="font-semibold text-zinc-100">Post campus notice</h3>
      <p className="mt-1 text-sm text-zinc-500">
        Faculty notices seed the Neo4j knowledge graph for student RAG queries
      </p>

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => setCategory(c.id)}
              className={`rounded-xl px-4 py-2 text-sm font-medium ${
                category === c.id
                  ? "bg-indigo-600 text-white"
                  : "border border-zinc-700 bg-zinc-800/80 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-zinc-600">
          {CATEGORIES.find((c) => c.id === category)?.hint}
        </p>

        <select
          value={batchId}
          onChange={(e) => setBatchId(e.target.value)}
          required
          className={`w-full ${selectClass}`}
        >
          <option value="">Select batch</option>
          {batches.map((b) => (
            <option key={b.id} value={b.id}>
              {b.code} — {b.name}
            </option>
          ))}
        </select>

        {category === "academic" && (
          <select
            value={subjectId}
            onChange={(e) => setSubjectId(e.target.value)}
            required
            disabled={!batchId}
            className={`w-full ${selectClass}`}
          >
            <option value="">Select subject</option>
            {subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.code} — {s.name}
              </option>
            ))}
          </select>
        )}

        {category === "cultural" && (
          <select
            value={clubName}
            onChange={(e) => setClubName(e.target.value)}
            required
            className={`w-full ${selectClass}`}
          >
            <option value="">Select club</option>
            {clubs.map((club) => (
              <option key={club} value={club}>
                {club}
              </option>
            ))}
          </select>
        )}

        {category === "technical" && (
          <select
            value={domainName}
            onChange={(e) => setDomainName(e.target.value)}
            required
            className={`w-full ${selectClass}`}
          >
            <option value="">Select domain</option>
            {domains.map((domain) => (
              <option key={domain} value={domain}>
                {domain}
              </option>
            ))}
          </select>
        )}

        {category === "global" && (
          <select
            value={globalScope}
            onChange={(e) => setGlobalScope(e.target.value)}
            required
            className={`w-full ${selectClass}`}
          >
            <option value="">Select scope</option>
            {scopes.map((scope) => (
              <option key={scope} value={scope}>
                {scope.charAt(0).toUpperCase() + scope.slice(1)}
              </option>
            ))}
          </select>
        )}

        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={3}
          placeholder={
            category === "academic"
              ? "CN exam on 15th July · SE Assignment 4 due 5th June…"
              : category === "cultural"
                ? "Annual cultural fest on 20th March at Main Auditorium…"
                : category === "technical"
                  ? "Hackathon registration closes 10th August…"
                  : "University closed on 15th August for Independence Day…"
          }
          className="w-full resize-none rounded-xl border border-zinc-700 bg-zinc-800/50 px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-600 outline-none focus:border-indigo-500"
        />

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="rounded-xl bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {loading ? "Seeding graph…" : "Post notice"}
          </button>
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}
        {success && <p className="text-sm text-emerald-400">{success}</p>}
      </form>
    </Card>
  );
}
