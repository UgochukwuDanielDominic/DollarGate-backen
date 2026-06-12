from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from app.models.models import UserRole, OrderStatus, Gender


# ── AUTH ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:     EmailStr
    full_name: str
    phone:     Optional[str] = None
    password:  str

    @field_validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"

class TokenRefreshRequest(BaseModel):
    refresh_token: str


# ── USER ───────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email:     EmailStr
    full_name: str
    phone:     Optional[str] = None
    address:   Optional[str] = None
    city:      Optional[str] = None
    state:     Optional[str] = None

class UserResponse(UserBase):
    id:         int
    role:       UserRole
    is_active:  bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone:     Optional[str] = None
    address:   Optional[str] = None
    city:      Optional[str] = None
    state:     Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password:     str


# ── CATEGORY ───────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name:        str
    slug:        str
    description: Optional[str] = None
    image_url:   Optional[str] = None

class CategoryResponse(CategoryCreate):
    id:        int
    is_active: bool

    class Config:
        from_attributes = True


# ── PRODUCT ────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    name:        str
    slug:        str
    description: Optional[str] = None
    brand:       Optional[str] = None
    sku:         Optional[str] = None
    price:       float
    old_price:   Optional[float] = None
    cost_price:  Optional[float] = None
    stock:       int = 0
    category_id: Optional[int] = None
    gender:      Gender = Gender.unisex
    images:      List[str] = []
    badge:       Optional[str] = None
    tags:        List[str] = []
    is_featured: bool = False

class ProductUpdate(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None
    price:       Optional[float] = None
    old_price:   Optional[float] = None
    stock:       Optional[int] = None
    badge:       Optional[str] = None
    is_active:   Optional[bool] = None
    is_featured: Optional[bool] = None
    images:      Optional[List[str]] = None

class ProductResponse(ProductCreate):
    id:         int
    is_active:  bool
    created_at: datetime
    category:   Optional[CategoryResponse] = None

    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    total:    int
    page:     int
    per_page: int
    products: List[ProductResponse]


# ── ORDER ──────────────────────────────────────────────────────────────────

class OrderItemCreate(BaseModel):
    product_id: int
    quantity:   int

class ShippingAddress(BaseModel):
    full_name: str
    phone:     str
    address:   str
    city:      str
    state:     str

class OrderCreate(BaseModel):
    items:    List[OrderItemCreate]
    shipping: ShippingAddress
    notes:    Optional[str] = None
    currency: str = "NGN"

class OrderItemResponse(BaseModel):
    id:           int
    product_id:   int
    product_name: str
    unit_price:   float
    quantity:     int
    subtotal:     float

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id:               int
    order_ref:        str
    status:           OrderStatus
    subtotal:         float
    shipping_fee:     float
    discount:         float
    total:            float
    currency:         str
    shipping_name:    str
    shipping_phone:   str
    shipping_address: str
    shipping_city:    str
    shipping_state:   str
    payment_status:   str
    payment_method:   Optional[str]
    items:            List[OrderItemResponse]
    created_at:       datetime

    class Config:
        from_attributes = True

class PaymentVerifyRequest(BaseModel):
    order_ref:     str
    payment_ref:   str
    payment_method: str = "paystack"


# ── ADMIN ──────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_orders:    int
    total_revenue:   float
    total_customers: int
    total_products:  int
    low_stock_count: int
    pending_orders:  int

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class StockUpdate(BaseModel):
    stock: int
