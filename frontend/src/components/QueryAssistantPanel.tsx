import { type FormEvent, useState } from "react";
import { sendQuery } from "../api/student";
import { Card } from "./ui/Card";

type Source = {
  type: string;
  title: string;
  subject?: string;
  batch?: string;
  due_date?: string;
};

export function QueryAssistantPanel() {
  const [message, setMessage] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await sendQuery(message.trim());
      setAnswer(result.answer);
      setSources(result.sources ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="p-6">
      <header className="mb-4">
        <h2 className="text-lg font-semibold text-zinc-100">Ask AcadMind AI</h2>
        <p className="text-sm text-zinc-500">
          Query deadlines, exams & assignments from your campus graph
        </p>
      </header>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="When is the CN exam? What's due this week?"
          rows={3}
          className="input-dark w-full resize-none"
        />
        <button
          type="submit"
          disabled={loading}
          className="self-start rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          {loading ? "Searching…" : "Ask"}
        </button>
      </form>

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
      {answer && (
        <div className="mt-4 rounded-xl bg-zinc-800/80 p-4 text-sm text-zinc-300 whitespace-pre-wrap">
          {answer}
        </div>
      )}
      {sources.length > 0 && (
        <ul className="mt-4 space-y-2">
          {sources.map((s, i) => (
            <li key={i} className="rounded-lg bg-indigo-500/10 px-3 py-2 text-xs text-indigo-200">
              {s.title}
              {s.subject && ` · ${s.subject}`}
              {s.due_date && ` · due ${s.due_date}`}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
