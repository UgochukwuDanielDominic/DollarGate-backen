from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.database import get_db
from app.models.models import User, Product, Order, OrderStatus, UserRole
from app.schemas.schemas import (
    DashboardStats, OrderStatusUpdate, StockUpdate,
    UserResponse, OrderResponse
)
from app.middleware.auth import get_current_admin

router = APIRouter()


# ── DASHBOARD STATS ────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardStats)
def dashboard(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin)
):
    total_orders    = db.query(Order).count()
    total_revenue   = db.query(func.sum(Order.total)).filter(
                          Order.payment_status == "paid"
                      ).scalar() or 0.0
    total_customers = db.query(User).filter(User.role == UserRole.customer).count()
    total_products  = db.query(Product).filter(Product.is_active == True).count()
    low_stock_count = db.query(Product).filter(
                          Product.stock <= Product.low_stock_threshold,
                          Product.is_active == True
                      ).count()
    pending_orders  = db.query(Order).filter(
                          Order.status == OrderStatus.pending
                      ).count()

    return DashboardStats(
        total_orders    = total_orders,
        total_revenue   = total_revenue,
        total_customers = total_customers,
        total_products  = total_products,
        low_stock_count = low_stock_count,
        pending_orders  = pending_orders,
    )


# ── ORDERS MANAGEMENT ──────────────────────────────────────────────────────

@router.get("/orders")
def list_all_orders(
    page:    int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status:  Optional[OrderStatus] = None,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin)
):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    total = query.count()
    orders = query.order_by(Order.created_at.desc())\
                  .offset((page - 1) * per_page).limit(per_page).all()
    return {"total": total, "page": page, "per_page": per_page, "orders": orders}


@router.put("/orders/{order_ref}/status")
def update_order_status(
    order_ref: str,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin)
):
    order = db.query(Order).filter(Order.order_ref == order_ref).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = payload.status
    db.commit()
    return {"message": f"Order status updated to {payload.status}"}


# ── USERS MANAGEMENT ───────────────────────────────────────────────────────

@router.get("/users")
def list_users(
    page:     int = Query(1, ge=1),
    per_page: int = Query(20),
    search:   Optional[str] = None,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin)
):
    query = db.query(User)
    if search:
        query = query.filter(
            User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%")
        )
    total = query.count()
    users = query.offset((page - 1) * per_page).limit(per_page).all()
    return {"total": total, "page": page, "per_page": per_page, "users": users}


@router.put("/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user.is_active = not user.is_active
    db.commit()
    status = "activated" if user.is_active else "deactivated"
    return {"message": f"User {status} successfully"}


@router.put("/users/{user_id}/make-admin")
def make_admin(
    user_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = UserRole.admin
    db.commit()
    return {"message": f"{user.full_name} is now an admin"}


# ── INVENTORY MANAGEMENT ───────────────────────────────────────────────────

@router.get("/inventory")
def low_stock_report(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin)
):
    products = db.query(Product).filter(
        Product.stock <= Product.low_stock_threshold,
        Product.is_active == True
    ).order_by(Product.stock.asc()).all()
    return {"low_stock_products": products, "count": len(products)}


@router.put("/inventory/{product_id}/stock")
def update_stock(
    product_id: int,
    payload: StockUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.stock = payload.stock
    db.commit()
    return {"message": f"Stock updated to {payload.stock}", "product": product.name}


# ── REVENUE REPORT ─────────────────────────────────────────────────────────

@router.get("/reports/revenue")
def revenue_report(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin)
):
    from sqlalchemy import extract
    from datetime import datetime

    current_year = datetime.utcnow().year
    monthly = db.query(
        extract("month", Order.created_at).label("month"),
        func.sum(Order.total).label("revenue"),
        func.count(Order.id).label("orders")
    ).filter(
        Order.payment_status == "paid",
        extract("year", Order.created_at) == current_year
    ).group_by("month").order_by("month").all()

    return {
        "year": current_year,
        "monthly_revenue": [
            {"month": int(r.month), "revenue": float(r.revenue or 0), "orders": int(r.orders)}
            for r in monthly
        ]
    }
