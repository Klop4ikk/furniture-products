from pydantic import BaseModel

class ProductItem(BaseModel):
    id: int
    product_name: str
    article: int                # было str
    product_type: str
    min_cost_partner: float     # было str
    main_material: str
    manufacturing_time: int

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    product_name: str
    article: int
    product_type: str
    min_cost_partner: float
    main_material: str

class ProductUpdate(BaseModel):
    product_name: str | None = None
    article: int | None = None
    product_type: str | None = None
    min_cost_partner: float | None = None
    main_material: str | None = None
