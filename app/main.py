from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.products_service import list_products_with_time

app = FastAPI(title="Продукция компании")

@app.get("/api/products")
def get_products(db: Session = Depends(get_db)):
    return list_products_with_time(db)

@app.get("/")
def root():
    return {"message": "Модуль продукции компании работает"}
from fastapi import HTTPException
from app.schemas.product import ProductCreate, ProductUpdate
from app.repositories.products_repository import create_product, update_product, delete_product

@app.post("/api/products")
def add_product(product: ProductCreate, db: Session = Depends(get_db)):
    return create_product(db, product)

@app.put("/api/products/{product_id}")
def edit_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    updated = update_product(db, product_id, product)
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated

@app.delete("/api/products/{product_id}")
def remove_product(product_id: int, db: Session = Depends(get_db)):
    deleted = delete_product(db, product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}
