import Image from "next/image";
import Link from "next/link";
import EditableTargetPrice from "@/components/editable-target-price";
import WatchlistItemActions from "@/components/watchlist-item-actions";
import { FreshfulImportForm } from "@/components/ui/FreshfulImportForm";
import {
  getWatchlist,
  getWatchlistDetailedItems,
  getWatchlistsWithSummary,
  type WatchlistDetailedItem,
} from "@/lib/api";

type PageProps = {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ promo?: string; view?: string }>;
};

function formatPrice(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  if (value < 0.01) return `${value.toFixed(4)} lei`;
  return `${value.toFixed(2)} lei`;
}

function formatNumeric(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  if (value < 0.01) return value.toFixed(4);
  return value.toFixed(2);
}

function normalizeUnit(unit: string | null | undefined): string {
  if (!unit) return "";
  return unit;
}

function formatComparison(
  value: number | null | undefined,
  unit: string | null | undefined,
): string {
  if (value === null || value === undefined || !unit) return "-";
  return `${formatNumeric(value)} ${normalizeUnit(unit)}`;
}

function formatCapturedAt(value: string | null | undefined): string {
  if (!value) return "-";

  const normalized = /[zZ]|[+\-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`;
  const date = new Date(normalized);

  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("ro-RO", {
    timeZone: "Europe/Bucharest",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

function statusBadgeClass(status: string): string {
  if (status === "best_buy") {
    return "border-emerald-400/20 bg-emerald-500/10 text-emerald-300";
  }

  if (status === "high_price") {
    return "border-rose-400/20 bg-rose-500/10 text-rose-300";
  }

  return "border-amber-400/20 bg-amber-500/10 text-amber-300";
}

function cardRowClass(hasPromo: boolean): string {
  return hasPromo
    ? "bg-gradient-to-r from-fuchsia-500/10 via-fuchsia-500/5 to-transparent"
    : "";
}

function hasPromo(item: {
  latest_promo_label?: string | null;
  latest_discount_percent?: number | null;
  latest_old_price?: number | null;
}) {
  return (
    !!item.latest_promo_label ||
    !!item.latest_discount_percent ||
    !!item.latest_old_price
  );
}

function getComparableDelta(item: WatchlistDetailedItem): number | null {
  if (
    item.target_price === null ||
    item.target_price === undefined ||
    item.latest_comparison_price === null ||
    item.latest_comparison_price === undefined
  ) {
    return null;
  }

  if (
    item.target_unit &&
    item.latest_comparison_unit &&
    item.target_unit !== item.latest_comparison_unit
  ) {
    return null;
  }

  return item.latest_comparison_price - item.target_price;
}

function getDeltaTone(delta: number | null): "good" | "neutral" | "warn" {
  if (delta === null) return "neutral";
  if (delta <= 0) return "good";
  return "warn";
}

function getDeltaText(item: WatchlistDetailedItem): string {
  const delta = getComparableDelta(item);

  if (delta === null) {
    return "Comparație indisponibilă";
  }

  const abs = Math.abs(delta);
  const unit = item.target_unit || item.latest_comparison_unit || "";

  if (delta <= 0) {
    return `${formatNumeric(abs)} lei sub țintă${unit ? ` · ${unit}` : ""}`;
  }

  return `${formatNumeric(abs)} lei peste țintă${unit ? ` · ${unit}` : ""}`;
}

function deltaBadgeClass(delta: number | null): string {
  const tone = getDeltaTone(delta);

  if (tone === "good") {
    return "border-emerald-400/20 bg-emerald-500/10 text-emerald-200";
  }

  if (tone === "warn") {
    return "border-rose-400/20 bg-rose-500/10 text-rose-200";
  }

  return "border-white/10 bg-white/5 text-white/65";
}

function filterLinkClass(isActive: boolean): string {
  return isActive
    ? "rounded-full border border-blue-400/20 bg-blue-500/15 px-3 py-1.5 text-xs font-medium text-blue-100 shadow-sm"
    : "rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/65 transition hover:bg-white/10 hover:text-white";
}

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
    <div className={`rounded-2xl border p-4 ${toneClass}`}>
      <div className="text-xs uppercase tracking-wide text-white/55">{label}</div>
      <div className="mt-2 text-3xl font-semibold tracking-tight">{value}</div>
    </div>
  );
}

export default async function WatchlistDetailPage({
  params,
  searchParams,
}: PageProps) {
  const { id } = await params;
  const resolvedSearchParams = searchParams ? await searchParams : {};

  const watchlistId = Number(id);
  const promoOnly = resolvedSearchParams?.promo === "1";
  const view = resolvedSearchParams?.view || "active";

  if (Number.isNaN(watchlistId)) {
    throw new Error("Invalid watchlist id");
  }

  const [watchlist, rawItems, allWatchlists] = await Promise.all([
    getWatchlist(watchlistId),
    getWatchlistDetailedItems(watchlistId),
    getWatchlistsWithSummary(),
  ]);

  const sortedItems = [...rawItems].sort((a, b) => {
    const aPromo = hasPromo(a) ? 1 : 0;
    const bPromo = hasPromo(b) ? 1 : 0;

    if (aPromo !== bPromo) return bPromo - aPromo;

    const aTs = a.latest_captured_at ? new Date(a.latest_captured_at).getTime() : 0;
    const bTs = b.latest_captured_at ? new Date(b.latest_captured_at).getTime() : 0;

    return bTs - aTs;
  });

  const activeItems = sortedItems.filter((item) => item.is_active);
  const hiddenItems = sortedItems.filter((item) => !item.is_active);
  const sourceItems =
    view === "hidden" ? hiddenItems : view === "all" ? sortedItems : activeItems;
  const visibleItems = promoOnly
    ? sourceItems.filter((item) => hasPromo(item))
    : sourceItems;

  const promoCount = sourceItems.filter((item) => hasPromo(item)).length;
  const bestBuyCount = sourceItems.filter(
    (item) => item.current_status === "best_buy",
  ).length;
  const highPriceCount = sourceItems.filter(
    (item) => item.current_status === "high_price",
  ).length;

  const basePath = `/lists/${watchlistId}`;

  return (
    <main className="min-h-screen bg-[#0b1020] text-white">
      <div className="mx-auto max-w-7xl px-6 py-8 md:px-8 md:py-10">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <Link
              href="/lists"
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white/70 transition hover:bg-white/10 hover:text-white"
            >
              ← Înapoi la liste
            </Link>

            <h1 className="mt-5 text-4xl font-semibold tracking-tight">
              {watchlist.name}
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-7 text-white/65">
              Produse urmărite, prețuri, promoții și alerte pentru lista selectată.
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/5 p-5 lg:w-[360px]">
            <div className="text-sm font-medium text-white/70">Alte liste</div>
            <div className="mt-4 flex flex-wrap gap-2">
              {allWatchlists.map((list) => (
                <Link
                  key={list.id}
                  href={`/lists/${list.id}`}
                  className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                    list.id === watchlistId
                      ? "border-white/10 bg-white text-black"
                      : "border-white/10 bg-white/5 text-white/75 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  {list.name}
                </Link>
              ))}
            </div>
          </div>
        </div>

        <section className="mt-8 rounded-3xl border border-white/10 bg-white/5 p-6">
          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div>
              <h2 className="text-xl font-semibold tracking-tight">Importă produse</h2>
              <p className="mt-2 text-sm text-white/65">
                Adaugă în această listă produse Freshful pentru monitorizare.
              </p>

              <div className="mt-5">
                <FreshfulImportForm watchlistId={watchlistId} />
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

        <section className="mt-8 rounded-3xl border border-white/10 bg-white/5 p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-wrap gap-2">
              <Link
                href={`${basePath}?view=active${promoOnly ? "&promo=1" : ""}`}
                className={filterLinkClass(view === "active")}
              >
                Active
              </Link>
              <Link
                href={`${basePath}?view=hidden${promoOnly ? "&promo=1" : ""}`}
                className={filterLinkClass(view === "hidden")}
              >
                Ascunse
              </Link>
              <Link
                href={`${basePath}?view=all${promoOnly ? "&promo=1" : ""}`}
                className={filterLinkClass(view === "all")}
              >
                Toate
              </Link>
            </div>

            <div className="flex flex-wrap gap-2">
              <Link
                href={`${basePath}?view=${view}`}
                className={filterLinkClass(!promoOnly)}
              >
                Fără filtru promo
              </Link>
              <Link
                href={`${basePath}?view=${view}&promo=1`}
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
              <h2 className="text-2xl font-semibold tracking-tight">
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
                const safeImageUrl = item.product_image_url?.includes(
                  "cdn.freshful.ro",
                )
                  ? item.product_image_url
                  : null;
                const itemHasPromo = hasPromo(item);
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
                          {itemHasPromo ? (
                            <span className="rounded-full border border-fuchsia-400/20 bg-fuchsia-500/15 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-fuchsia-200">
                              Promo
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
                          Preț unitar: {formatNumeric(item.latest_unit_price_value)}{" "}
                          lei/{item.latest_unit_price_unit}
                        </div>
                      ) : (
                        <div className="mt-2 text-sm text-white/35">
                          Preț unitar indisponibil
                        </div>
                      )}
                    </div>

                    <div>
                      <div className="text-lg font-semibold text-white">
                        {item.target_price !== null && item.target_price !== undefined
                          ? `${formatNumeric(item.target_price)} lei${
                              item.target_unit ? `/${item.target_unit}` : ""
                            }`
                          : "-"}
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
                        {itemHasPromo ? (
                          <span className="rounded-full border border-fuchsia-400/20 bg-fuchsia-500/15 px-2.5 py-1 text-[11px] font-medium text-fuchsia-100">
                            Promo activ
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
                        currentTargetPrice={item.target_price}
                        currentTargetUnit={item.target_unit}
                      />

                      <WatchlistItemActions
                        watchlistId={watchlistId}
                        itemId={item.watchlist_item_id}
                        productUrl={item.product_url}
                        isActive={item.is_active}
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