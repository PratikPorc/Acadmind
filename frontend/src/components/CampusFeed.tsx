import { useEffect, useState } from "react";
import { Card } from "./ui/Card";

export type FeedItem = {
  id: string;
  title: string;
  content: string;
  item_type: string;
  event_category: string;
  group_name: string | null;
  subject_code: string | null;
  batch_code: string | null;
  due_date: string | null;
  created_at: string | null;
};

export type EventCategory = "academic" | "cultural" | "technical" | "global";

function typeVariant(
  t: string,
): "exam" | "assignment" | "resource" | "notice" | "cultural" | "technical" | "default" {
  if (t === "exam") return "exam";
  if (t === "assignment") return "assignment";
  if (t === "resource") return "resource";
  if (t === "notice") return "notice";
  if (t === "cultural") return "cultural";
  if (t === "technical") return "technical";
  return "default";
}

function Badge({
  children,
  variant = "default",
}: {
  children: React.ReactNode;
  variant?:
    | "default"
    | "exam"
    | "assignment"
    | "resource"
    | "notice"
    | "cultural"
    | "technical";
}) {
  const colors = {
    default: "bg-indigo-500/20 text-indigo-300",
    exam: "bg-red-500/20 text-red-300",
    assignment: "bg-amber-500/20 text-amber-300",
    resource: "bg-emerald-500/20 text-emerald-300",
    notice: "bg-sky-500/20 text-sky-300",
    cultural: "bg-fuchsia-500/20 text-fuchsia-300",
    technical: "bg-cyan-500/20 text-cyan-300",
  };
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[variant]}`}>
      {children}
    </span>
  );
}

function FeedList({ items }: { items: FeedItem[] }) {
  if (items.length === 0) {
    return (
      <Card className="p-6 text-center">
        <p className="text-sm text-zinc-500">No announcements in this section yet.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => {
        const category = item.event_category || "academic";
        const badgeVariant =
          category === "cultural" || category === "technical"
            ? typeVariant(category)
            : typeVariant(item.item_type);

        return (
          <Card key={item.id} className="p-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={badgeVariant}>{item.item_type}</Badge>
              {category !== "academic" && (
                <Badge variant={typeVariant(category)}>{category}</Badge>
              )}
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
          </Card>
        );
      })}
    </div>
  );
}

function FeedSection({
  title,
  description,
  items,
}: {
  title: string;
  description: string;
  items: FeedItem[];
}) {
  return (
    <section>
      <div className="mb-3">
        <h3 className="text-base font-semibold text-zinc-100">{title}</h3>
        <p className="text-xs text-zinc-500">{description}</p>
      </div>
      <FeedList items={items} />
    </section>
  );
}

const SECTIONS: { id: EventCategory; title: string; description: string }[] = [
  {
    id: "academic",
    title: "Academic",
    description: "Exams, assignments, subject notices & deadlines from faculty",
  },
  {
    id: "cultural",
    title: "Cultural Events",
    description: "Fests, celebrations, sports & cultural campus activities",
  },
  {
    id: "technical",
    title: "Technical Events",
    description: "Hackathons, workshops, tech fests & seminars",
  },
  {
    id: "global",
    title: "Global Updates",
    description: "Campus-wide updates, holidays & admin notices",
  },
];

export function CampusFeed({
  api,
  refreshKey = 0,
  sectioned = false,
}: {
  api: "faculty" | "student";
  refreshKey?: number;
  sectioned?: boolean;
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

  if (!sectioned) {
    return <FeedList items={items} />;
  }

  return (
    <div className="space-y-8">
      {SECTIONS.map((section) => (
        <FeedSection
          key={section.id}
          title={section.title}
          description={section.description}
          items={items.filter((item) => (item.event_category || "academic") === section.id)}
        />
      ))}
    </div>
  );
}
