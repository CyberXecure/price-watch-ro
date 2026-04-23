"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  getDashboardSummary,
  getWatchlistsWithSummary,
  waitForApiReady,
  type DashboardSummary,
  type WatchlistSummary,
} from "@/lib/api";

function statCard(
  label: string,
  value: number | string,
  tone: "neutral" | "good" | "warn" | "accent" = "neutral",
) {
  const toneClass =
    tone === "good"
      ? "border-emerald-400/20 bg-emerald-500/10 text-emerald-200"
      : tone === "warn"
        ? "border-rose-400/20 bg-rose-500/10 text-rose-200"
        : tone === "accent"
          ? "border-blue-400/20 bg-blue-500/10 text-blue-100"
          : "border-white/10 bg-white/5 text-white";

  return (
    <div className={`rounded-3xl border p-5 shadow-sm ${toneClass}`}>
      <div className="text-xs uppercase tracking-wide text-white/55">
        {label}
      </div>
      <div className="mt-2 text-3xl font-semibold tracking-tight">
        {value}
      </div>
    </div>
  );
}

function quickActionLink(href: string, label: string, primary = false) {
  return (
    <Link
      href={href}
      className={
        primary
          ? "rounded-full border border-blue-400/20 bg-blue-500/15 px-4 py-2 text-sm font-medium text-blue-100 transition hover:bg-blue-500/20"
          : "rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white/85 transition hover:bg-white/10"
      }
    >
      {label}
    </Link>
  );
}

