import { type ChangeEvent, useRef, useState } from "react";
import { uploadScreenshot } from "../api/student";
import { Card } from "./ui/Card";

export function JarvisPanel() {
  const [fileName, setFileName] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setLoading(true);
    setError(null);
    try {
      const response = await uploadScreenshot(file);
      setResult(response.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="p-6">
      <header className="mb-4">
        <h2 className="text-lg font-semibold text-zinc-100">Jarvis Memory</h2>
        <p className="text-sm text-zinc-500">
          Upload screenshots from WhatsApp, email, or notice boards
        </p>
      </header>

      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />
      <button
        type="button"
        onClick={() => fileRef.current?.click()}
        disabled={loading}
        className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-zinc-700 bg-zinc-800/50 py-10 text-sm text-zinc-400 hover:border-sky-500/50 hover:text-sky-300"
      >
        <span className="text-xl">📎</span>
        {loading ? "Uploading…" : fileName ?? "Upload screenshot"}
      </button>

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
      {result && (
        <div className="mt-4 rounded-xl bg-zinc-800/80 p-4 text-sm text-zinc-300">{result}</div>
      )}
    </Card>
  );
}
