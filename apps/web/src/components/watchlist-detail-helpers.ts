import type { WatchlistDetailedItem } from "@/lib/api";

export function formatPrice(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  if (value < 0.01) return `${value.toFixed(4)} lei`;
  return `${value.toFixed(2)} lei`;
}

export function formatNumeric(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  if (value < 0.01) return value.toFixed(4);
  return value.toFixed(2);
}

export function formatUnitLabel(unit: string | null | undefined): string {
  if (!unit) return "";

  const raw = unit.trim();
  if (!raw) return "";

  const normalized = raw.toUpperCase();

  if (normalized.includes("LEI_PER_BUC")) return "buc";
  if (normalized.includes("LEI_PER_KG")) return "kg";
  if (normalized.includes("LEI_PER_L")) return "l";
  if (normalized === "TOTAL") return "total";

  const lower = raw.toLowerCase();
  if (lower === "lei/buc" || lower === "buc" || lower === "/buc") return "buc";
  if (lower === "lei/kg" || lower === "kg" || lower === "/kg") return "kg";
  if (lower === "lei/l" || lower === "l" || lower === "/l") return "l";
  if (lower === "total") return "total";

  return lower;
}

export function formatComparison(
  value: number | null | undefined,
  unit: string | null | undefined,
): string {
  if (value === null || value === undefined) return "-";

  const label = formatUnitLabel(unit);
  if (!label || label === "total") {
    return `${formatNumeric(value)} lei`;
  }

  return `${formatNumeric(value)} lei/${label}`;
}

export function formatTarget(
  value: number | null | undefined,
  unit: string | null | undefined,
): string {
  if (value === null || value === undefined) return "-";

  const label = formatUnitLabel(unit);
  if (!label || label === "total") {
    return `${formatNumeric(value)} lei`;
  }

  return `${formatNumeric(value)} lei/${label}`;
}

export function formatCapturedAt(value: string | null | undefined): string {
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

export function statusBadgeClass(status: string): string {
  if (status === "best_buy") {
    return "border-emerald-400/20 bg-emerald-500/10 text-emerald-300";
  }

  if (status === "high_price") {
    return "border-rose-400/20 bg-rose-500/10 text-rose-300";
  }

  return "border-amber-400/20 bg-amber-500/10 text-amber-300";
}

export function cardRowClass(hasPromo: boolean): string {
  return hasPromo
    ? "bg-gradient-to-r from-fuchsia-500/10 via-fuchsia-500/5 to-transparent"
    : "";
}

export function hasPromo(item: {
  latest_promo_label?: string | null;
  latest_discount_percent?: number | null;
  latest_promo_kind?: string | null;
  latest_availability?: string | null;
}) {
  const availability = item.latest_availability?.trim().toLowerCase() ?? "";
  const isUnavailable =
    availability === "out_of_stock" ||
    availability.includes("indispon") ||
    availability.includes("unavailable");
  if (isUnavailable) {
    return false;
  }

  const hasPromoLabel = !!item.latest_promo_label?.trim();
  const hasDiscount =
    item.latest_discount_percent !== null &&
    item.latest_discount_percent !== undefined &&
    item.latest_discount_percent > 0;

  const isBundlePromo = item.latest_promo_kind === "bundle";

  return hasPromoLabel || hasDiscount || isBundlePromo;
}

export function getPromoBadgeLabel(item: {
  latest_promo_kind?: string | null;
}) {
  if (item.latest_promo_kind === "bundle") {
    return "PROMO pachet";
  }

  return "PROMO";
}

export function getComparableDelta(item: WatchlistDetailedItem): number | null {
  if (
    item.target_price === null ||
    item.target_price === undefined ||
    item.latest_comparison_price === null ||
    item.latest_comparison_price === undefined
  ) {
    return null;
  }

  const targetLabel = formatUnitLabel(item.target_unit);
  const comparisonLabel = formatUnitLabel(item.latest_comparison_unit);

  if (targetLabel && comparisonLabel && targetLabel !== comparisonLabel) {
    return null;
  }

  return item.latest_comparison_price - item.target_price;
}

export function getDeltaTone(delta: number | null): "good" | "neutral" | "warn" {
  if (delta === null) return "neutral";
  if (delta <= 0) return "good";
  return "warn";
}

export function getDeltaText(item: WatchlistDetailedItem): string {
  const delta = getComparableDelta(item);

  if (delta === null) {
    return "Comparație indisponibilă";
  }

  const abs = Math.abs(delta);
  const label =
    formatUnitLabel(item.target_unit) ||
    formatUnitLabel(item.latest_comparison_unit);

  if (delta <= 0) {
    return `${formatNumeric(abs)} lei sub țintă${
      label && label !== "total" ? ` · ${label}` : ""
    }`;
  }

  return `${formatNumeric(abs)} lei peste țintă${
    label && label !== "total" ? ` · ${label}` : ""
  }`;
}

export function deltaBadgeClass(delta: number | null): string {
  const tone = getDeltaTone(delta);

  if (tone === "good") {
    return "border-emerald-400/20 bg-emerald-500/10 text-emerald-200";
  }

  if (tone === "warn") {
    return "border-rose-400/20 bg-rose-500/10 text-rose-200";
  }

  return "border-white/10 bg-white/5 text-white/65";
}

export function filterLinkClass(isActive: boolean): string {
  return isActive
    ? "rounded-full border border-blue-400/20 bg-blue-500/15 px-3 py-1.5 text-xs font-medium text-blue-100 shadow-sm"
    : "rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/65 transition hover:bg-white/10 hover:text-white";
}






