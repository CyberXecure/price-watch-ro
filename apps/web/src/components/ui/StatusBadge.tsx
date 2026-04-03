import type { PriceStatus } from "@/lib/types";

const styles: Record<PriceStatus, string> = {
  best_buy:
    "border border-emerald-400/20 bg-emerald-500/10 text-emerald-300",
  normal:
    "border border-slate-400/15 bg-slate-500/10 text-slate-200",
  high_price:
    "border border-orange-400/20 bg-orange-500/10 text-orange-300",
};

export function StatusBadge({
  status,
  label,
}: {
  status: PriceStatus;
  label: string;
}) {
  return (
    <span
      className={`inline-flex rounded-full px-3 py-1.5 text-xs font-semibold ${styles[status]}`}
    >
      {label}
    </span>
  );
}