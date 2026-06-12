from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app.database import get_db
from app.models.models import Product, Category, Gender
from app.schemas.schemas import (
    ProductCreate, ProductUpdate, ProductResponse,
    ProductListResponse, CategoryCreate, CategoryResponse
)
from app.middleware.auth import get_current_admin

router = APIRouter()


# ── CATEGORIES ─────────────────────────────────────────────────────────────

@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).filter(Category.is_active == True).all()


@router.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin)
):
    if db.query(Category).filter(Category.slug == payload.slug).first():
        raise HTTPException(status_code=400, detail="Category slug already exists")
    cat = Category(**payload.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


# ── PRODUCTS ───────────────────────────────────────────────────────────────

@router.get("", response_model=ProductListResponse)
def list_products(
    page:        int = Query(1, ge=1),
    per_page:    int = Query(12, ge=1, le=100),
    category:    Optional[str]   = None,
    gender:      Optional[Gender] = None,
    min_price:   Optional[float] = None,
    max_price:   Optional[float] = None,
    search:      Optional[str]   = None,
    featured:    Optional[bool]  = None,
    sort_by:     str = Query("created_at", enum=["price", "created_at", "name"]),
    sort_order:  str = Query("desc", enum=["asc", "desc"]),
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.is_active == True)

    # Filters
    if category:
        query = query.join(Category).filter(Category.slug == category)
    if gender:
        query = query.filter(Product.gender == gender)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if featured is not None:
        query = query.filter(Product.is_featured == featured)
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
                Product.brand.ilike(f"%{search}%"),
            )
        )

    # Sorting
    sort_col = getattr(Product, sort_by)
    query = query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())

    total = query.count()
    products = query.offset((page - 1) * per_page).limit(per_page).all()

    return ProductListResponse(
        total=total, page=page, per_page=per_page, products=products
    )


@router.get("/{slug}", response_model=ProductResponse)
def get_product(slug: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(
        Product.slug == slug, Product.is_active == True
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin)
):
    if db.query(Product).filter(Product.slug == payload.slug).first():
        raise HTTPException(status_code=400, detail="Product slug already exists")
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False  # soft delete
    db.commit()
