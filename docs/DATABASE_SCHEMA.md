# Database Schema

PostgreSQL in production (SQLite fallback for local dev — see
`backend/config/config.py`). Schema is defined in `backend/models/*.py` and
applied via Alembic (`backend/migrations/versions/`), not by hand-written SQL.

## Entity-relationship diagram

```mermaid
erDiagram
    ROLES ||--o{ USERS : "has"
    USERS ||--o| CUSTOMERS : "is"
    USERS ||--o{ NOTIFICATIONS : "receives"
    USERS ||--o{ AUDIT_LOGS : "performs"
    USERS ||--o{ ORDERS : "delivers (assigned_delivery_id)"
    CUSTOMERS ||--o{ ORDERS : "places"
    CUSTOMERS ||--o{ SUBSCRIPTIONS : "holds"
    CATEGORIES ||--o{ PRODUCTS : "groups"
    PRODUCTS ||--|| INVENTORY : "tracked by"
    SUPPLIERS ||--o{ INVENTORY : "supplies"
    INVENTORY ||--o{ INVENTORY_HISTORY : "logs"
    PRODUCTS ||--o{ ORDER_ITEMS : "sold as"
    ORDERS ||--o{ ORDER_ITEMS : "contains"
    ORDERS ||--o{ PAYMENTS : "paid by"

    ROLES {
        int id PK
        string name UK
        string description
    }
    USERS {
        int id PK
        string name
        string email UK
        string password_hash
        string phone
        int role_id FK
        bool is_active
        datetime created_at
        datetime updated_at
    }
    CUSTOMERS {
        int id PK
        int user_id FK "UNIQUE, ON DELETE CASCADE"
        string address
        string city
        string pincode
        int loyalty_points
    }
    CATEGORIES {
        int id PK
        string name UK
        string description
        string image_url
    }
    PRODUCTS {
        int id PK
        string sku UK
        string name
        int category_id FK "ON DELETE SET NULL"
        numeric price "CHECK price >= 0"
        string unit
        bool is_active
    }
    SUPPLIERS {
        int id PK
        string name
        string contact_person
        string phone
        string email
    }
    INVENTORY {
        int id PK
        int product_id FK "UNIQUE, ON DELETE CASCADE"
        int quantity "CHECK quantity >= 0"
        int reorder_level
        int reorder_quantity
        int supplier_id FK "ON DELETE SET NULL"
        datetime last_restocked_at
    }
    INVENTORY_HISTORY {
        int id PK
        int inventory_id FK "ON DELETE CASCADE"
        int change_qty
        string reason
        int created_by FK
        datetime created_at
    }
    ORDERS {
        int id PK
        int customer_id FK "ON DELETE CASCADE"
        string status
        numeric total_amount "CHECK total_amount >= 0"
        string delivery_address
        int assigned_delivery_id FK "ON DELETE SET NULL"
        datetime placed_at
    }
    ORDER_ITEMS {
        int id PK
        int order_id FK "ON DELETE CASCADE"
        int product_id FK "ON DELETE RESTRICT"
        int quantity "CHECK quantity > 0"
        numeric unit_price
        numeric subtotal
    }
    PAYMENTS {
        int id PK
        int order_id FK "ON DELETE CASCADE"
        string method
        numeric amount "CHECK amount >= 0"
        string status
        string razorpay_order_id
        string razorpay_payment_id
    }
    SUBSCRIPTIONS {
        int id PK
        int customer_id FK "ON DELETE CASCADE"
        string plan_name
        string status
        date start_date
        date end_date
        numeric amount
    }
    BRANDING_SETTINGS {
        int id PK
        string app_name
        string logo_url
        string primary_color
        string secondary_color
    }
    THEME_SETTINGS {
        int id PK
        string theme_name
        json colors
        bool is_active
    }
    NOTIFICATIONS {
        int id PK
        int user_id FK "NULLABLE = broadcast, ON DELETE CASCADE"
        string title
        string message
        bool is_read
    }
    AUDIT_LOGS {
        int id PK
        int user_id FK "ON DELETE SET NULL"
        string action
        string entity_type
        int entity_id
        json details
    }
```

## Notes on cascade rules

- Deleting a `User` cascades to their `Customer` profile and `Notifications`
  (a customer account and its own profile/notifications are one lifecycle).
- Deleting a `Product` cascades to its `Inventory` row (soft-delete via
  `is_active=false` is used instead of hard delete in the API — see
  `DELETE /api/products/<id>`).
- Deleting an `Order` cascades to `OrderItems` and `Payments`.
- `OrderItems.product_id` uses `ON DELETE RESTRICT` — a product referenced by
  historical order line items cannot be hard-deleted, which is why the
  product delete endpoint deactivates rather than removes rows.
- `Inventory.supplier_id`, `Order.assigned_delivery_id`, and
  `AuditLogs.user_id` use `ON DELETE SET NULL` so removing a supplier or
  staff account doesn't destroy historical records.

## Indexes

Unique/lookup indexes on `users.email`, `products.sku`, `products.name`,
`categories.name`, `roles.name`; query-pattern indexes on `orders.status`,
`orders.placed_at`, `payments.status`, `payments.razorpay_order_id`,
`payments.razorpay_payment_id`, `inventory_history.created_at`,
`notifications.created_at`, `audit_logs.created_at`, and a composite index on
`inventory(quantity, reorder_level)` for the low-stock query.

## Migrations

```bash
cd backend
flask db upgrade                 # apply migrations/versions/*.py
flask db migrate -m "message"    # generate a new migration after model changes
```

The initial migration (`migrations/versions/454bef96b498_*.py`) was generated
with `flask db migrate` against the real models — it is not hand-written —
and has been applied and verified against a live SQLite database as part of
this build (see `docs/DEPLOYMENT_GUIDE.md` for the PostgreSQL equivalent).
