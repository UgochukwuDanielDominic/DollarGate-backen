import httpx
import random
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Order, OrderItem, Product, User, OrderStatus
from app.schemas.schemas import OrderCreate, OrderResponse, PaymentVerifyRequest
from app.middleware.auth import get_current_user
from app.config import settings

router = APIRouter()


def generate_order_ref() -> str:
    suffix = ''.join(random.choices(string.digits, k=6))
    return f"DG-{suffix}"


# ── PLACE ORDER ────────────────────────────────────────────────────────────

@router.post("", response_model=OrderResponse, status_code=201)
def place_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    subtotal = 0.0
    order_items = []

    for item in payload.items:
        product = db.query(Product).filter(
            Product.id == item.product_id, Product.is_active == True
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}. Available: {product.stock}"
            )

        line_total = product.price * item.quantity
        subtotal += line_total
        order_items.append({
            "product": product,
            "quantity": item.quantity,
            "unit_price": product.price,
            "subtotal": line_total
        })

    shipping_fee = 0.0  # Free shipping!
    total = subtotal - 0.0 + shipping_fee  # discount logic can go here

    # Create order
    order = Order(
        order_ref        = generate_order_ref(),
        user_id          = current_user.id,
        subtotal         = subtotal,
        shipping_fee     = shipping_fee,
        discount         = 0.0,
        total            = total,
        currency         = payload.currency,
        shipping_name    = payload.shipping.full_name,
        shipping_phone   = payload.shipping.phone,
        shipping_address = payload.shipping.address,
        shipping_city    = payload.shipping.city,
        shipping_state   = payload.shipping.state,
        notes            = payload.notes,
    )
    db.add(order)
    db.flush()  # get order.id without committing

    # Create order items & deduct stock
    for item_data in order_items:
        db.add(OrderItem(
            order_id     = order.id,
            product_id   = item_data["product"].id,
            product_name = item_data["product"].name,
            unit_price   = item_data["unit_price"],
            quantity     = item_data["quantity"],
            subtotal     = item_data["subtotal"],
        ))
        item_data["product"].stock -= item_data["quantity"]

    db.commit()
    db.refresh(order)
    return order


# ── GET ORDER ──────────────────────────────────────────────────────────────

@router.get("/{order_ref}", response_model=OrderResponse)
def get_order(
    order_ref: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.order_ref == order_ref).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return order


# ── VERIFY PAYMENT (PAYSTACK) ──────────────────────────────────────────────

@router.post("/verify-payment", response_model=OrderResponse)
async def verify_payment(
    payload: PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.order_ref == payload.order_ref).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if order.payment_status == "paid":
        return order  # already verified

    # Verify with Paystack
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.paystack.co/transaction/verify/{payload.payment_ref}",
            headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
        )

    data = response.json()
    if not data.get("status") or data["data"]["status"] != "success":
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # Confirm the amount matches
    paid_amount = data["data"]["amount"] / 100  # Paystack uses kobo
    if paid_amount < order.total:
        raise HTTPException(status_code=400, detail="Payment amount mismatch")

    order.payment_ref    = payload.payment_ref
    order.payment_status = "paid"
    order.payment_method = payload.payment_method
    order.status         = OrderStatus.confirmed
    db.commit()
    db.refresh(order)
    return order


# ── CANCEL ORDER ───────────────────────────────────────────────────────────

@router.post("/{order_ref}/cancel")
def cancel_order(
    order_ref: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.order_ref == order_ref).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if order.status not in [OrderStatus.pending, OrderStatus.confirmed]:
        raise HTTPException(status_code=400, detail="Order cannot be cancelled at this stage")

    # Restore stock
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity

    order.status = OrderStatus.cancelled
    db.commit()
    return {"message": "Order cancelled successfully"}
