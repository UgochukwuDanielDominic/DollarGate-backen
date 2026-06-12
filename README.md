# DollarGate Backend API

**Python · FastAPI · PostgreSQL · Paystack**

---

## Project Structure

```
dollargate/
├── app/
│   ├── main.py              # App entry point
│   ├── config.py            # Settings & env vars
│   ├── database.py          # DB connection
│   ├── models/
│   │   └── models.py        # SQLAlchemy models
│   ├── schemas/
│   │   └── schemas.py       # Pydantic schemas
│   ├── middleware/
│   │   └── auth.py          # JWT & auth helpers
│   └── routes/
│       ├── auth.py          # Register, Login, Refresh
│       ├── users.py         # Profile, Wishlist
│       ├── products.py      # Products, Categories
│       ├── orders.py        # Orders, Payment
│       └── admin.py         # Dashboard, Reports
├── seed.py                  # Database seeder
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Install Python 3.11+
Download from https://python.org

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL
- Install PostgreSQL: https://postgresql.org/download
- Create a database:
```sql
CREATE DATABASE dollargate;
```

### 5. Configure environment
```bash
cp .env.example .env
# Edit .env with your database URL and keys
```

### 6. Seed the database
```bash
python seed.py
```
This creates your admin account and all 8 starter products.

### 7. Run the server
```bash
uvicorn app.main:app --reload
```
Server runs at: **http://localhost:8000**
API docs at: **http://localhost:8000/docs**

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Create account |
| POST | /api/auth/login | Login |
| POST | /api/auth/refresh | Refresh token |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/products | List products (filter, search, paginate) |
| GET | /api/products/{slug} | Single product |
| GET | /api/products/categories | All categories |
| POST | /api/products | Create product (admin) |
| PUT | /api/products/{id} | Update product (admin) |
| DELETE | /api/products/{id} | Soft-delete product (admin) |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/orders | Place an order |
| GET | /api/orders/{ref} | Get order details |
| POST | /api/orders/verify-payment | Verify Paystack payment |
| POST | /api/orders/{ref}/cancel | Cancel order |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/users/me | My profile |
| PUT | /api/users/me | Update profile |
| PUT | /api/users/me/password | Change password |
| GET | /api/users/me/orders | My orders |
| GET | /api/users/me/wishlist | My wishlist |
| POST | /api/users/me/wishlist/{id} | Toggle wishlist |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/admin/dashboard | Stats overview |
| GET | /api/admin/orders | All orders |
| PUT | /api/admin/orders/{ref}/status | Update order status |
| GET | /api/admin/users | All users |
| PUT | /api/admin/users/{id}/toggle-active | Activate/deactivate user |
| GET | /api/admin/inventory | Low stock report |
| PUT | /api/admin/inventory/{id}/stock | Update stock |
| GET | /api/admin/reports/revenue | Monthly revenue report |

---

## Default Admin Credentials
```
Email:    admin@dollargate.com
Password: Admin@1234
```
⚠️ Change this immediately in production!

---

## Payment Flow (Paystack)

1. Frontend creates an order → gets `order_ref` + `total`
2. Frontend initiates Paystack payment with the total amount
3. Paystack returns a `payment_ref` on success
4. Frontend calls `POST /api/orders/verify-payment` with both refs
5. Backend verifies with Paystack → marks order as **paid** + **confirmed**

---

## Deploying to Production

Recommended stack:
- **Server**: Railway, Render, or a ₦5k/month VPS (Contabo)
- **Database**: Supabase (free PostgreSQL) or Railway Postgres
- **Domain**: Point your domain to the server IP

Set `ENVIRONMENT=production` in your `.env` and update `CORS` origins in `main.py`.
