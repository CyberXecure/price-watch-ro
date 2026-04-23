"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import EditableTargetPrice from "@/components/editable-target-price";
import WatchlistItemActions from "@/components/watchlist-item-actions";
import { FreshfulImportForm } from "@/components/ui/FreshfulImportForm";
import {
  getWatchlist,
  getWatchlistDetailedItems,
  getWatchlistsWithSummary,
  waitForApiReady,
  type Watchlist,
  type WatchlistDetailedItem,
  type WatchlistSummary,
} from "@/lib/api";
import {
  cardRowClass,
  deltaBadgeClass,
  filterLinkClass,
  formatCapturedAt,
  formatComparison,
  formatNumeric,
  formatPrice,
  formatTarget,
  getComparableDelta,
  getDeltaText,
  getPromoBadgeLabel,
  hasPromo,
  statusBadgeClass,
} from "@/components/watchlist-detail-helpers";

function kpiCard(
  label: string,
  value: number,
  tone: "neutral" | "good" | "warn" = "neutral",
) {
  const toneClass =
    tone === "good"
      ? "border-emerald-400/20 bg-emerald-500/10 text-emerald-200"
      : tone === "warn"
        ? "border-rose-400/20 bg-rose-500/10 text-rose-200"
        : "border-white/10 bg-white/5 text-white";

  return (
    <div className={`rounded-3xl border p-5 ${toneClass}`}>
      <div className="text-xs uppercase tracking-wide text-white/55">
        {label}
      </div>
      <div className="mt-2 text-3xl font-semibold tracking-tight">{value}</div>
    </div>
  );
}

