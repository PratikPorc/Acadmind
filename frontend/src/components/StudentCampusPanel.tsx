import { useEffect, useMemo, useState } from "react";
import {
  fetchCampusGroups,
  fetchFeed,
  fetchSubjects,
  type CampusGroup,
  type FeedItem,
  type StudentSubject,
} from "../api/student";
import { Card } from "./ui/Card";

type CampusTab = "academic" | "cultural" | "technical" | "global";

const TABS: { id: CampusTab; label: string }[] = [
  { id: "academic", label: "Academic" },
  { id: "cultural", label: "Cultural Events" },
  { id: "technical", label: "Technical Events" },
  { id: "global", label: "Global Updates" },
];

function FeedList({ items }: { items: FeedItem[] }) {
  if (items.length === 0) {
    return (
      <Card className="p-8 text-center">
        <p className="text-sm text-zinc-500">No notices in this view yet.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <Card key={item.id} className="p-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-indigo-500/20 px-2.5 py-0.5 text-xs font-medium text-indigo-300">
              {item.item_type}
            </span>
            {item.batch_code && <span className="text-xs text-zinc-500">{item.batch_code}</span>}
            {item.subject_code && (
              <span className="text-xs font-medium text-sky-400">{item.subject_code}</span>
            )}
            {item.global_scope && (
              <span className="text-xs font-medium text-emerald-400">{item.global_scope}</span>
            )}
            {item.group_name && (
              <span className="text-xs font-medium text-violet-400">{item.group_name}</span>
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
      ))}
    </div>
  );
}

function Sidebar({
  title,
  items,
  selected,
  onSelect,
  emptyLabel,
}: {
  title: string;
  items: { id: string; label: string; sublabel?: string }[];
  selected: string | null;
  onSelect: (id: string | null) => void;
  emptyLabel: string;
}) {
  return (
    <aside className="lg:sticky lg:top-24 lg:self-start">
      <Card className="p-3">
        <p className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
          {title}
        </p>
        <nav className="space-y-1">
          <button
            type="button"
            onClick={() => onSelect(null)}
            className={`w-full rounded-lg px-3 py-2 text-left text-sm ${
              selected === null
                ? "bg-indigo-600 text-white"
                : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
            }`}
          >
            All
          </button>
          {items.length === 0 ? (
            <p className="px-3 py-2 text-xs text-zinc-600">{emptyLabel}</p>
          ) : (
            items.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => onSelect(item.id)}
                className={`w-full rounded-lg px-3 py-2 text-left text-sm ${
                  selected === item.id
                    ? "bg-indigo-600 text-white"
                    : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                }`}
              >
                <span className="font-medium">{item.label}</span>
                {item.sublabel && (
                  <span className="mt-0.5 block text-xs opacity-70">{item.sublabel}</span>
                )}
              </button>
            ))
          )}
        </nav>
      </Card>
    </aside>
  );
}

export function StudentCampusPanel() {
  const [tab, setTab] = useState<CampusTab>("academic");
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [subjects, setSubjects] = useState<StudentSubject[]>([]);
  const [clubs, setClubs] = useState<CampusGroup[]>([]);
  const [domains, setDomains] = useState<CampusGroup[]>([]);
  const [filter, setFilter] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [feedItems, subjectList, clubList, domainList] = await Promise.all([
          fetchFeed(),
          fetchSubjects(),
          fetchCampusGroups("cultural"),
          fetchCampusGroups("technical"),
        ]);
        setFeed(feedItems);
        setSubjects(subjectList);
        setClubs(clubList);
        setDomains(domainList);
      } catch {
        setFeed([]);
        setSubjects([]);
        setClubs([]);
        setDomains([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  useEffect(() => {
    setFilter(null);
  }, [tab]);

  const categoryFeed = useMemo(
    () => feed.filter((item) => (item.event_category || "academic") === tab),
    [feed, tab],
  );

  const filteredFeed = useMemo(() => {
    if (!filter) return categoryFeed;
    if (tab === "academic") {
      return categoryFeed.filter((item) => item.subject_code === filter);
    }
    return categoryFeed.filter((item) => (item.group_name || "General") === filter);
  }, [categoryFeed, filter, tab]);

  const sidebarItems = useMemo(() => {
    if (tab === "academic") {
      return subjects.map((s) => ({
        id: s.code,
        label: s.code,
        sublabel: s.name,
      }));
    }
    if (tab === "cultural") {
      const fromFeed = [
        ...new Set(
          categoryFeed.map((i) => i.group_name).filter((g): g is string => Boolean(g)),
        ),
      ];
      const names = fromFeed.length > 0 ? fromFeed : clubs.map((c) => c.name);
      return names.map((name) => ({ id: name, label: name }));
    }
    if (tab === "technical") {
      const fromFeed = [
        ...new Set(
          categoryFeed.map((i) => i.group_name).filter((g): g is string => Boolean(g)),
        ),
      ];
      const names = fromFeed.length > 0 ? fromFeed : domains.map((d) => d.name);
      return names.map((name) => ({ id: name, label: name }));
    }
    return [];
  }, [tab, subjects, clubs, domains, categoryFeed]);

  if (loading) {
    return <p className="text-sm text-zinc-500">Loading campus notices…</p>;
  }

  return (
    <div>
      <nav className="mb-4 flex flex-wrap gap-2 border-b border-zinc-800 pb-4">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              tab === t.id
                ? "bg-indigo-600 text-white"
                : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === "global" ? (
        <FeedList items={categoryFeed} />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[220px_1fr]">
          <Sidebar
            title={
              tab === "academic"
                ? "My Subjects"
                : tab === "cultural"
                  ? "Clubs"
                  : "Domains"
            }
            items={sidebarItems}
            selected={filter}
            onSelect={setFilter}
            emptyLabel={
              tab === "academic"
                ? "No subjects assigned yet."
                : tab === "cultural"
                  ? "No clubs yet."
                  : "No domains yet."
            }
          />
          <div>
            <FeedList items={filteredFeed} />
          </div>
        </div>
      )}
    </div>
  );
}
