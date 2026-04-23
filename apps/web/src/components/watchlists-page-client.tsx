"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CreateWatchlistForm } from "@/components/ui/CreateWatchlistForm";
import { DeleteWatchlistButton } from "@/components/ui/DeleteWatchlistButton";
import { RenameWatchlistForm } from "@/components/ui/RenameWatchlistForm";
import {
  getWatchlistsWithSummary,
  waitForApiReady,
  type WatchlistSummary,
} from "@/lib/api";

function statBadge(label: string, value: number, tone: "neutral" | "good" | "warn" = "neutral") {
  const cls =
    tone === "good"
      ? "border-emerald-400/20 bg-emerald-500/10 text-emerald-200"
      : tone === "warn"
        ? "border-rose-400/20 bg-rose-500/10 text-rose-200"
        : "border-white/10 bg-white/5 text-white/75";

  return (
    <div className={`rounded-full border px-3 py-1.5 text-xs font-medium ${cls}`}>
      {label}: {value}
    </div>
  );
}

function formatCreatedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("ro-RO", {
    timeZone: "Europe/Bucharest",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

export default function WatchlistsPageClient() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lists, setLists] = useState<WatchlistSummary[]>([]);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setError(null);

        await waitForApiReady();
        const data = await getWatchlistsWithSummary();
        setLists(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Eroare la încărcare");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  return (
    <main className="min-h-screen bg-[#0b1020] text-white">
      <div className="mx-auto max-w-7xl px-6 py-10 md:px-8 md:py-12">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white/80 shadow-sm transition hover:bg-white/10 hover:text-white"
            >
              ← Înapoi la dashboard
            </Link>

            <h1 className="mt-5 text-4xl font-semibold tracking-tight text-white">
              Liste
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-7 text-white/65">
              Creează, redenumește și administrează listele tale din Chilipir.
            </p>
          </div>
        </div>

        <section className="mt-8 rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm backdrop-blur-sm">
          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div>
              <h2 className="text-xl font-semibold tracking-tight text-white">
                Creează listă nouă
              </h2>
              <p className="mt-2 text-sm text-white/65">
                Adaugă o listă personalizată în Chilipir.
              </p>

              <div className="mt-5">
                <CreateWatchlistForm />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
                <div className="text-xs uppercase tracking-wide text-white/55">
                  Total liste
                </div>
                <div className="mt-2 text-3xl font-semibold tracking-tight text-white">
                  {lists.length}
                </div>
              </div>

              <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
                <div className="text-xs uppercase tracking-wide text-white/55">
                  Total produse
                </div>
                <div className="mt-2 text-3xl font-semibold tracking-tight text-white">
                  {lists.reduce((acc, item) => acc + item.total_items, 0)}
                </div>
              </div>

              <div className="rounded-3xl border border-emerald-400/20 bg-emerald-500/10 p-5 text-emerald-200">
                <div className="text-xs uppercase tracking-wide text-white/55">
                  Total Chilipir
                </div>
                <div className="mt-2 text-3xl font-semibold tracking-tight">
                  {lists.reduce((acc, item) => acc + item.total_chilipir, 0)}
                </div>
              </div>

              <div className="rounded-3xl border border-rose-400/20 bg-rose-500/10 p-5 text-rose-200">
                <div className="text-xs uppercase tracking-wide text-white/55">
                  Total Răsfăț
                </div>
                <div className="mt-2 text-3xl font-semibold tracking-tight">
                  {lists.reduce((acc, item) => acc + item.total_rasfat, 0)}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-8">
          {loading ? (
            <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
              Se încarcă listele...
            </div>
          ) : error ? (
            <div className="rounded-3xl border border-rose-400/20 bg-rose-500/10 p-6 text-rose-100">
              {error}
            </div>
          ) : lists.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 p-10 text-center">
              <h2 className="text-2xl font-semibold tracking-tight text-white">
                Nu există liste încă
              </h2>
              <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-white/60">
                Creează prima listă pentru a începe monitorizarea produselor.
              </p>
            </div>
          ) : (
            <div className="grid gap-6 lg:grid-cols-2">
              {lists.map((list) => (
                <article
                  key={list.id}
                  className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm backdrop-blur-sm"
                >
                  <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div className="min-w-0">
                      <Link
                        href={`/lists/view?id=${list.id}`}
                        className="text-2xl font-semibold tracking-tight text-white transition hover:text-fuchsia-200"
                      >
                        {list.name}
                      </Link>

                      <div className="mt-2 text-sm text-white/50">
                        Creată la: {formatCreatedAt(list.created_at)}
                      </div>

                      <div className="mt-4 flex flex-wrap gap-2">
                        {statBadge("Produse", list.total_items)}
                        {statBadge("Chilipir", list.total_chilipir, "good")}
                        {statBadge("Preț cinstit", list.total_pret_cinstit)}
                        {statBadge("Răsfăț", list.total_rasfat, "warn")}
                      </div>
                    </div>

                    <div>
                      <Link
                        href={`/lists/view?id=${list.id}`}
                        className="inline-flex items-center rounded-full border border-blue-400/20 bg-blue-500/15 px-4 py-2 text-sm font-medium text-blue-100 shadow-sm transition hover:bg-blue-500/25"
                      >
                        Deschide lista
                      </Link>
                    </div>
                  </div>

                  <div className="mt-6 grid gap-4">
                    <RenameWatchlistForm
                      watchlistId={list.id}
                      initialName={list.name}
                    />

                    <DeleteWatchlistButton watchlistId={list.id} />
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
