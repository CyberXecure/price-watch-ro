export type PriceStatus = "best_buy" | "normal" | "high_price";

export type ComparisonUnit = "lei/l" | "lei/kg" | "lei/buc" | "total";

export interface Watchlist {
  id: number;
  name: string;
  created_at: string;
}

export interface WatchlistSummary {
  watchlist_id: number;
  watchlist_name: string;
  total_items: number;
  total_chilipir: number;
  total_pret_cinstit: number;
  total_rasfat: number;
}

export interface WatchlistItemDetailed {
  watchlist_item_id: number;
  watchlist_id: number;
  store_product_id: number;
  product_title: string;
  product_brand?: string | null;
  product_category?: string | null;
  product_url: string;
  product_image_url?: string | null;
  package_text?: string | null;
  current_status: PriceStatus;
  current_status_label: string;
  target_price?: number | null;
  target_unit?: ComparisonUnit | null;
  latest_price_total?: number | null;
  latest_comparison_price?: number | null;
  latest_comparison_unit?: ComparisonUnit | null;
  latest_unit_price_value?: number | null;
  latest_unit_price_unit?: string | null;
  latest_captured_at?: string | null;
  notify_best_buy: boolean;
  notify_high_price: boolean;
  is_active: boolean;
  created_at: string;
}

export interface DashboardSummary {
  total_watchlists: number;
  total_products: number;
  total_watchlist_items: number;
  total_chilipir: number;
  total_pret_cinstit: number;
  total_rasfat: number;
}