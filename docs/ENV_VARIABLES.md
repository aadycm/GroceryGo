# Environment Variables

Copy `backend/.env.example` to `backend/.env` (the app loads it automatically
via `python-dotenv`) and `customer-app/.env.example` to `customer-app/.env`.

## Backend (`backend/.env`)

| Variable | Required | Default | Notes |
|---|---|---|---|
| `FLASK_ENV` | recommended | `development` | `development` \| `production` \| `testing` |
| `SECRET_KEY` | production | dev placeholder | Flask session/signing secret — set a random 64-char value |
| `JWT_SECRET_KEY` | production | dev placeholder | Signs access/refresh tokens — set a **different** random 64-char value |
| `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` | no | `60` | |
| `JWT_REFRESH_TOKEN_EXPIRES_DAYS` | no | `30` | |
| `DATABASE_URL` | **production: yes** | SQLite file (dev only) | `postgresql://user:pass@host:5432/grocerygo` — see below |
| `RAZORPAY_KEY_ID` | to accept card/netbanking | none | From Razorpay dashboard (test or live) |
| `RAZORPAY_KEY_SECRET` | to accept card/netbanking | none | Keep server-side only, never expose to the frontend |
| `RAZORPAY_WEBHOOK_SECRET` | to receive webhooks | none | Set when configuring the webhook URL in Razorpay |
| `UPI_MERCHANT_VPA` | to accept UPI | none | Your merchant UPI ID, e.g. `freshmart@okhdfcbank` |
| `UPI_MERCHANT_NAME` | no | `FreshMart` | Shown in the UPI payment app |
| `CORS_ORIGINS` | production | `*` | Comma-separated allowed origins, e.g. `https://app.freshmart.com` |
| `RATE_LIMIT_DEFAULT` | no | `200 per hour` | Flask-Limiter default rule |
| `UPLOAD_FOLDER` | no | `uploads` | Relative to `backend/` |
| `MAX_CONTENT_LENGTH_MB` | no | `5` | Max upload size (logo images) |
| `PORT` | no | `5000` | Only used by `python app.py` directly; gunicorn takes `-b` instead |

**`DATABASE_URL` is the one variable that gates going to production** — see
`config/config.py`: `ProductionConfig` requires it and `get_config()` raises
a clear `RuntimeError` if `FLASK_ENV=production` and it's unset.

## Customer app (`customer-app/.env`)

| Variable | Required | Default | Notes |
|---|---|---|---|
| `VITE_API_BASE_URL` | production build | empty (uses Vite dev proxy) | Set to your deployed backend origin, e.g. `https://api.freshmart.com` |

## Admin dashboard

No separate env file — it's served by the Flask app itself
(`admin-dashboard/templates` + `static` are wired into `backend/app.py`) and
inherits the backend's configuration.
