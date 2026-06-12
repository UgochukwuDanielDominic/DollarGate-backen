from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import UserResponse, UserUpdateRequest, ChangePasswordRequest
from app.middleware.auth import get_current_user, hash_password, verify_password

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_profile(
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/me/password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@router.get("/me/orders")
def get_my_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.models import Order
    orders = db.query(Order).filter(Order.user_id == current_user.id)\
                            .order_by(Order.created_at.desc()).all()
    return orders


@router.get("/me/wishlist")
def get_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.models import Wishlist
    return db.query(Wishlist).filter(Wishlist.user_id == current_user.id).all()


@router.post("/me/wishlist/{product_id}")
def toggle_wishlist(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.models import Wishlist, Product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.product_id == product_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"message": "Removed from wishlist", "wishlisted": False}
    else:
        db.add(Wishlist(user_id=current_user.id, product_id=product_id))
        db.commit()
        return {"message": "Added to wishlist", "wishlisted": True}
