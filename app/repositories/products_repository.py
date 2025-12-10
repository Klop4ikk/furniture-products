from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import Session
from app.db import Base

# Products_import
class ProductsImport(Base):
    __tablename__ = "Products_import"

    id = Column(Integer, primary_key=True, index=True)
    product_type = Column("Product type", String)
    product_name = Column("Product name", String, index=True)
    article = Column("Article", String)
    min_cost_partner = Column("Minimum cost for a partner", String)
    main_material = Column("Main material", String)

# Workshops_import
class WorkshopsImport(Base):
    __tablename__ = "Workshops_import"

    id = Column(Integer, primary_key=True, index=True)
    workshop_name = Column("Workshop name", String)
    workshop_type = Column("Workshop type", String)
    people_count = Column("Number of people for production", String)

# Product_workshops_import
class ProductWorkshopsImport(Base):
    __tablename__ = "Product_workshops_import"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column("Product name", String, index=True)
    workshop_name = Column("Workshop name", String)
    production_time_h = Column("Production time, h", Float)

# Material_type_import
class MaterialTypeImport(Base):
    __tablename__ = "Material_type_import"

    id = Column(Integer, primary_key=True, index=True)
    type_material = Column("Type material", String)
    raw_loss_pct = Column("Percentage of raw material losses", String)

# Product_type_import
class ProductTypeImport(Base):
    __tablename__ = "Product_type_import"

    id = Column(Integer, primary_key=True, index=True)
    product_type = Column("Product type", String)
    type_coefficient = Column("Product type coefficient", String)


def get_all_products(db: Session):
    return db.query(ProductsImport).all()

def get_workshop_times_for_product(db: Session, product_name: str):
    return (
        db.query(ProductWorkshopsImport)
        .filter(ProductWorkshopsImport.product_name == product_name)
        .all()
    )

from app.schemas.product import ProductCreate, ProductUpdate
from app.repositories.products_repository import ProductsImport

def create_product(db: Session, product: ProductCreate):
    new_product = ProductsImport(
        product_name=product.product_name,
        article=product.article,
        product_type=product.product_type,
        min_cost_partner=product.min_cost_partner,
        main_material=product.main_material,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

def update_product(db: Session, product_id: int, product: ProductUpdate):
    db_product = db.query(ProductsImport).filter(ProductsImport.id == product_id).first()
    if not db_product:
        return None
    for field, value in product.dict(exclude_unset=True).items():
        setattr(db_product, field, value)
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int):
    db_product = db.query(ProductsImport).filter(ProductsImport.id == product_id).first()
    if not db_product:
        return None
    db.delete(db_product)
    db.commit()
    return True
