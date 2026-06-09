import { useEffect, useState } from "react";
import { Card } from "./ui/Card";

export type FeedItem = {
  id: string;
  title: string;
  content: string;
  item_type: string;
  subject_code: string | null;
  batch_code: string | null;
  due_date: string | null;
  file_name: string | null;
  created_at: string | null;
};

function typeVariant(t: string): "exam" | "assignment" | "resource" | "notice" | "default" {
  if (t === "exam") return "exam";
  if (t === "assignment") return "assignment";
  if (t === "resource") return "resource";
  if (t === "notice") return "notice";
  return "default";
}

function Badge({
  children,
  variant = "default",
}: {
  children: React.ReactNode;
  variant?: "default" | "exam" | "assignment" | "resource" | "notice";
}) {
  const colors = {
    default: "bg-indigo-500/20 text-indigo-300",
    exam: "bg-red-500/20 text-red-300",
    assignment: "bg-amber-500/20 text-amber-300",
    resource: "bg-emerald-500/20 text-emerald-300",
    notice: "bg-sky-500/20 text-sky-300",
  };
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[variant]}`}>
      {children}
    </span>
  );
}

export function CampusFeed({
  api,
  refreshKey = 0,
}: {
  api: "faculty" | "student";
  refreshKey?: number;
}) {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const mod = api === "faculty" ? await import("../api/faculty") : await import("../api/student");
        setItems(await mod.fetchFeed());
      } catch {
        setItems([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [api, refreshKey]);

  if (loading) return <p className="text-sm text-zinc-500">Loading campus feed…</p>;

  if (items.length === 0) {
    return (
      <Card className="p-8 text-center">
        <p className="text-zinc-500">No announcements yet.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <Card key={item.id} className="p-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={typeVariant(item.item_type)}>{item.item_type}</Badge>
            {item.batch_code && <span className="text-xs text-zinc-500">{item.batch_code}</span>}
            {item.subject_code && (
              <span className="text-xs font-medium text-indigo-400">{item.subject_code}</span>
            )}
            {item.due_date && (
              <span className="ml-auto text-xs text-amber-400">Due {item.due_date}</span>
            )}
          </div>
          <h4 className="mt-2 font-medium text-zinc-100">{item.title}</h4>
          {item.content && item.content !== item.title && (
            <p className="mt-1 text-sm text-zinc-400">{item.content}</p>
          )}
          {item.file_name && <p className="mt-2 text-xs text-emerald-400">📎 {item.file_name}</p>}
        </Card>
      ))}
    </div>
  );
}
