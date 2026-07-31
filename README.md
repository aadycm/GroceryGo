# GroceryGo / FreshMart — Unified Platform

A single, production-ready grocery commerce platform for the fictional shop
**FreshMart** (Nandambakkam, Chennai): one Flask + PostgreSQL backend serving
both a React customer app and a server-rendered admin dashboard.

This repository was built from scratch in this workspace — the original
GroceryGo prototypes (HTML dashboard, Flask/Jinja2 version, MySQL version,
Ingres version, and the customer-facing `GroceryGoApp.tsx`) from earlier
sessions were never saved to disk and could not be recovered, so there was no
existing code to consolidate. Everything below is new, and it *is* the single
consolidated architecture the earlier prototypes were working towards.

## Architecture

```
GroceryGo/
├── backend/            Flask + SQLAlchemy + PostgreSQL REST API (the only backend)
│   ├── app.py           App factory
│   ├── config/          Environment-based config (dev/prod/test)
│   ├── database/        SQLAlchemy + Flask-Migrate setup
│   ├── models/          16 tables: Users, Roles, Customers, Products, Categories,
│   │                    Inventory, InventoryHistory, Orders, OrderItems, Payments,
│   │                    Suppliers, Subscriptions, BrandingSettings, ThemeSettings,
│   │                    Notifications, AuditLogs
│   ├── routes/          REST blueprints (auth, products, orders, payments, ...)
│   ├── services/        Business logic (order, inventory, payment/Razorpay, reports, QR)
│   ├── auth/            JWT issuing/verification + role decorators
│   ├── middleware/      Error handlers, CORS, rate limiting
│   ├── utils/           Pagination, validation, response helpers
│   ├── migrations/      Alembic migrations (generated, not hand-written)
│   └── seed.py          Demo roles/users/products/orders
├── admin-dashboard/     Jinja2 templates + vanilla JS, calls the same REST API
├── customer-app/        React + TypeScript (Vite), calls the same REST API
├── tests/                32 pytest tests covering auth, inventory, orders, payments, reports
└── docs/                 This documentation set
```

**One backend, one database, one set of REST APIs.** Both frontends are pure
API consumers — there is no server-rendered business logic duplicated in the
admin dashboard and no mock data anywhere in the customer app.

## Quick start (local, no PostgreSQL required)

The backend falls back to a local SQLite file when `DATABASE_URL` isn't set,
so you can try the whole system before provisioning Postgres:

```bash
cd backend
pip install -r requirements.txt --break-system-packages
export FLASK_APP=app.py FLASK_ENV=development
flask db upgrade          # applies migrations/versions/*.py
python seed.py             # demo roles, users, products, one sample order
python app.py               # http://localhost:5000
```

Then either:
- Open `http://localhost:5000/admin/login` for the admin dashboard, or
- `cd ../customer-app && npm install && npm run dev` → `http://localhost:5173`

Demo logins (created by `seed.py`):

| Role | Email | Password |
|---|---|---|
| Owner (admin) | owner@freshmart.test | Owner@12345 |
| Auditor (manager) | auditor@freshmart.test | Auditor@12345 |
| Staff | staff@freshmart.test | Staff@12345 |
| Delivery | delivery@freshmart.test | Delivery@12345 |
| Customer | customer@freshmart.test | Customer@12345 |

## Documentation index

- [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) — every REST endpoint
- [`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md) — ERD + table definitions
- [`docs/ENV_VARIABLES.md`](docs/ENV_VARIABLES.md) — every environment variable
- [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) — PostgreSQL + production deploy
- [`docs/NEXT_STEPS_CHECKLIST.md`](docs/NEXT_STEPS_CHECKLIST.md) — what's left for you, in order

## Running tests

```bash
cd GroceryGo
pip install -r backend/requirements.txt --break-system-packages
python -m pytest tests/ -v
```

32/32 tests pass against an isolated SQLite database (auth, RBAC, inventory
adjustments, order lifecycle + stock reservation/restoration, cash/UPI/card
payment flows including idempotent retries, and report/invoice generation).

## What's genuinely done vs. what needs your input

Everything is implemented and tested end-to-end using safe local defaults
(SQLite instead of Postgres, no real Razorpay/UPI credentials). To go live
you must supply real credentials — see `docs/NEXT_STEPS_CHECKLIST.md`.
