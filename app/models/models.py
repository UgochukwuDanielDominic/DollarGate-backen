from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text,
    DateTime, ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


# ── ENUMS ──────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    customer = "customer"
    admin    = "admin"

class OrderStatus(str, enum.Enum):
    pending    = "pending"
    confirmed  = "confirmed"
    shipped    = "shipped"
    delivered  = "delivered"
    cancelled  = "cancelled"
    refunded   = "refunded"

class Gender(str, enum.Enum):
    men   = "men"
    women = "women"
    unisex = "unisex"


# ── USER ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String(255), unique=True, index=True, nullable=False)
    full_name     = Column(String(255), nullable=False)
    phone         = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role          = Column(SAEnum(UserRole), default=UserRole.customer)
    is_active     = Column(Boolean, default=True)
    is_verified   = Column(Boolean, default=False)

    # Address
    address       = Column(Text, nullable=True)
    city          = Column(String(100), nullable=True)
    state         = Column(String(100), nullable=True)

    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    orders        = relationship("Order", back_populates="user")
    wishlist      = relationship("Wishlist", back_populates="user")


# ── CATEGORY ───────────────────────────────────────────────────────────────

class Category(Base):
    __tablename__ = "categories"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), unique=True, nullable=False)
    slug        = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    image_url   = Column(String(500), nullable=True)
    is_active   = Column(Boolean, default=True)

    products    = relationship("Product", back_populates="category")


# ── PRODUCT ────────────────────────────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(255), nullable=False)
    slug          = Column(String(255), unique=True, nullable=False)
    description   = Column(Text, nullable=True)
    brand         = Column(String(100), nullable=True)
    sku           = Column(String(100), unique=True, nullable=True)

    price         = Column(Float, nullable=False)
    old_price     = Column(Float, nullable=True)
    cost_price    = Column(Float, nullable=True)   # for profit tracking

    stock         = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=5)

    category_id   = Column(Integer, ForeignKey("categories.id"), nullable=True)
    gender        = Column(SAEnum(Gender), default=Gender.unisex)

    images        = Column(JSON, default=list)   # list of image URLs
    badge         = Column(String(50), nullable=True)  # "New", "Sale", "Trending"
    tags          = Column(JSON, default=list)

    is_active     = Column(Boolean, default=True)
    is_featured   = Column(Boolean, default=False)

    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    category      = relationship("Category", back_populates="products")
    order_items   = relationship("OrderItem", back_populates="product")
    wishlist      = relationship("Wishlist", back_populates="product")


# ── ORDER ──────────────────────────────────────────────────────────────────

class Order(Base):
    __tablename__ = "orders"

    id               = Column(Integer, primary_key=True, index=True)
    order_ref        = Column(String(50), unique=True, nullable=False)  # e.g. DG-20250001
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False)

    status           = Column(SAEnum(OrderStatus), default=OrderStatus.pending)

    # Pricing
    subtotal         = Column(Float, nullable=False)
    shipping_fee     = Column(Float, default=0.0)
    discount         = Column(Float, default=0.0)
    total            = Column(Float, nullable=False)
    currency         = Column(String(10), default="NGN")

    # Shipping address (snapshot at time of order)
    shipping_name    = Column(String(255), nullable=False)
    shipping_phone   = Column(String(20), nullable=False)
    shipping_address = Column(Text, nullable=False)
    shipping_city    = Column(String(100), nullable=False)
    shipping_state   = Column(String(100), nullable=False)

    # Payment
    payment_ref      = Column(String(255), nullable=True)   # Paystack reference
    payment_status   = Column(String(50), default="unpaid")  # unpaid | paid | refunded
    payment_method   = Column(String(50), nullable=True)

    notes            = Column(Text, nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())

    user             = relationship("User", back_populates="orders")
    items            = relationship("OrderItem", back_populates="order")


# ── ORDER ITEM ─────────────────────────────────────────────────────────────

class OrderItem(Base):
    __tablename__ = "order_items"

    id           = Column(Integer, primary_key=True, index=True)
    order_id     = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id   = Column(Integer, ForeignKey("products.id"), nullable=False)

    product_name = Column(String(255), nullable=False)  # snapshot
    unit_price   = Column(Float, nullable=False)         # price at time of order
    quantity     = Column(Integer, nullable=False)
    subtotal     = Column(Float, nullable=False)

    order        = relationship("Order", back_populates="items")
    product      = relationship("Product", back_populates="order_items")


# ── WISHLIST ───────────────────────────────────────────────────────────────

class Wishlist(Base):
    __tablename__ = "wishlist"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user       = relationship("User", back_populates="wishlist")
    product    = relationship("Product", back_populates="wishlist")
