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


def seed_default_watchlists(session: Session) -> None:
    from app.models import Watchlist

    default_names = [
        "Săptămânal",
        "Bebeluș",
        "Casă",
        "Electronice",
    ]

    existing_names = set(session.exec(select(Watchlist.name)).all())

    for name in default_names:
        if name not in existing_names:
            session.add(Watchlist(name=name))

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