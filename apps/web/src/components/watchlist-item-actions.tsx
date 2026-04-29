"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import WatchlistItemActiveToggle from "@/components/watchlist-item-active-toggle";
import { API_BASE_URL, archiveWatchlistItem, getPromoEngineHealth, startPromoEngine } from "@/lib/api";

type Props = {
  watchlistId: number;
  itemId: number;
  productUrl: string;
  isActive: boolean;
  onChanged?: () => Promise<void> | void;
};

function normalizeRefreshError(message: string): string {
  const text = message.toLowerCase();

  if (
    text.includes("connect_econnrefused") ||
    text.includes("connect econnrefused") ||
    text.includes("connect_over_cdp") ||
    text.includes("browsertype.connect_over_cdp") ||
    text.includes("websocket") ||
    text.includes("browser") ||
    text.includes("rendered")
  ) {
    return "Motorul pentru actualizarea promo nu este disponibil acum. Încearcă din nou după pornirea completă a aplicației.";
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
  onChanged,
}: Props) {
  const router = useRouter();

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isRefreshingRendered, setIsRefreshingRendered] = useState(false);
  const [isArchiving, setIsArchiving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [promoEngineAvailable, setPromoEngineAvailable] = useState<boolean>(false);
  const [promoEngineDetail, setPromoEngineDetail] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadPromoEngineHealth() {
      try {
        const health = await getPromoEngineHealth();
        if (cancelled) return;

        setPromoEngineAvailable(health.status === "ok");
        setPromoEngineDetail(health.detail ?? null);
      } catch (err) {
        if (cancelled) return;

        setPromoEngineAvailable(false);
        setPromoEngineDetail(
          err instanceof Error ? err.message : "Motor promo indisponibil",
        );
      }
    }

    loadPromoEngineHealth();

    return () => {
      cancelled = true;
    };
  }, []);

  async function runRefresh(mode: "static" | "rendered") {
    try {
      setError(null);

      if (mode === "static") {
        setIsRefreshing(true);
      } else {
        setIsRefreshingRendered(true);
      }

      if (mode === "rendered") {
        let health = await getPromoEngineHealth();

        if (health.status !== "ok") {
          await startPromoEngine();
          health = await getPromoEngineHealth();
        }

        setPromoEngineAvailable(health.status === "ok");
        setPromoEngineDetail(health.detail ?? null);

        if (health.status !== "ok") {
          throw new Error(
            health.detail ||
              "Motorul pentru actualizarea promo nu este disponibil acum.",
          );
        }
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
        }

        throw new Error(detail);
      }

      if (onChanged) {
        await onChanged();
      } else {
        router.refresh();
      }
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
      if (onChanged) {
        await onChanged();
      } else {
        router.refresh();
      }
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

      {!promoEngineAvailable && promoEngineDetail ? (
        <div className="rounded-2xl border border-amber-400/20 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
          {promoEngineDetail}
        </div>
      ) : null}
    </div>
  );
}
