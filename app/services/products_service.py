from typing import List
from sqlalchemy.orm import Session
from app.repositories.products_repository import (
    ProductsImport,
    get_all_products,
    get_workshop_times_for_product,
)
from app.schemas.product import ProductItem

def compute_manufacturing_time(db: Session, product_name: str) -> int:
    times = get_workshop_times_for_product(db, product_name)
    total = sum((t.production_time_h or 0.0) for t in times)
    # целое неотрицательное число
    result = int(round(total))
    return max(0, result)

def list_products_with_time(db: Session) -> List[ProductItem]:
    rows = get_all_products(db)
    items: List[ProductItem] = []
    for r in rows:
        items.append(
            ProductItem(
                id=r.id,
                product_name=r.product_name or "",
                article=r.article or "",
                product_type=r.product_type or "",
                min_cost_partner=r.min_cost_partner or "",
                main_material=r.main_material or "",
                manufacturing_time=compute_manufacturing_time(db, r.product_name or ""),
            )
        )
    return items