export default function DashboardHomeClient() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [watchlists, setWatchlists] = useState<WatchlistSummary[]>([]);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setError(null);

        await waitForApiReady();

        const [summaryData, watchlistsData] = await Promise.all([
          getDashboardSummary(),
          getWatchlistsWithSummary(),
        ]);

        setSummary(summaryData);
        setWatchlists(watchlistsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Eroare la încărcare");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  const sortedWatchlists = useMemo(() => {
    return [...watchlists].sort((a, b) => {
      if ((b.total_chilipir ?? 0) !== (a.total_chilipir ?? 0)) {
        return (b.total_chilipir ?? 0) - (a.total_chilipir ?? 0);
      }

      if ((b.total_items ?? 0) !== (a.total_items ?? 0)) {
        return (b.total_items ?? 0) - (a.total_items ?? 0);
      }

      return a.name.localeCompare(b.name, "ro");
    });
  }, [watchlists]);

  const topOpportunityWatchlists = useMemo(() => {
    return [...watchlists]
      .filter((list) => (list.total_items ?? 0) > 0)
      .sort((a, b) => {
        if ((b.total_chilipir ?? 0) !== (a.total_chilipir ?? 0)) {
          return (b.total_chilipir ?? 0) - (a.total_chilipir ?? 0);
        }

        if ((a.total_rasfat ?? 0) !== (b.total_rasfat ?? 0)) {
          return (a.total_rasfat ?? 0) - (b.total_rasfat ?? 0);
        }

        if ((b.total_items ?? 0) !== (a.total_items ?? 0)) {
          return (b.total_items ?? 0) - (a.total_items ?? 0);
        }

        return a.name.localeCompare(b.name, "ro");
      })
      .slice(0, 5);
  }, [watchlists]);

  const totalPretCinstit =
    summary?.total_pret_cinstit ??
    Math.max(
      0,
      (summary?.total_products ?? 0) -
        (summary?.total_chilipir ?? 0) -
        (summary?.total_rasfat ?? 0),
    );

  const topWatchlists = sortedWatchlists.slice(0, 6);
  const totalPromoActive = watchlists.reduce(
    (sum, list) => sum + (list.total_chilipir ?? 0),
    0,
  );

  return (
    <main className="min-h-screen bg-[#0b1020] text-white">
      <div className="mx-auto max-w-7xl px-6 py-10 md:px-8 md:py-12">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="text-sm font-medium text-white/60">Chilipir</div>
            <h1 className="mt-2 text-4xl font-semibold tracking-tight text-white">
              Radar de prețuri
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-white/65">
              Vezi rapid starea listelor, produsele avantajoase și zonele unde
              prețurile au depășit țintele setate.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {quickActionLink("/lists", "Vezi listele", true)}
            {quickActionLink("/lists", "Administrează")}
          </div>
        </div>

        {loading ? (
          <div className="mt-8 rounded-3xl border border-white/10 bg-white/5 p-6">
            Se încarcă dashboard-ul...
          </div>
        ) : error ? (
          <div className="mt-8 rounded-3xl border border-rose-400/20 bg-rose-500/10 p-6 text-rose-100">
            {error}
          </div>
        ) : (
          <>
            <section className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
              {statCard("Liste", summary?.total_watchlists ?? 0, "accent")}
              {statCard("Produse", summary?.total_products ?? 0)}
              {statCard("Chilipir", summary?.total_chilipir ?? 0, "good")}
              {statCard("Preț cinstit", totalPretCinstit)}
              {statCard("Răsfăț", summary?.total_rasfat ?? 0, "warn")}
            </section>

            <section className="mt-8 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
              <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <h2 className="text-2xl font-semibold tracking-tight text-white">
                      Liste urmărite
                    </h2>
                    <p className="mt-2 text-sm text-white/60">
                      Acces rapid către listele cele mai active.
                    </p>
                  </div>

                  <Link
                    href="/lists"
                    className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white/85 transition hover:bg-white/10"
                  >
                    Deschide toate
                  </Link>
                </div>

                <div className="mt-6 space-y-3">
                  {topWatchlists.length === 0 ? (
                    <div className="rounded-2xl border border-white/10 bg-[#0f162d] p-4 text-sm text-white/65">
                      Nu există liste încă.
                    </div>
                  ) : (
                    topWatchlists.map((list) => (
                      <Link
                        key={list.id}
                        href={`/lists/view?id=${list.id}`}
                        className="block rounded-2xl border border-white/10 bg-[#0f162d] p-4 transition hover:bg-white/10"
                      >
                        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                          <div>
                            <div className="text-lg font-semibold text-white">
                              {list.name}
                            </div>
                            <div className="mt-2 text-sm text-white/60">
                              Produse: {list.total_items}
                            </div>
                          </div>

                          <div className="flex flex-wrap gap-2 text-xs">
                            <span className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-2.5 py-1 text-emerald-200">
                              Chilipir: {list.total_chilipir}
                            </span>
                            <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-white/75">
                              Preț cinstit: {list.total_pret_cinstit}
                            </span>
                            <span className="rounded-full border border-rose-400/20 bg-rose-500/10 px-2.5 py-1 text-rose-200">
                              Răsfăț: {list.total_rasfat}
                            </span>
                          </div>
                        </div>
                      </Link>
                    ))
                  )}
                </div>
              </div>

              <div className="space-y-6">
                <section className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm">
                  <h2 className="text-xl font-semibold tracking-tight text-white">
                    Rezumat rapid
                  </h2>

                  <div className="mt-5 space-y-3">
                    <div className="rounded-2xl border border-white/10 bg-[#0f162d] p-4">
                      <div className="text-sm text-white/60">Promoții active</div>
                      <div className="mt-1 text-2xl font-semibold text-white">
                        {totalPromoActive}
                      </div>
                    </div>

                    <div className="rounded-2xl border border-white/10 bg-[#0f162d] p-4">
                      <div className="text-sm text-white/60">Liste cu produse</div>
                      <div className="mt-1 text-2xl font-semibold text-white">
                        {watchlists.filter((x) => (x.total_items ?? 0) > 0).length}
                      </div>
                    </div>

                    <div className="rounded-2xl border border-white/10 bg-[#0f162d] p-4">
                      <div className="text-sm text-white/60">
                        Zone care cer atenție
                      </div>
                      <div className="mt-1 text-2xl font-semibold text-white">
                        {summary?.total_rasfat ?? 0}
                      </div>
                    </div>
                  </div>
                </section>

                <section className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm">
                  <h2 className="text-xl font-semibold tracking-tight text-white">
                    Top oportunități acum
                  </h2>
                  <p className="mt-2 text-sm text-white/60">
                    Listele cu cele mai multe produse avantajoase chiar acum.
                  </p>

                  <div className="mt-5 space-y-3">
                    {topOpportunityWatchlists.length === 0 ? (
                      <div className="rounded-2xl border border-white/10 bg-[#0f162d] p-4 text-sm text-white/65">
                        Nu există suficiente date încă.
                      </div>
                    ) : (
                      topOpportunityWatchlists.map((list, index) => (
                        <Link
                          key={list.id}
                          href={`/lists/view?id=${list.id}`}
                          className="block rounded-2xl border border-white/10 bg-[#0f162d] p-4 transition hover:bg-white/10"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="rounded-full border border-blue-400/20 bg-blue-500/10 px-2 py-0.5 text-[11px] font-semibold text-blue-100">
                                  #{index + 1}
                                </span>
                                <div className="truncate text-sm font-semibold text-white">
                                  {list.name}
                                </div>
                              </div>

                              <div className="mt-2 text-xs text-white/60">
                                Produse: {list.total_items}
                              </div>
                            </div>

                            <div className="flex flex-col items-end gap-1 text-xs">
                              <span className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-2.5 py-1 text-emerald-200">
                                Chilipir: {list.total_chilipir}
                              </span>
                              <span className="rounded-full border border-rose-400/20 bg-rose-500/10 px-2.5 py-1 text-rose-200">
                                Răsfăț: {list.total_rasfat}
                              </span>
                            </div>
                          </div>
                        </Link>
                      ))
                    )}
                  </div>
                </section>

                <section className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm">
                  <h2 className="text-xl font-semibold tracking-tight text-white">
                    Recomandare
                  </h2>
                  <p className="mt-3 text-sm leading-7 text-white/65">
                    Începe cu listele care au cele mai multe produse în
                    <span className="text-emerald-200"> Chilipir</span>, apoi
                    verifică secțiunile unde ai produse marcate ca
                    <span className="text-rose-200"> Răsfăț</span>.
                  </p>

                  <div className="mt-5">
                    <Link
                      href="/lists"
                      className="inline-flex rounded-full border border-blue-400/20 bg-blue-500/15 px-4 py-2 text-sm font-medium text-blue-100 transition hover:bg-blue-500/20"
                    >
                      Deschide listele
                    </Link>
                  </div>
                </section>
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
