from collections.abc import Generator
from datetime import datetime, timedelta

from sqlmodel import Session, SQLModel, create_engine, delete, select

from app.config import DATABASE_URL
from app.enums import ComparisonUnit, MeasureType, PriceStatus

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

DEFAULT_WATCHLISTS = [
    {
        "slug": "saptamanal",
        "name": "Săptămânal",
        "icon": "calendar",
        "description": "Produsele cumpărate cel mai des.",
        "sort_order": 1,
    },
    {
        "slug": "la-10-zile",
        "name": "La 10 zile",
        "icon": "refresh-cw",
        "description": "Reaprovizionare periodică pentru casă.",
        "sort_order": 2,
    },
    {
        "slug": "lunar",
        "name": "Lunar",
        "icon": "package",
        "description": "Produse cumpărate mai rar, dar constant.",
        "sort_order": 3,
    },
    {
        "slug": "casa",
        "name": "Casă",
        "icon": "home",
        "description": "Esențiale pentru gospodărie și consum zilnic.",
        "sort_order": 4,
    },
    {
        "slug": "curatenie",
        "name": "Curățenie",
        "icon": "sparkles",
        "description": "Detergenți, soluții și consumabile de curățenie.",
        "sort_order": 5,
    },
    {
        "slug": "bebelus",
        "name": "Bebeluș",
        "icon": "baby",
        "description": "Produse dedicate celor mici.",
        "sort_order": 6,
    },
    {
        "slug": "oferte",
        "name": "Oferte",
        "icon": "tag",
        "description": "Produse urmărite pentru promoții și reduceri.",
        "sort_order": 7,
    },
    {
        "slug": "chilipiruri",
        "name": "Chilipiruri",
        "icon": "badge-percent",
        "description": "Cele mai bune prețuri și cumpărături inspirate.",
        "sort_order": 8,
    },
]


def _apply_watchlist_fields(watchlist, item: dict) -> None:
    """
    Populează câmpurile existente pe modelul Watchlist.
    Funcționează și dacă modelul are doar `name`.
    """
    if hasattr(watchlist, "name"):
        watchlist.name = item["name"]

    if hasattr(watchlist, "slug"):
        watchlist.slug = item["slug"]

    if hasattr(watchlist, "icon"):
        watchlist.icon = item["icon"]

    if hasattr(watchlist, "description"):
        watchlist.description = item["description"]

    if hasattr(watchlist, "sort_order"):
        watchlist.sort_order = item["sort_order"]


def _build_watchlist_payload(Watchlist, item: dict) -> dict:
    """
    Construiește payload-ul doar cu câmpurile suportate de model.
    """
    payload = {}

    if hasattr(Watchlist, "name"):
        payload["name"] = item["name"]

    if hasattr(Watchlist, "slug"):
        payload["slug"] = item["slug"]

    if hasattr(Watchlist, "icon"):
        payload["icon"] = item["icon"]

    if hasattr(Watchlist, "description"):
        payload["description"] = item["description"]

    if hasattr(Watchlist, "sort_order"):
        payload["sort_order"] = item["sort_order"]

    return payload


def seed_default_watchlists(session: Session) -> None:
    from app.models import Watchlist

    all_watchlists = session.exec(select(Watchlist)).all()

    by_name = {}
    by_slug = {}

    for watchlist in all_watchlists:
        name = getattr(watchlist, "name", None)
        slug = getattr(watchlist, "slug", None)

        if name:
            by_name[name] = watchlist
        if slug:
            by_slug[slug] = watchlist

    for item in DEFAULT_WATCHLISTS:
        existing = by_slug.get(item["slug"]) or by_name.get(item["name"])

        if existing:
            _apply_watchlist_fields(existing, item)
        else:
            payload = _build_watchlist_payload(Watchlist, item)
            session.add(Watchlist(**payload))

    session.commit()