export default function WatchlistDetailClient() {
  const searchParams = useSearchParams();
  const id = searchParams.get("id");
  const promoParam = searchParams.get("promo");
  const viewParam = searchParams.get("view");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [watchlist, setWatchlist] = useState<Watchlist | null>(null);
  const [rawItems, setRawItems] = useState<WatchlistDetailedItem[]>([]);
  const [allWatchlists, setAllWatchlists] = useState<WatchlistSummary[]>([]);

  const watchlistId = Number(id);
  const promoOnly = promoParam === "1";
  const view = viewParam || "active";

  async function reloadData() {
    try {
      setError(null);

      if (!id || Number.isNaN(watchlistId)) {
        throw new Error("ID listă invalid.");
      }

      await waitForApiReady();

      const [watchlistData, itemsData, watchlistsData] = await Promise.all([
        getWatchlist(watchlistId),
        getWatchlistDetailedItems(watchlistId),
        getWatchlistsWithSummary(),
      ]);

      setWatchlist(watchlistData);
      setRawItems(itemsData);
      setAllWatchlists(watchlistsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare la încărcare");
    }
  }

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        await reloadData();
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [id, watchlistId]);

  const sortedItems = useMemo(() => {
    return [...rawItems].sort((a, b) => {
      const aPromo = hasPromo(a) ? 1 : 0;
      const bPromo = hasPromo(b) ? 1 : 0;

      if (aPromo !== bPromo) return bPromo - aPromo;

      const aTs = a.latest_captured_at ? new Date(a.latest_captured_at).getTime() : 0;
      const bTs = b.latest_captured_at ? new Date(b.latest_captured_at).getTime() : 0;

      return bTs - aTs;
    });
  }, [rawItems]);

  const activeItems = useMemo(
    () => sortedItems.filter((item) => item.is_active),
    [sortedItems],
  );

  const hiddenItems = useMemo(
    () => sortedItems.filter((item) => !item.is_active),
    [sortedItems],
  );

  const sourceItems = useMemo(() => {
    if (view === "hidden") return hiddenItems;
    if (view === "all") return sortedItems;
    return activeItems;
  }, [activeItems, hiddenItems, sortedItems, view]);

  const visibleItems = useMemo(() => {
    return promoOnly
      ? sourceItems.filter((item) => hasPromo(item))
      : sourceItems;
  }, [promoOnly, sourceItems]);

  const promoCount = sourceItems.filter((item) => hasPromo(item)).length;
  const bestBuyCount = sourceItems.filter(
    (item) => item.current_status === "best_buy",
  ).length;
  const highPriceCount = sourceItems.filter(
    (item) => item.current_status === "high_price",
  ).length;

  if (loading) {
    return (
      <main className="min-h-screen bg-[#0b1020] text-white">
        <div className="mx-auto max-w-7xl px-6 py-10 md:px-8 md:py-12">
          <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
            Se încarcă lista...
          </div>
        </div>
      </main>
    );
  }

  if (error || !watchlist) {
    return (
      <main className="min-h-screen bg-[#0b1020] text-white">
        <div className="mx-auto max-w-7xl px-6 py-10 md:px-8 md:py-12">
          <Link
            href="/lists"
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white/80 shadow-sm transition hover:bg-white/10 hover:text-white"
          >
            ← Înapoi la liste
          </Link>

          <div className="mt-8 rounded-3xl border border-rose-400/20 bg-rose-500/10 p-6 text-rose-100">
            {error || "Lista nu a putut fi încărcată."}
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#0b1020] text-white">
      <div className="mx-auto max-w-7xl px-6 py-10 md:px-8 md:py-12">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <Link
              href="/lists"
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white/80 shadow-sm transition hover:bg-white/10 hover:text-white"
            >
              ← Înapoi la liste
            </Link>

            <h1 className="mt-5 text-4xl font-semibold tracking-tight text-white">
              {watchlist.name}
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-7 text-white/65">
              Produse urmărite, prețuri, promoții și alerte pentru lista selectată.
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-sm backdrop-blur-sm lg:w-[360px]">
            <div className="text-sm font-medium text-white/70">Alte liste</div>
            <div className="mt-4 flex flex-wrap gap-2">
              {allWatchlists.map((list) => (
                <Link
                  key={list.id}
                  href={`/lists/view?id=${list.id}`}
                  className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                    list.id === watchlistId
                      ? "border-blue-400/20 bg-blue-500/15 text-blue-100 shadow-sm"
                      : "border-white/10 bg-white/5 text-white/75 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  {list.name}
                </Link>
              ))}
            </div>
          </div>
        </div>

        <section className="mt-10 rounded-3xl border border-white/10 bg-white/5 p-6 shadow-sm backdrop-blur-sm">
          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div>
              <h2 className="text-xl font-semibold tracking-tight text-white">
                Importă produse
              </h2>
              <p className="mt-2 text-sm text-white/65">
                Adaugă în această listă produse Freshful pentru monitorizare.
              </p>

              <div className="mt-5">
                <FreshfulImportForm watchlistId={watchlistId} onImported={reloadData} />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {kpiCard("Total produse", sourceItems.length)}
              {kpiCard("Promoții active", promoCount)}
              {kpiCard("Chilipir", bestBuyCount, "good")}
              {kpiCard("Răsfăț", highPriceCount, "warn")}
            </div>
          </div>
        </section>

        <section className="mt-8 rounded-3xl border border-white/10 bg-white/5 p-5 shadow-sm backdrop-blur-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-wrap gap-2">
              <Link
                href={`/lists/view?id=${watchlistId}&view=active${promoOnly ? "&promo=1" : ""}`}
                className={filterLinkClass(view === "active")}
              >
                Active
              </Link>
              <Link
                href={`/lists/view?id=${watchlistId}&view=hidden${promoOnly ? "&promo=1" : ""}`}
                className={filterLinkClass(view === "hidden")}
              >
                Ascunse
              </Link>
              <Link
                href={`/lists/view?id=${watchlistId}&view=all${promoOnly ? "&promo=1" : ""}`}
                className={filterLinkClass(view === "all")}
              >
                Toate
              </Link>
            </div>

            <div className="flex flex-wrap gap-2">
              <Link
                href={`/lists/view?id=${watchlistId}&view=${view}`}
                className={filterLinkClass(!promoOnly)}
              >
                Fără filtru promo
              </Link>
              <Link
                href={`/lists/view?id=${watchlistId}&view=${view}&promo=1`}
                className={filterLinkClass(promoOnly)}
              >
                Doar promoții
              </Link>
            </div>
          </div>

          <div className="mt-4 text-sm text-white/55">
            Promoțiile apar primele.
          </div>
        </section>

        <section className="mt-8">
          {visibleItems.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 p-10 text-center">
              <h2 className="text-2xl font-semibold tracking-tight text-white">
                {promoOnly
                  ? "Nu există promoții pentru filtrul selectat"
                  : view === "hidden"
                    ? "Nu există produse ascunse în această listă"
                    : view === "all"
                      ? "Nu există produse în această listă"
                      : "Nu există produse active în această listă"}
              </h2>

              <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-white/60">
                {promoOnly
                  ? "Revino la toate produsele sau schimbă filtrul."
                  : view === "hidden"
                    ? "Produsele ascunse pot fi reactivate din această secțiune."
                    : "Importă produse Freshful sau schimbă filtrul curent."}
              </p>
            </div>
          ) : (
            <div className="overflow-hidden rounded-3xl border border-white/10 bg-[#0f162d]">
              <div className="grid grid-cols-[minmax(320px,2.2fr)_1fr_1fr_1fr_1fr_1.1fr] gap-4 border-b border-white/10 px-5 py-4 text-xs font-semibold uppercase tracking-wide text-white/45">
                <div>Produs</div>
                <div>Preț</div>
                <div>Preț unitar</div>
                <div>Țintă</div>
                <div>Status</div>
                <div>Acțiuni / actualizat</div>
              </div>

              {visibleItems.map((item) => {
                const safeImageUrl = item.product_image_url?.includes("cdn.freshful.ro")
                  ? item.product_image_url
                  : null;

                const itemHasPromo = hasPromo(item);
                const availabilityText = item.latest_availability?.trim().toLowerCase() ?? "";
                const isUnavailable =
                  availabilityText === "out_of_stock" ||
                  availabilityText.includes("indispon") ||
                  availabilityText.includes("unavailable");
                const delta = getComparableDelta(item);

                return (
                  <article
                    key={item.watchlist_item_id}
                    className={`grid grid-cols-[minmax(320px,2.2fr)_1fr_1fr_1fr_1fr_1.1fr] gap-4 border-b border-white/10 px-5 py-5 align-start last:border-b-0 ${cardRowClass(itemHasPromo)}`}
                  >
                    <div className="flex gap-4">
                      <div className="relative h-20 w-20 overflow-hidden rounded-2xl border border-white/10 bg-white/5">
                        {safeImageUrl ? (
                          <Image
                            src={safeImageUrl}
                            alt={item.product_title}
                            fill
                            className="object-cover"
                            sizes="80px"
                          />
                        ) : (
                          <div className="flex h-full w-full items-center justify-center text-center text-xs text-white/40">
                            Fără imagine
                          </div>
                        )}
                      </div>

                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          {itemHasPromo && !isUnavailable ? (
                            <span className="rounded-full border border-fuchsia-400/20 bg-fuchsia-500/15 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-fuchsia-200">
                              {getPromoBadgeLabel(item)}
                            </span>
                          ) : null}

                          {isUnavailable ? (
                            <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-white/70">
                              Indisponibil
                            </span>
                          ) : null}

                          {!item.is_active ? (
                            <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-white/60">
                              Ascuns
                            </span>
                          ) : null}
                        </div>

                        <a
                          href={item.product_url}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-2 block text-lg font-semibold leading-6 text-white transition hover:text-fuchsia-200"
                        >
                          {item.product_title}
                        </a>

                        <div className="mt-2 flex flex-wrap gap-2 text-xs text-white/55">
                          {item.product_brand ? (
                            <span className="rounded-full bg-white/5 px-2.5 py-1">
                              {item.product_brand}
                            </span>
                          ) : null}

                          {item.product_category ? (
                            <span className="rounded-full bg-white/5 px-2.5 py-1">
                              {item.product_category}
                            </span>
                          ) : null}

                          {item.package_text ? (
                            <span className="rounded-full bg-white/5 px-2.5 py-1">
                              {item.package_text}
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </div>

                    <div>
                      <div className="text-2xl font-semibold tracking-tight text-white">
                        {formatPrice(item.latest_price_total)}
                      </div>

                      {item.latest_old_price ? (
                        <div className="mt-1 text-sm text-white/40 line-through">
                          {formatPrice(item.latest_old_price)}
                        </div>
                      ) : null}

                      {(item.latest_promo_label || item.latest_discount_percent) && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {item.latest_promo_label ? (
                            <span className="rounded-full border border-fuchsia-400/20 bg-fuchsia-500/15 px-2.5 py-1 text-xs font-medium text-fuchsia-100">
                              {item.latest_promo_label}
                            </span>
                          ) : null}

                          {item.latest_discount_percent ? (
                            <span className="rounded-full border border-emerald-400/20 bg-emerald-500/15 px-2.5 py-1 text-xs font-medium text-emerald-100">
                              -{item.latest_discount_percent.toFixed(0)}%
                            </span>
                          ) : null}
                        </div>
                      )}

                      {item.latest_deposit_value ? (
                        <div className="mt-3 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-white/70">
                          SGR: +{formatPrice(item.latest_deposit_value)}
                        </div>
                      ) : null}
                    </div>

                    <div>
                      <div className="text-lg font-semibold text-white">
                        {formatComparison(
                          item.latest_comparison_price,
                          item.latest_comparison_unit,
                        )}
                      </div>

                      {item.latest_unit_price_value !== null &&
                      item.latest_unit_price_value !== undefined &&
                      item.latest_unit_price_unit ? (
                        <div className="mt-2 text-sm text-white/60">
                          Preț unitar: {formatNumeric(item.latest_unit_price_value)} lei
                        </div>
                      ) : (
                        <div className="mt-2 text-sm text-white/35">
                          Preț unitar indisponibil
                        </div>
                      )}
                    </div>

                    <div>
                      <div className="text-lg font-semibold text-white">
                        {formatTarget(item.target_price, item.target_unit)}
                      </div>

                      <div
                        className={`mt-3 inline-flex rounded-full border px-3 py-1.5 text-xs font-medium ${deltaBadgeClass(delta)}`}
                      >
                        {getDeltaText(item)}
                      </div>
                    </div>

                    <div>
                      <div
                        className={`inline-flex rounded-full border px-3 py-1.5 text-xs font-semibold ${statusBadgeClass(item.current_status)}`}
                      >
                        {item.current_status_label}
                      </div>

                      <div className="mt-3 flex flex-wrap gap-2">
                        {itemHasPromo && !isUnavailable ? (
                          <span className="rounded-full border border-fuchsia-400/20 bg-fuchsia-500/15 px-2.5 py-1 text-[11px] font-medium text-fuchsia-100">
                            {getPromoBadgeLabel(item)}
                          </span>
                        ) : null}

                        {!item.is_active ? (
                          <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] font-medium text-white/60">
                            Ascuns
                          </span>
                        ) : null}
                      </div>
                    </div>

                    <div>
                      <EditableTargetPrice
                        watchlistId={watchlistId}
                        itemId={item.watchlist_item_id}
                        targetPrice={item.target_price}
                        targetUnit={item.target_unit}
                        onChanged={reloadData}
                      />

                      <WatchlistItemActions
                        watchlistId={watchlistId}
                        itemId={item.watchlist_item_id}
                        productUrl={item.product_url}
                        isActive={item.is_active}
                        onChanged={reloadData}
                      />

                      <div className="mt-4 text-xs text-white/45">
                        Actualizat: {formatCapturedAt(item.latest_captured_at)}
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}








