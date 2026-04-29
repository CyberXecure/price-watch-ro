from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.enums import ComparisonUnit, MeasureType, PriceStatus


class WatchlistCreate(SQLModel):
    name: str


class ProductCreate(SQLModel):
    url: str
    title: str
    brand: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    package_text: Optional[str] = None

    base_measure_type: MeasureType = MeasureType.UNKNOWN
    base_measure_value: Optional[float] = None
    base_measure_unit: Optional[str] = None

    external_id: Optional[str] = None


class WatchlistItemCreate(SQLModel):
    store_product_id: int
    target_price: Optional[float] = None
    target_unit: Optional[ComparisonUnit] = None
    notify_best_buy: bool = True
    notify_high_price: bool = True


class SnapshotCreate(SQLModel):
    price_total: float
    currency: str = "RON"

    unit_price_value: Optional[float] = None
    unit_price_unit: Optional[str] = None

    old_price: Optional[float] = None
    promo_label: Optional[str] = None
    discount_percent: Optional[float] = None
    promo_kind: Optional[str] = None
    availability: Optional[str] = None
    captured_at: Optional[datetime] = None


class WatchlistItemRead(SQLModel):
    id: int
    watchlist_id: int
    store_product_id: int

    target_price: Optional[float] = None
    target_unit: Optional[ComparisonUnit] = None

    notify_best_buy: bool
    notify_high_price: bool

    current_status: PriceStatus
    current_status_label: str

    is_active: bool
    created_at: datetime


class AlertEventRead(SQLModel):
    id: int
    watchlist_item_id: int
    store_product_id: int

    triggered_at: datetime

    old_status: PriceStatus
    old_status_label: str

    new_status: PriceStatus
    new_status_label: str

    comparison_price: float
    comparison_unit: ComparisonUnit

    message: str
    is_read: bool

class DashboardSummary(SQLModel):
    total_watchlists: int
    total_products: int
    total_watchlist_items: int

    total_chilipir: int
    total_pret_cinstit: int
    total_rasfat: int

class WatchlistItemDetailedRead(SQLModel):
    watchlist_item_id: int
    watchlist_id: int

    store_product_id: int
    product_title: str
    product_brand: Optional[str] = None
    product_category: Optional[str] = None
    product_url: str
    product_image_url: Optional[str] = None
    package_text: Optional[str] = None

    current_status: PriceStatus
    current_status_label: str

    target_price: Optional[float] = None
    target_unit: Optional[ComparisonUnit] = None

    latest_price_total: Optional[float] = None
    latest_comparison_price: Optional[float] = None
    latest_comparison_unit: Optional[ComparisonUnit] = None
    latest_unit_price_value: Optional[float] = None
    latest_unit_price_unit: Optional[str] = None
    latest_captured_at: Optional[datetime] = None

    notify_best_buy: bool
    notify_high_price: bool
    is_active: bool
    created_at: datetime

class FreshfulImportRequest(SQLModel):
    url: str
    title: str
    brand: str | None = None
    image_url: str | None = None
    category: str | None = None
    package_text: str | None = None

    base_measure_type: str = "unknown"
    base_measure_value: float | None = None
    base_measure_unit: str | None = None

    external_id: str | None = None

    price_total: float
    currency: str = "RON"
    unit_price_value: float | None = None
    unit_price_unit: str | None = None

    old_price: float | None = None
    promo_label: str | None = None
    discount_percent: float | None = None
    promo_kind: str | None = None
    deposit_value: float | None = None
    availability: str | None = None

    watchlist_id: int | None = None
    target_price: float | None = None
    target_unit: ComparisonUnit | None = None
    notify_best_buy: bool = True
    notify_high_price: bool = True


class FreshfulImportResponse(SQLModel):
    product_id: int
    product_title: str
    product_url: str

    snapshot_id: int
    comparison_price: float
    comparison_unit: ComparisonUnit

    watchlist_item_id: Optional[int] = None
    current_status: Optional[PriceStatus] = None
    current_status_label: Optional[str] = None

    message: str

class WatchlistUpdate(SQLModel):
    name: str

class WatchlistItemUpdate(SQLModel):
    target_price: Optional[float] = None
    notify_best_buy: Optional[bool] = None
    notify_high_price: Optional[bool] = None

class WatchlistItemMoveRequest(SQLModel):
    target_watchlist_id: int

class WatchlistWithSummary(SQLModel):
    id: int
    name: str
    created_at: datetime

    total_items: int
    total_chilipir: int
    total_pret_cinstit: int
    total_rasfat: int

class WatchlistSummary(SQLModel):
    watchlist_id: int
    watchlist_name: str

    total_items: int
    total_chilipir: int
    total_pret_cinstit: int
    total_rasfat: int