def seed_demo_product(session: Session) -> None:
    from app.models import PriceSnapshot, StoreProduct, Watchlist, WatchlistItem

    existing_product = session.exec(
        select(StoreProduct).where(
            StoreProduct.url == "https://www.freshful.ro/p/demo-lapte-1l"
        )
    ).first()

    if existing_product:
        return

    product = StoreProduct(
        source_code="freshful",
        external_id="demo-lapte-1l",
        url="https://www.freshful.ro/p/demo-lapte-1l",
        title="Lapte 1L Demo",
        brand="Chilipir Demo",
        category="Lactate",
        package_text="1 L",
        base_measure_type=MeasureType.VOLUME,
        base_measure_value=1.0,
        base_measure_unit="l",
    )
    session.add(product)
    session.commit()
    session.refresh(product)

    snapshots = [
        PriceSnapshot(
            store_product_id=product.id,
            captured_at=datetime.utcnow() - timedelta(days=4),
            price_total=9.99,
            currency="RON",
            unit_price_value=9.99,
            unit_price_unit="l",
            comparison_price=9.99,
            comparison_unit=ComparisonUnit.LEI_PER_L,
            old_price=10.49,
            promo_label=None,
            availability="in_stock",
        ),
        PriceSnapshot(
            store_product_id=product.id,
            captured_at=datetime.utcnow() - timedelta(days=3),
            price_total=9.49,
            currency="RON",
            unit_price_value=9.49,
            unit_price_unit="l",
            comparison_price=9.49,
            comparison_unit=ComparisonUnit.LEI_PER_L,
            old_price=9.99,
            promo_label=None,
            availability="in_stock",
        ),
        PriceSnapshot(
            store_product_id=product.id,
            captured_at=datetime.utcnow() - timedelta(days=2),
            price_total=8.99,
            currency="RON",
            unit_price_value=8.99,
            unit_price_unit="l",
            comparison_price=8.99,
            comparison_unit=ComparisonUnit.LEI_PER_L,
            old_price=9.49,
            promo_label="Promo demo",
            availability="in_stock",
        ),
        PriceSnapshot(
            store_product_id=product.id,
            captured_at=datetime.utcnow() - timedelta(days=1),
            price_total=8.79,
            currency="RON",
            unit_price_value=8.79,
            unit_price_unit="l",
            comparison_price=8.79,
            comparison_unit=ComparisonUnit.LEI_PER_L,
            old_price=8.99,
            promo_label="Promo demo",
            availability="in_stock",
        ),
        PriceSnapshot(
            store_product_id=product.id,
            captured_at=datetime.utcnow(),
            price_total=8.29,
            currency="RON",
            unit_price_value=8.29,
            unit_price_unit="l",
            comparison_price=8.29,
            comparison_unit=ComparisonUnit.LEI_PER_L,
            old_price=8.79,
            promo_label="Promo demo",
            availability="in_stock",
        ),
    ]

    for snapshot in snapshots:
        session.add(snapshot)

    session.commit()

    weekly_watchlist = session.exec(
        select(Watchlist).where(Watchlist.name == "Săptămânal")
    ).first()

    if not weekly_watchlist:
        return

    existing_item = session.exec(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == weekly_watchlist.id,
            WatchlistItem.store_product_id == product.id,
        )
    ).first()

    if existing_item:
        return

    watchlist_item = WatchlistItem(
        watchlist_id=weekly_watchlist.id,
        store_product_id=product.id,
        target_price=8.50,
        target_unit=ComparisonUnit.LEI_PER_L,
        notify_best_buy=True,
        notify_high_price=True,
        current_status=PriceStatus.BEST_BUY,
    )
    session.add(watchlist_item)
    session.commit()


def reset_demo_data() -> None:
    from app.models import AlertEvent, PriceSnapshot, StoreProduct, Watchlist, WatchlistItem

    with Session(engine) as session:
        session.exec(delete(AlertEvent))
        session.exec(delete(PriceSnapshot))
        session.exec(delete(WatchlistItem))
        session.exec(delete(StoreProduct))
        session.exec(delete(Watchlist))
        session.commit()

        seed_default_watchlists(session)
        seed_demo_product(session)


def init_db() -> None:
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        seed_default_watchlists(session)
        seed_demo_product(session)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session