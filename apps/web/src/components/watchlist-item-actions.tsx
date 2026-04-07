"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import WatchlistItemActiveToggle from "@/components/watchlist-item-active-toggle";
import { archiveWatchlistItem } from "@/lib/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE?.trim() ||
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim() ||
  "http://127.0.0.1:8000";

type Props = {
  watchlistId: number;
  itemId: number;
  productUrl: string;
  isActive: boolean;
};

function normalizeRefreshError(message: string): string {
  const text = message.toLowerCase();

  if (
    text.includes("9222") ||
    text.includes("connect_econnrefused") ||
    text.includes("connect econnrefused") ||
    text.includes("connect_over_cdp") ||
    text.includes("browsertype.connect_over_cdp") ||
    text.includes("websocket")
  ) {
    return "Motorul pentru actualizarea promo nu este disponibil acum. Pornește sesiunea locală completă și încearcă din nou.";
  }

  if (text.includes("missing price_total")) {
    return "Actualizarea promo nu a putut extrage încă prețul produsului.";
  }

  return message;
}

export default function WatchlistItemActions({
  watchlistId,
  itemId,
  productUrl,
  isActive,
}: Props) {
  const router = useRouter();

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isRefreshingRendered, setIsRefreshingRendered] = useState(false);
  const [isArchiving, setIsArchiving] = useState(false);
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
        } catch {
          // păstrăm mesajul fallback
        }

        throw new Error(detail);
      }

      router.refresh();
    } catch (err) {
      const rawMessage =
        err instanceof Error ? err.message : "Actualizarea a eșuat";

      setError(
        mode === "rendered" ? normalizeRefreshError(rawMessage) : rawMessage,
      );
    } finally {
      setIsRefreshing(false);
      setIsRefreshingRendered(false);
    }
  }

  async function handleArchive() {
    const confirmed = window.confirm("Ascunzi acest produs din lista activă?");
    if (!confirmed) return;

    try {
      setError(null);
      setIsArchiving(true);
      await archiveWatchlistItem(watchlistId, itemId);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Acțiunea a eșuat");
    } finally {
      setIsArchiving(false);
    }
  }

  const isBusy = isRefreshing || isRefreshingRendered || isArchiving;

  return (
    <div className="mt-3 space-y-3">
      <div className="text-xs font-semibold uppercase tracking-wide text-white/45">
        Acțiuni
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => runRefresh("static")}
          disabled={isBusy}
          className="rounded-full border border-blue-400/20 bg-blue-500/10 px-3 py-1.5 text-xs font-medium text-blue-200 transition hover:bg-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isRefreshing ? "Actualizez..." : "Actualizează"}
        </button>

        <button
          type="button"
          onClick={() => runRefresh("rendered")}
          disabled={isBusy}
          className="rounded-full border border-fuchsia-400/20 bg-fuchsia-500/10 px-3 py-1.5 text-xs font-medium text-fuchsia-200 transition hover:bg-fuchsia-500/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isRefreshingRendered ? "Actualizez promo..." : "Actualizează promo"}
        </button>

        <a
          href={productUrl}
          target="_blank"
          rel="noreferrer"
          className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/85 transition hover:bg-white/10"
        >
          Deschide
        </a>

        <WatchlistItemActiveToggle
          watchlistId={watchlistId}
          itemId={itemId}
          isActive={isActive}
        />

        {isActive ? (
          <button
            type="button"
            onClick={handleArchive}
            disabled={isBusy}
            className="rounded-full border border-amber-400/20 bg-amber-500/10 px-3 py-1.5 text-xs font-medium text-amber-200 transition hover:bg-amber-500/20 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isArchiving ? "Ascund..." : "Ascunde"}
          </button>
        ) : null}
      </div>

      {error ? (
        <div className="rounded-2xl border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-xs text-rose-100">
          {error}
        </div>
      ) : null}
    </div>
  );
}