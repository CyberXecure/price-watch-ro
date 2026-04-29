export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE?.trim() || "http://127.0.0.1:18400";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const method = (init?.method || "GET").toUpperCase();
  const extraHeaders =
    method === "GET"
      ? { ...(init?.headers || {}) }
      : {
          "Content-Type": "application/json",
          ...(init?.headers || {}),
        };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: extraHeaders,
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = "Request failed";

    try {
      const data = await response.json();
      detail = data?.detail || data?.message || detail;
    } catch {
      try {
        detail = await response.text();
      } catch {
        detail = "Request failed";
      }
    }

    throw new Error(detail);
  }

  return response.json();
}

export async function waitForApiReady(
  attempts: number = 12,
  delayMs: number = 500,
): Promise<void> {
  let lastError: unknown = null;

  for (let i = 0; i < attempts; i += 1) {
    try {
      await getApiHealth();
      return;
    } catch (error) {
      lastError = error;
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }

  throw lastError instanceof Error ? lastError : new Error("API not ready");
}

export type DashboardSummary = {
  total_watchlists: number;
  total_products: number;
  total_watchlist_items: number;
  total_chilipir: number;
  total_pret_cinstit: number;
  total_rasfat: number;
};

export type WatchlistSummary = {
  id: number;
  name: string;
  created_at: string;
  total_items: number;
  total_chilipir: number;
  total_pret_cinstit: number;
  total_rasfat: number;
};

export type Watchlist = {
  id: number;
  name: string;
  created_at: string;
};

export type WatchlistDetailedItem = {
  watchlist_item_id: number;
  watchlist_id: number;
  store_product_id: number;
  product_title: string;
  product_brand: string | null;
  product_category: string | null;
  product_url: string;
  product_image_url: string | null;
  package_text: string | null;
  current_status: string;
  current_status_label: string;
  target_price: number | null;
  target_unit: string | null;
  latest_price_total: number | null;
  latest_comparison_price: number | null;
  latest_comparison_unit: string | null;
  latest_unit_price_value: number | null;
  latest_unit_price_unit: string | null;
  latest_old_price?: number | null;
  latest_promo_label?: string | null;
  latest_discount_percent?: number | null;
  latest_promo_kind?: string | null;
  latest_deposit_value?: number | null;
  latest_availability?: string | null;
  latest_captured_at: string | null;
  notify_best_buy: boolean;
  notify_high_price: boolean;
  is_active: boolean;
  created_at: string;
};

export type BasicHealth = {
  status: "ok" | "error";
};

export type RenderedHealth = {
  status: "ok" | "error";
  target: string;
  http_status: number | null;
  browser: string | null;
  websocket_debugger_url: string | null;
  detail: string | null;
};

export type PromoEngineHealth = {
  status: "ok" | "error";
  mode: "external" | "internal" | "disabled";
  detail: string | null;
  target: string | null;
  websocket_debugger_url: string | null;
  browser: string | null;
  last_checked_at: string | null;
};

export async function getApiHealth(): Promise<BasicHealth> {
  return apiFetch<BasicHealth>("/health");
}

export async function getRenderedHealth(): Promise<RenderedHealth> {
  return apiFetch<RenderedHealth>("/health/rendered");
}

export async function getPromoEngineHealth(): Promise<PromoEngineHealth> {
  return apiFetch<PromoEngineHealth>("/health/promo-engine");
}

export async function startPromoEngine() {
  return apiFetch("/health/promo-engine/start", {
    method: "POST",
  });
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>("/dashboard/summary");
}

export async function getWatchlists(): Promise<Watchlist[]> {
  return apiFetch<Watchlist[]>("/watchlists");
}

export async function getWatchlistsWithSummary(): Promise<WatchlistSummary[]> {
  return apiFetch<WatchlistSummary[]>("/watchlists/with-summary");
}

export async function getWatchlist(watchlistId: number): Promise<Watchlist> {
  return apiFetch<Watchlist>(`/watchlists/${watchlistId}`);
}

export async function getWatchlistDetailedItems(
  watchlistId: number,
): Promise<WatchlistDetailedItem[]> {
  return apiFetch<WatchlistDetailedItem[]>(
    `/watchlists/${watchlistId}/items/detailed`,
  );
}

export async function createWatchlist(name: string): Promise<Watchlist> {
  return apiFetch<Watchlist>("/watchlists", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export async function updateWatchlistItem(
  watchlistId: number,
  itemId: number,
  payload: {
    target_price?: number | null;
    target_unit?: string | null;
    notify_best_buy?: boolean;
    notify_high_price?: boolean;
    is_active?: boolean;
  },
) {
  return apiFetch(`/watchlists/${watchlistId}/items/${itemId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function importFreshfulUrl(payload: {
  watchlistId: number;
  url: string;
  targetPrice?: number | null;
  targetUnit?: string | null;
}) {
  const params = new URLSearchParams({
    url: payload.url,
    watchlist_id: String(payload.watchlistId),
  });

  if (payload.targetPrice !== null && payload.targetPrice !== undefined) {
    params.set("target_price", String(payload.targetPrice));
  }

  if (payload.targetUnit) {
    params.set("target_unit", payload.targetUnit);
  }

  return apiFetch(`/imports/freshful-url-auto?${params.toString()}`, {
    method: "POST",
  });
}

export async function archiveWatchlistItem(
  watchlistId: number,
  itemId: number,
) {
  return updateWatchlistItem(watchlistId, itemId, {
    is_active: false,
  });
}

export async function deleteWatchlist(watchlistId: number) {
  return apiFetch(`/watchlists/${watchlistId}`, {
    method: "DELETE",
  });
}

export async function updateWatchlist(
  watchlistId: number,
  payload: { name: string },
) {
  return apiFetch(`/watchlists/${watchlistId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}







export async function refreshActiveRenderedWatchlist(watchlistId: number) {
  return apiFetch<{
    ok: boolean;
    watchlist_id: number;
    processed: number;
    results: Array<{
      watchlist_item_id: number;
      ok: boolean;
      detail?: string;
      snapshot_id?: number;
      parser_used?: string;
    }>;
  }>(`/watchlists/${watchlistId}/refresh-active-rendered`, {
    method: "POST",
  });
}
