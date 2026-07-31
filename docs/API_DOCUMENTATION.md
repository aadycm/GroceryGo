# API Documentation

Base URL: `http://localhost:5000` (dev) or your deployed backend origin.
All request/response bodies are JSON unless noted. Authenticated endpoints
require `Authorization: Bearer <access_token>`.

Every endpoint below is implemented in `backend/routes/*.py` and covered
end-to-end by either the pytest suite (`tests/`) or the manual verification
run documented in this project's build log — nothing here is aspirational.

## Response envelope

Success: `{ "data": ..., "message": "...", "meta": {...} }` (message/meta optional)
Error: `{ "error": "human-readable message" }`
List endpoints support `?page=&per_page=&sort_by=&sort_dir=` and return a `meta` block with pagination info.

## Auth (`/api/auth`)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | none | Register a customer (`name`, `email`, `password`, optional `phone`, `address`, `city`, `pincode`) |
| POST | `/api/auth/login` | none | `{email, password}` → `{access_token, refresh_token, user}` |
| POST | `/api/auth/refresh` | none | `{refresh_token}` → new `access_token` |
| GET | `/api/auth/me` | any | Current user profile |

Access tokens expire in 60 minutes, refresh tokens in 30 days (configurable via env).

## Categories (`/api/categories`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/categories` | none | List all categories |
| GET | `/api/categories/<id>` | none | Get one category |
| POST | `/api/categories` | admin, manager | Create |
| PUT | `/api/categories/<id>` | admin, manager | Update |
| DELETE | `/api/categories/<id>` | admin | Delete |

## Products (`/api/products`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/products` | none | List, filters: `search`, `category_id`, `min_price`, `max_price`; paginated/sorted |
| GET | `/api/products/<id>` | none | Get one product (includes live stock) |
| POST | `/api/products` | admin, manager | Create (also creates its Inventory row) |
| PUT | `/api/products/<id>` | admin, manager | Update |
| DELETE | `/api/products/<id>` | admin | Soft-delete (`is_active=false`) |

## Inventory (`/api/inventory`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/inventory` | admin, manager, staff | List all inventory rows |
| GET | `/api/inventory/low-stock` | admin, manager, staff | Items at/below reorder level |
| GET | `/api/inventory/reorder-suggestions` | admin, manager | Suggested reorder quantities + supplier |
| PUT | `/api/inventory/<product_id>` | admin, manager | Update reorder_level / reorder_quantity / supplier_id |
| POST | `/api/inventory/<product_id>/adjust` | admin, manager, staff | `{change_qty, reason}`; reason ∈ restock/sale/adjustment/return |
| GET | `/api/inventory/<product_id>/history` | admin, manager, staff | Full audit trail of stock changes |

## Orders (`/api/orders`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/orders` | any | Own orders (customer), assigned orders (delivery), all orders (admin/manager/staff); `?status=` filter |
| GET | `/api/orders/<id>` | any (scoped) | Order detail with items |
| POST | `/api/orders` | any | Place order: `{items:[{product_id,quantity}], delivery_address}` — reserves stock atomically, 409 if insufficient |
| PUT | `/api/orders/<id>/status` | admin, manager, staff | Advance status; enforces valid state machine (see below) |
| PUT | `/api/orders/<id>/assign-delivery` | admin, manager | `{delivery_user_id}` |
| POST | `/api/orders/<id>/cancel` | any (scoped) | Cancels and restores reserved stock |
| GET | `/api/orders/<id>/track` | any | Lightweight status/assignment poll |
| GET | `/api/orders/<id>/qr` | any | Generates/returns a QR code for the order |

Order status state machine: `pending → confirmed → preparing → out_for_delivery → delivered`, with `cancelled` reachable from any non-terminal state. Invalid transitions return `409`.

## Payments (`/api/payments`)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/payments/orders/<order_id>/initiate` | any (scoped) | `{method}` ∈ upi/card/netbanking/cash |
| POST | `/api/payments/razorpay/verify` | any | `{razorpay_order_id, razorpay_payment_id, razorpay_signature}` — HMAC-verified, idempotent |
| POST | `/api/payments/upi/verify` | any | `{payment_id, token, transaction_ref}` — single-use QR token, idempotent |
| POST | `/api/payments/razorpay/webhook` | none (HMAC-verified) | Razorpay server-to-server webhook receiver |
| GET | `/api/payments/order/<order_id>` | any | All payments for an order |

`cash` marks the payment successful immediately. `upi` returns a UPI deep
link and a single-use expiring QR PNG. `card`/`netbanking` create a Razorpay
order and return the key/order id for the Razorpay Checkout widget.

## Customers (`/api/customers`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/customers` | admin, manager | List all customers |
| GET | `/api/customers/<id>` | any (self or staff) | Customer profile |
| PUT | `/api/customers/<id>` | any (self or staff) | Update address/city/pincode/name/phone |

## Suppliers (`/api/suppliers`)

Standard CRUD, `admin`/`manager` for writes, `DELETE` is `admin`-only.

## Subscriptions (`/api/subscriptions`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/subscriptions` | any | Own (customer) or all (staff+) |
| POST | `/api/subscriptions` | admin, manager | Create |
| PUT | `/api/subscriptions/<id>` | admin, manager | Update |

## Branding (`/api/branding`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/branding` | none | Current app name/colors/logo |
| PUT | `/api/branding` | admin | Update app name/colors |
| POST | `/api/branding/logo` | admin | Multipart upload, `logo` field |

## Themes (`/api/themes`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/themes` | none | All saved themes |
| GET | `/api/themes/active` | none | Currently active theme |
| POST | `/api/themes` | admin | Create (dark/light/custom + colors JSON) |
| PUT | `/api/themes/<id>/activate` | admin | Activate (deactivates all others) |

## Notifications (`/api/notifications`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/notifications` | any | Own + broadcast notifications |
| PUT | `/api/notifications/<id>/read` | any | Mark read |
| POST | `/api/notifications/broadcast` | admin, manager | Send to all users |

## Reports (`/api/reports`)

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/reports/sales?period=` | admin, manager | period ∈ daily/weekly/monthly |
| GET | `/api/reports/revenue?period=` | admin, manager | Revenue total + breakdown by payment method |
| GET | `/api/reports/inventory` | admin, manager | Stock levels + low-stock count |
| GET | `/api/reports/customers` | admin, manager | Per-customer order/spend summary |
| GET | `/api/reports/top-products?period=` | admin, manager | Best sellers by units/revenue |
| GET | `/api/reports/<type>/export?format=pdf\|excel` | admin, manager | Downloads the report as PDF or XLSX |
| GET | `/api/reports/invoice/<order_id>` | any (scoped) | Downloads a PDF invoice |

## Audit logs (`/api/audit-logs`)

`GET /api/audit-logs` — `admin` only, paginated/sorted.

## QR codes (`/api/qr`)

`GET /api/qr/product/<id>` (public), `GET /api/qr/order/<id>` (authenticated) — both return `{qr_code_path}`, a static file under `/uploads/qrcodes/`.

## Machine-readable spec

A structural OpenAPI 3.0 document covering the core resources is at
[`docs/openapi.yaml`](openapi.yaml). It documents shapes and auth
requirements for the primary flows (auth, products, orders, payments); the
table above is the complete reference for every route.
