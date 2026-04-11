from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.enums import ComparisonUnit, MeasureType, PriceStatus


class Watchlist(SQLModel, table=True):
    __tablename__ = "watchlist"

    id: Optional[int] = Field(default=None, primary_key=True)

    slug: str = Field(index=True, unique=True, max_length=120)
    name: str = Field(index=True, unique=True, max_length=120)
    icon: Optional[str] = Field(default=None, max_length=80)
    description: Optional[str] = Field(default=None, max_length=500)
    sort_order: int = Field(default=0, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    items: List["WatchlistItem"] = Relationship(back_populates="watchlist")


class StoreProduct(SQLModel, table=True):
    __tablename__ = "storeproduct"

    id: Optional[int] = Field(default=None, primary_key=True)

    source_code: str = Field(index=True, max_length=50)
    external_id: Optional[str] = Field(default=None, index=True, max_length=255)

    url: str = Field(index=True, unique=True, max_length=1000)
    title: str = Field(index=True, max_length=500)

    brand: Optional[str] = Field(default=None, index=True, max_length=255)
    category: Optional[str] = Field(default=None, index=True, max_length=255)
    image_url: Optional[str] = Field(default=None, max_length=1000)
    package_text: Optional[str] = Field(default=None, max_length=255)

    base_measure_type: Optional[MeasureType] = Field(default=None, index=True)
    base_measure_value: Optional[float] = Field(default=None)
    base_measure_unit: Optional[str] = Field(default=None, max_length=50)

    currency: str = Field(default="RON", max_length=10)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    snapshots: List["PriceSnapshot"] = Relationship(back_populates="store_product")
    watchlist_items: List["WatchlistItem"] = Relationship(back_populates="store_product")
    alert_events: List["AlertEvent"] = Relationship(back_populates="store_product")


class PriceSnapshot(SQLModel, table=True):
    __tablename__ = "pricesnapshot"

    id: Optional[int] = Field(default=None, primary_key=True)

    store_product_id: int = Field(foreign_key="storeproduct.id", index=True)

    captured_at: datetime = Field(default_factory=datetime.utcnow, index=True, nullable=False)

    price_total: float = Field(index=True)
    currency: str = Field(default="RON", max_length=10)

    unit_price_value: Optional[float] = Field(default=None)
    unit_price_unit: Optional[str] = Field(default=None, max_length=50)

    comparison_price: Optional[float] = Field(default=None, index=True)
    comparison_unit: Optional[ComparisonUnit] = Field(default=None, index=True)

    old_price: Optional[float] = Field(default=None)
    promo_label: Optional[str] = Field(default=None, max_length=255)
    discount_percent: Optional[float] = Field(default=None)
    deposit_value: Optional[float] = Field(default=None)

    availability: Optional[str] = Field(default=None, max_length=50)

    store_product: Optional["StoreProduct"] = Relationship(back_populates="snapshots")


class WatchlistItem(SQLModel, table=True):
    __tablename__ = "watchlistitem"

    id: Optional[int] = Field(default=None, primary_key=True)

    watchlist_id: int = Field(foreign_key="watchlist.id", index=True)
    store_product_id: int = Field(foreign_key="storeproduct.id", index=True)

    target_price: Optional[float] = Field(default=None)
    target_unit: Optional[ComparisonUnit] = Field(default=None, index=True)

    notify_best_buy: bool = Field(default=True)
    notify_high_price: bool = Field(default=True)

    current_status: Optional[PriceStatus] = Field(default=None, index=True)
    is_active: bool = Field(default=True, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    watchlist: Optional["Watchlist"] = Relationship(back_populates="items")
    store_product: Optional["StoreProduct"] = Relationship(back_populates="watchlist_items")


class AlertEvent(SQLModel, table=True):
    __tablename__ = "alertevent"

    id: Optional[int] = Field(default=None, primary_key=True)

    store_product_id: int = Field(foreign_key="storeproduct.id", index=True)
    watchlist_id: Optional[int] = Field(default=None, foreign_key="watchlist.id", index=True)
    watchlist_item_id: Optional[int] = Field(default=None, foreign_key="watchlistitem.id", index=True)

    event_type: str = Field(index=True, max_length=100)
    message: Optional[str] = Field(default=None, max_length=1000)

    old_status: Optional[PriceStatus] = Field(default=None, index=True)
    new_status: Optional[PriceStatus] = Field(default=None, index=True)

    old_price: Optional[float] = Field(default=None)
    new_price: Optional[float] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True, nullable=False)

    store_product: Optional["StoreProduct"] = Relationship(back_populates="alert_events")