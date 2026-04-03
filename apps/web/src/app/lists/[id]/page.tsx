import Image from "next/image";
import Link from "next/link";
import EditableTargetPrice from "@/components/editable-target-price";
import WatchlistItemActions from "@/components/watchlist-item-actions";
import {
  getWatchlist,
  getWatchlistDetailedItems,
  getWatchlistsWithSummary,
} from "@/lib/api";

type PageProps = {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ promo?: string }>;
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

function statusBadgeClass(status: string): string {
  if (status === "best_buy") {
    return "border-emerald-400/20 bg-emerald-500/10 text-emerald-300";
  }
  if (status === "high_price") {
    return "border-rose-400/20 bg-rose-500/10 text-rose-300";
  }
  return "border-slate-400/20 bg-white/5 text-slate-300";
}

function cardRowClass(hasPromo: boolean): string {
  return hasPromo
    ? "bg-gradient-to-r from-fuchsia-500/5 via-transparent to-transparent"
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

export default async function WatchlistDetailPage({
  params,
  searchParams,
}: PageProps) {
  const { id } = await params;
  const resolvedSearchParams = searchParams ? await searchParams : {};
  const watchlistId = Number(id);
  const promoOnly = resolvedSearchParams?.promo === "1";

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

    const aTs = a.latest_captured_at
      ? new Date(a.latest_captured_at).getTime()
      : 0;
    const bTs = b.latest_captured_at
      ? new Date(b.latest_captured_at).getTime()
      : 0;

    return bTs - aTs;
  });

  const visibleItems = promoOnly
    ? sortedItems.filter((item) => hasPromo(item))
    : sortedItems;

  const promoCount = rawItems.filter((item) => hasPromo(item)).length;
  const bestBuyCount = rawItems.filter(
    (item) => item.current_status === "best_buy",
  ).length;
  const highPriceCount = rawItems.filter(
    (item) => item.current_status === "high_price",
  ).length;

  const basePath = `/lists/${watchlistId}`;

  return (
    <main className="mx-auto max-w-7xl px-6 py-8">
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="mb-2">
            <Link
              href="/lists"
              className="text-sm text-slate-400 transition hover:text-slate-200"
            >
              ← Înapoi la liste
            </Link>
          </div>

          <h1 className="text-4xl font-bold tracking-tight text-white">
            {watchlist.name}
          </h1>

          <p className="mt-2 text-slate-400">
            Produse urmărite, prețuri, promoții și alerte pentru lista selectată.
          </p>
        </div>

        <div className="rounded-3xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
          <div className="font-medium text-white">Alte liste</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {allWatchlists.map((list) => (
              <Link
                key={list.id}
                href={`/lists/${list.id}`}
                className={`rounded-full border px-3 py-1 transition ${
                  list.id === watchlistId
                    ? "border-blue-400/20 bg-blue-500/10 text-blue-200"
                    : "border-white/10 bg-white/5 text-slate-300 hover:bg-white/10"
                }`}
              >
                {list.name}
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="mb-6 grid gap-3 md:grid-cols-4">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="text-xs uppercase tracking-wide text-slate-400">
            Total produse
          </div>
          <div className="mt-2 text-2xl font-semibold text-white">
            {rawItems.length}
          </div>
        </div>

        <div className="rounded-2xl border border-fuchsia-400/15 bg-fuchsia-500/5 p-4">
          <div className="text-xs uppercase tracking-wide text-fuchsia-200/80">
            Promoții active
          </div>
          <div className="mt-2 text-2xl font-semibold text-fuchsia-100">
            {promoCount}
          </div>
        </div>

        <div className="rounded-2xl border border-emerald-400/15 bg-emerald-500/5 p-4">
          <div className="text-xs uppercase tracking-wide text-emerald-200/80">
            Chilipir
          </div>
          <div className="mt-2 text-2xl font-semibold text-emerald-100">
            {bestBuyCount}
          </div>
        </div>

        <div className="rounded-2xl border border-rose-400/15 bg-rose-500/5 p-4">
          <div className="text-xs uppercase tracking-wide text-rose-200/80">
            Răsfăț
          </div>
          <div className="mt-2 text-2xl font-semibold text-rose-100">
            {highPriceCount}
          </div>
        </div>
      </div>

      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          <Link
            href={basePath}
            className={`rounded-full border px-4 py-2 text-sm transition ${
              !promoOnly
                ? "border-white/10 bg-white/10 text-white"
                : "border-white/10 bg-white/5 text-slate-300 hover:bg-white/10"
            }`}
          >
            Toate
          </Link>

          <Link
            href={`${basePath}?promo=1`}
            className={`rounded-full border px-4 py-2 text-sm transition ${
              promoOnly
                ? "border-fuchsia-400/20 bg-fuchsia-500/10 text-fuchsia-200"
                : "border-white/10 bg-white/5 text-slate-300 hover:bg-white/10"
            }`}
          >
            Doar promoții
          </Link>
        </div>

        <div className="text-sm text-slate-400">
          Sortare: promoțiile apar primele
        </div>
      </div>

      {visibleItems.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-white/15 bg-white/5 p-10 text-center shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
          <p className="text-lg font-semibold text-white">
            {promoOnly
              ? "Nu există promoții active în această listă"
              : "Nu există produse în această listă"}
          </p>
          <p className="mt-2 text-sm text-slate-400">
            {promoOnly
              ? "Revino la toate produsele sau importă oferte Freshful."
              : "Importă produse Freshful pentru a începe urmărirea."}
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-3xl border border-white/10 bg-[#0b1320] shadow-[0_20px_60px_rgba(0,0,0,0.28)]">
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="border-b border-white/10 bg-white/5 text-left text-slate-300">
                <tr>
                  <th className="p-3 font-medium">Produs</th>
                  <th className="p-3 font-medium">Preț</th>
                  <th className="p-3 font-medium">Comparație</th>
                  <th className="p-3 font-medium">Țintă</th>
                  <th className="p-3 font-medium">Status</th>
                  <th className="p-3 font-medium">Acțiuni</th>
                  <th className="p-3 font-medium">Actualizat</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-white/5">
                {visibleItems.map((item) => {
                  const safeImageUrl =
                    item.product_image_url?.includes("cdn.freshful.ro")
                      ? item.product_image_url
                      : null;

                  const itemHasPromo = hasPromo(item);

                  return (
                    <tr
                      key={item.watchlist_item_id}
                      className={`align-top transition hover:bg-white/[0.03] ${cardRowClass(itemHasPromo)}`}
                    >
                      <td className="p-3">
                        <div className="flex min-w-[300px] gap-3">
                          <div className="relative h-[72px] w-[72px] shrink-0 overflow-hidden rounded-2xl border border-white/10 bg-white/5">
                            {safeImageUrl ? (
                              <Image
                                src={safeImageUrl}
                                alt={item.product_title}
                                width={72}
                                height={72}
                                className="h-[72px] w-[72px] object-cover"
                              />
                            ) : (
                              <div className="flex h-full w-full items-center justify-center text-xs text-slate-500">
                                Fără imagine
                              </div>
                            )}

                            {itemHasPromo ? (
                              <div className="absolute left-1.5 top-1.5 rounded-full bg-fuchsia-500 px-2 py-0.5 text-[10px] font-semibold text-white shadow">
                                PROMO
                              </div>
                            ) : null}
                          </div>

                          <div className="min-w-0">
                            <a
                              href={item.product_url}
                              target="_blank"
                              rel="noreferrer"
                              className="line-clamp-2 font-semibold text-white transition hover:text-blue-300"
                            >
                              {item.product_title}
                            </a>

                            <div className="mt-1 space-y-1 text-xs text-slate-400">
                              {item.product_brand ? <div>{item.product_brand}</div> : null}
                              {item.product_category ? <div>{item.product_category}</div> : null}
                              {item.package_text ? <div>{item.package_text}</div> : null}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="p-3 align-top">
                        <div className="space-y-1.5">
                          <div className="text-base font-semibold text-white">
                            {formatPrice(item.latest_price_total)}
                          </div>

                          {item.latest_old_price ? (
                            <div className="text-sm text-slate-400 line-through">
                              {formatPrice(item.latest_old_price)}
                            </div>
                          ) : null}

                          {item.latest_promo_label || item.latest_discount_percent ? (
                            <div className="flex flex-wrap gap-2">
                              {item.latest_promo_label ? (
                                <span className="rounded-full border border-fuchsia-400/20 bg-fuchsia-500/10 px-2.5 py-1 text-xs font-medium text-fuchsia-200">
                                  {item.latest_promo_label}
                                </span>
                              ) : null}

                              {item.latest_discount_percent ? (
                                <span className="rounded-full border border-rose-400/20 bg-rose-500/10 px-2.5 py-1 text-xs font-medium text-rose-200">
                                  -{item.latest_discount_percent.toFixed(0)}%
                                </span>
                              ) : null}
                            </div>
                          ) : null}

                          {item.latest_deposit_value ? (
                            <div className="text-xs text-slate-400">
                              SGR: +{formatPrice(item.latest_deposit_value)}
                            </div>
                          ) : null}
                        </div>
                      </td>

                      <td className="p-3 align-top text-slate-200">
                        <div className="space-y-1">
                          <div>
                            {formatComparison(
                              item.latest_comparison_price,
                              item.latest_comparison_unit,
                            )}
                          </div>

                          {item.latest_unit_price_value !== null &&
                          item.latest_unit_price_value !== undefined &&
                          item.latest_unit_price_unit ? (
                            <div className="text-xs text-slate-400">
                              unitar: {formatNumeric(item.latest_unit_price_value)} lei/
                              {item.latest_unit_price_unit}
                            </div>
                          ) : null}
                        </div>
                      </td>

                      <td className="p-3 align-top text-slate-200">
                        <EditableTargetPrice
                          watchlistId={item.watchlist_id}
                          itemId={item.watchlist_item_id}
                          targetPrice={item.target_price}
                          targetUnit={item.target_unit}
                        />
                      </td>

                      <td className="p-3 align-top">
                        <div className="flex flex-wrap gap-2">
                          <span
                            className={`inline-flex rounded-full border px-3 py-1 text-xs font-medium ${statusBadgeClass(item.current_status)}`}
                          >
                            {item.current_status_label}
                          </span>

                          {itemHasPromo ? (
                            <span className="inline-flex rounded-full border border-amber-400/20 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-200">
                              ofertă activă
                            </span>
                          ) : null}
                        </div>
                      </td>

                      <td className="p-3 align-top">
                        <WatchlistItemActions
                          watchlistId={item.watchlist_id}
                          itemId={item.watchlist_item_id}
                          productUrl={item.product_url}
                          isActive={item.is_active}
                        />
                      </td>

                      <td className="p-3 align-top text-slate-400">
                        {item.latest_captured_at
                          ? new Date(item.latest_captured_at).toLocaleString("ro-RO")
                          : "-"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
  );
}