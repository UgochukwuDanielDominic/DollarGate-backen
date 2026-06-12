from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, products, orders, users, admin
from app.database import engine, Base

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DollarGate API",
    description="Backend API for DollarGate — Luxury Watches & Eyewear",
    version="1.0.0"
)

# CORS — allow your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router,     prefix="/api/auth",     tags=["Auth"])
app.include_router(users.router,    prefix="/api/users",    tags=["Users"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(orders.router,   prefix="/api/orders",   tags=["Orders"])
app.include_router(admin.router,    prefix="/api/admin",    tags=["Admin"])

@app.get("/")
def root():
    return {"message": "DollarGate API is running 🚀", "docs": "/docs"}
