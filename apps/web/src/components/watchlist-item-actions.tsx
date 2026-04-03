"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import WatchlistItemActiveToggle from "@/components/watchlist-item-active-toggle";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "http://127.0.0.1:8000";

type Props = {
  watchlistId: number;
  itemId: number;
  productUrl: string;
  isActive: boolean;
};

export default function WatchlistItemActions({
  watchlistId,
  itemId,
  productUrl,
  isActive,
}: Props) {
  const router = useRouter();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isRefreshingRendered, setIsRefreshingRendered] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runRefresh(mode: "static" | "rendered") {
    try {
      setError(null);

      if (mode === "static") {
        setIsRefreshing(true);
      } else {
        setIsRefreshingRendered(true);
      }

      const endpoint =
        mode === "static"
          ? `${API_BASE_URL}/watchlists/${watchlistId}/items/${itemId}/refresh`
          : `${API_BASE_URL}/watchlists/${watchlistId}/items/${itemId}/refresh-rendered`;

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        let detail = "Actualizarea a eșuat";
        try {
          const data = await response.json();
          detail = data?.detail || detail;
        } catch {}
        throw new Error(detail);
      }

      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Actualizarea a eșuat");
    } finally {
      setIsRefreshing(false);
      setIsRefreshingRendered(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
        Acțiuni
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => runRefresh("static")}
          disabled={isRefreshing || isRefreshingRendered}
          className="rounded-full border border-blue-400/20 bg-blue-500/10 px-3 py-1.5 text-xs font-medium text-blue-200 transition hover:bg-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isRefreshing ? "Actualizez..." : "Actualizează"}
        </button>

        <button
          type="button"
          onClick={() => runRefresh("rendered")}
          disabled={isRefreshing || isRefreshingRendered}
          className="rounded-full border border-fuchsia-400/20 bg-fuchsia-500/10 px-3 py-1.5 text-xs font-medium text-fuchsia-200 transition hover:bg-fuchsia-500/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isRefreshingRendered ? "Actualizez promo..." : "Actualizează promo"}
        </button>

        <a
          href={productUrl}
          target="_blank"
          rel="noreferrer"
          className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-white/10"
        >
          Deschide
        </a>
      </div>

      <div className="text-[11px] leading-5 text-slate-500">
        Actualizarea promo necesită Chrome pornit cu remote debugging pe portul 9222.
      </div>

      <WatchlistItemActiveToggle
        watchlistId={watchlistId}
        itemId={itemId}
        isActive={isActive}
      />

      {error ? <div className="text-xs text-rose-300">{error}</div> : null}
    </div>
  );
}