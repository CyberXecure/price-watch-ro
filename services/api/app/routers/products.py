from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session

def _db_enum_from_ui_unit(unit: str | None) -> str | None:
    if unit is None:
        return None

    value = str(unit).strip().lower()
    if not value:
        return None

    mapping = {
        "l": "LEI_PER_L",
        "lei/l": "LEI_PER_L",
        "kg": "LEI_PER_KG",
        "lei/kg": "LEI_PER_KG",
        "buc": "LEI_PER_BUC",
        "lei/buc": "LEI_PER_BUC",
        "total": "TOTAL",
    }

    return mapping.get(value, unit)
from app.models import PriceSnapshot, StoreProduct
from app.schemas import ProductCreate, SnapshotCreate
from app.services.pricing import (
    evaluate_and_create_alerts_for_product,
    pick_comparison,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=StoreProduct)
def create_product(
    payload: ProductCreate,
    session: Session = Depends(get_session),
) -> StoreProduct:
    product = StoreProduct(
        source_code="freshful",
        external_id=payload.external_id,
        url=payload.url,
        title=payload.title,
        brand=payload.brand,
        image_url=payload.image_url,
        category=payload.category,
        package_text=payload.package_text,
        base_measure_type=payload.base_measure_type,
        base_measure_value=payload.base_measure_value,
        base_measure_unit=payload.base_measure_unit,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.get("", response_model=list[StoreProduct])
def list_products(session: Session = Depends(get_session)) -> list[StoreProduct]:
    return session.exec(
        select(StoreProduct).order_by(StoreProduct.created_at.desc())
    ).all()


@router.get("/{product_id}", response_model=StoreProduct)
def get_product(
    product_id: int,
    session: Session = Depends(get_session),
) -> StoreProduct:
    product = session.get(StoreProduct, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{product_id}/history", response_model=list[PriceSnapshot])
def get_product_history(
    product_id: int,
    session: Session = Depends(get_session),
) -> list[PriceSnapshot]:
    product = session.get(StoreProduct, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return session.exec(
        select(PriceSnapshot)
        .where(PriceSnapshot.store_product_id == product_id)
        .order_by(PriceSnapshot.captured_at.desc())
    ).all()


@router.post("/{product_id}/snapshots", response_model=PriceSnapshot)
def add_price_snapshot(
    product_id: int,
    payload: SnapshotCreate,
    session: Session = Depends(get_session),
) -> PriceSnapshot:
    product = session.get(StoreProduct, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    comparison_price, comparison_unit = pick_comparison(
        price_total=payload.price_total,
        unit_price_value=payload.unit_price_value,
        unit_price_unit=_db_enum_from_ui_unit(payload.unit_price_unit),
    )

    snapshot = PriceSnapshot(
        store_product_id=product_id,
        captured_at=payload.captured_at or datetime.utcnow(),
        price_total=payload.price_total,
        currency=payload.currency,
        unit_price_value=payload.unit_price_value,
        unit_price_unit=_db_enum_from_ui_unit(payload.unit_price_unit),
        comparison_price=comparison_price,
        comparison_unit=_db_enum_from_ui_unit(comparison_unit),
        old_price=payload.old_price,
        promo_label=payload.promo_label,
        availability=payload.availability,
    )
    session.add(snapshot)

    product.updated_at = datetime.utcnow()
    session.add(product)

    session.commit()
    session.refresh(snapshot)

    evaluate_and_create_alerts_for_product(
        session=session,
        product=product,
        comparison_price=comparison_price,
        comparison_unit=_db_enum_from_ui_unit(comparison_unit),
    )
    session.commit()

    return snapshot

