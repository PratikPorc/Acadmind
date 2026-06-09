import { useEffect, useState } from "react";
import { createBatch, fetchBatches, type BatchResponse } from "../api/faculty";
import { CreateBatchModal } from "./CreateBatchModal";
import { Card } from "./ui/Card";

type Props = {
  onSelectBatch: (batchId: string) => void;
};

export function BatchGrid({ onSelectBatch }: Props) {
  const [batches, setBatches] = useState<BatchResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  async function load() {
    setLoading(true);
    try {
      setBatches(await fetchBatches());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load batches");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) return <p className="text-sm text-zinc-500">Loading batches…</p>;

  return (
    <section>
      <div className="mb-4 flex items-center justify-end">
        <button
          type="button"
          onClick={() => setShowCreate(true)}
          className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500"
        >
          + New batch
        </button>
      </div>

      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      {batches.length === 0 ? (
        <Card className="border-dashed p-12 text-center">
          <p className="text-zinc-500">No batches yet. Create your first batch.</p>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {batches.map((batch) => (
            <button
              key={batch.id}
              type="button"
              onClick={() => onSelectBatch(batch.id)}
              className="text-left"
            >
              <Card className="p-5 transition hover:border-violet-500/50 hover:bg-zinc-800/80">
                <p className="text-xs font-semibold uppercase text-violet-400">{batch.code}</p>
                <h3 className="mt-1 text-lg font-semibold text-zinc-100">{batch.name}</h3>
                <p className="mt-1 text-sm text-zinc-500">
                  Sem {batch.semester} · {batch.branch}
                </p>
                <div className="mt-4 flex gap-4 text-xs text-zinc-400">
                  <span>{batch.subject_count} subjects</span>
                  <span>{batch.student_count} students</span>
                </div>
              </Card>
            </button>
          ))}
        </div>
      )}

      {showCreate && (
        <CreateBatchModal
          onClose={() => setShowCreate(false)}
          onCreate={async (data) => {
            await createBatch(data);
            setShowCreate(false);
            await load();
          }}
        />
      )}
    </section>
  );
}
