const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "http://127.0.0.1:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
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
  latest_deposit_value?: number | null;
  latest_captured_at: string | null;
  notify_best_buy: boolean;
  notify_high_price: boolean;
  is_active: boolean;
  created_at: string;
};

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