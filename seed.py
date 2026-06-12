"""
Run this once to seed the database with categories, products, and an admin user.
Usage: python seed.py
"""
import sys
sys.path.append(".")

from app.database import SessionLocal, engine, Base
from app.models.models import User, Category, Product, UserRole, Gender
from app.middleware.auth import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ── ADMIN USER ─────────────────────────────────────────────────────────────
admin = db.query(User).filter(User.email == "admin@dollargate.com").first()
if not admin:
    admin = User(
        email         = "admin@dollargate.com",
        full_name     = "DollarGate Admin",
        password_hash = hash_password("Admin@1234"),
        role          = UserRole.admin,
        is_active     = True,
        is_verified   = True,
    )
    db.add(admin)
    db.commit()
    print("✅ Admin created → admin@dollargate.com / Admin@1234")

# ── CATEGORIES ─────────────────────────────────────────────────────────────
categories_data = [
    {"name": "Watches",  "slug": "watches",  "description": "Luxury timepieces for men and women"},
    {"name": "Eyewear",  "slug": "eyewear",  "description": "Designer sunglasses and optical frames"},
    {"name": "Sunglasses","slug":"sunglasses","description": "Premium sunglasses collection"},
]
cat_map = {}
for c in categories_data:
    existing = db.query(Category).filter(Category.slug == c["slug"]).first()
    if not existing:
        obj = Category(**c)
        db.add(obj)
        db.flush()
        cat_map[c["slug"]] = obj.id
        print(f"✅ Category: {c['name']}")
    else:
        cat_map[c["slug"]] = existing.id
db.commit()

# ── PRODUCTS ───────────────────────────────────────────────────────────────
products_data = [
    {
        "name": "Chronos Elite", "slug": "chronos-elite",
        "description": "Precision-crafted timepiece with Swiss movement. Stainless steel case, sapphire crystal glass, and a premium leather strap.",
        "brand": "DollarGate", "sku": "DG-W-001",
        "price": 24500, "old_price": 32000, "cost_price": 12000,
        "stock": 25, "category_id": cat_map["watches"],
        "gender": Gender.men, "badge": "Bestseller", "is_featured": True,
        "images": ["/images/chronos-elite.jpg"],
        "tags": ["watch", "men", "luxury", "leather"],
    },
    {
        "name": "Luna Rose Gold", "slug": "luna-rose-gold",
        "description": "Elegant rose gold women's watch. Minimalist dial, ceramic bracelet, and water-resistant up to 30m.",
        "brand": "DollarGate", "sku": "DG-W-002",
        "price": 19800, "old_price": None, "cost_price": 9500,
        "stock": 18, "category_id": cat_map["watches"],
        "gender": Gender.women, "badge": "New", "is_featured": True,
        "images": ["/images/luna-rose-gold.jpg"],
        "tags": ["watch", "women", "rose gold"],
    },
    {
        "name": "Stealth Black", "slug": "stealth-black",
        "description": "All-black tactical watch. Ion-plated case, carbon fibre dial, silicone strap. Bold statement for the modern man.",
        "brand": "DollarGate", "sku": "DG-W-003",
        "price": 31000, "old_price": 40000, "cost_price": 16000,
        "stock": 12, "category_id": cat_map["watches"],
        "gender": Gender.men, "badge": "Sale", "is_featured": True,
        "images": ["/images/stealth-black.jpg"],
        "tags": ["watch", "men", "black", "tactical"],
    },
    {
        "name": "Gold Commander", "slug": "gold-commander",
        "description": "Statement gold-tone watch. Chronograph functions, date display, and full stainless steel construction.",
        "brand": "DollarGate", "sku": "DG-W-004",
        "price": 27500, "old_price": 35000, "cost_price": 14000,
        "stock": 8, "category_id": cat_map["watches"],
        "gender": Gender.men, "badge": None, "is_featured": False,
        "images": ["/images/gold-commander.jpg"],
        "tags": ["watch", "men", "gold", "chronograph"],
    },
    {
        "name": "Aviator Pro", "slug": "aviator-pro",
        "description": "Classic aviator sunglasses with polarised lenses. UV400 protection, lightweight titanium frame.",
        "brand": "DollarGate", "sku": "DG-E-001",
        "price": 8900, "old_price": 12000, "cost_price": 3500,
        "stock": 40, "category_id": cat_map["sunglasses"],
        "gender": Gender.men, "badge": "Sale", "is_featured": True,
        "images": ["/images/aviator-pro.jpg"],
        "tags": ["sunglasses", "men", "polarised", "aviator"],
    },
    {
        "name": "Noir Oversized", "slug": "noir-oversized",
        "description": "Chic oversized square frames in matte black. UV400, acetate construction. The statement piece your wardrobe needs.",
        "brand": "DollarGate", "sku": "DG-E-002",
        "price": 7500, "old_price": None, "cost_price": 3000,
        "stock": 35, "category_id": cat_map["sunglasses"],
        "gender": Gender.women, "badge": "Trending", "is_featured": True,
        "images": ["/images/noir-oversized.jpg"],
        "tags": ["sunglasses", "women", "oversized", "black"],
    },
    {
        "name": "Velvet Frame", "slug": "velvet-frame",
        "description": "Sophisticated optical frames in rich tortoise acetate. Lightweight, flexible hinges, suitable for prescription lenses.",
        "brand": "DollarGate", "sku": "DG-E-003",
        "price": 11200, "old_price": None, "cost_price": 4800,
        "stock": 22, "category_id": cat_map["eyewear"],
        "gender": Gender.women, "badge": "New", "is_featured": False,
        "images": ["/images/velvet-frame.jpg"],
        "tags": ["eyewear", "women", "optical", "tortoise"],
    },
    {
        "name": "Crystal Clear", "slug": "crystal-clear",
        "description": "Sleek transparent frame sunglasses. Anti-reflective coating, UV400 protection, unisex appeal.",
        "brand": "DollarGate", "sku": "DG-E-004",
        "price": 6800, "old_price": 9000, "cost_price": 2800,
        "stock": 30, "category_id": cat_map["sunglasses"],
        "gender": Gender.unisex, "badge": "Sale", "is_featured": False,
        "images": ["/images/crystal-clear.jpg"],
        "tags": ["sunglasses", "unisex", "transparent"],
    },
]

for p in products_data:
    if not db.query(Product).filter(Product.slug == p["slug"]).first():
        db.add(Product(**p))
        print(f"✅ Product: {p['name']}")

db.commit()
db.close()
print("\n🎉 Seed complete! Your DollarGate database is ready.")
print("📖 API docs available at: http://localhost:8000/docs")
