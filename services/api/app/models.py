from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.enums import ComparisonUnit, MeasureType, PriceStatus


class Watchlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StoreProduct(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_code: str = Field(default="freshful", index=True)
    external_id: Optional[str] = Field(default=None, index=True)

    url: str = Field(index=True)
    title: str = Field(index=True)
    brand: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = Field(default=None, index=True)
    package_text: Optional[str] = None

    base_measure_type: MeasureType = Field(default=MeasureType.UNKNOWN)
    base_measure_value: Optional[float] = None
    base_measure_unit: Optional[str] = None

    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WatchlistItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    watchlist_id: int = Field(foreign_key="watchlist.id", index=True)
    store_product_id: int = Field(foreign_key="storeproduct.id", index=True)

    target_price: Optional[float] = None
    target_unit: Optional[ComparisonUnit] = None

    notify_best_buy: bool = Field(default=True)
    notify_high_price: bool = Field(default=True)

    current_status: PriceStatus = Field(default=PriceStatus.NORMAL)

    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PriceSnapshot(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    store_product_id: int = Field(foreign_key="storeproduct.id", index=True)
    captured_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    price_total: float
    currency: str = "RON"

    unit_price_value: float | None = None
    unit_price_unit: str | None = None

    comparison_price: float
    comparison_unit: ComparisonUnit

    old_price: float | None = None
    promo_label: str | None = None
    discount_percent: float | None = None
    deposit_value: float | None = None
    availability: str | None = None


class AlertEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    watchlist_item_id: int = Field(foreign_key="watchlistitem.id", index=True)
    store_product_id: int = Field(foreign_key="storeproduct.id", index=True)

    triggered_at: datetime = Field(default_factory=datetime.utcnow)

    old_status: PriceStatus
    new_status: PriceStatus

    comparison_price: float
    comparison_unit: ComparisonUnit

    message: str
    is_read: bool = Field(default=False)
