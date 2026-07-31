# Deployment Guide

## 1. Provision PostgreSQL

Any managed Postgres works (RDS, Cloud SQL, Supabase, Neon, Railway, a VM).
You need the connection string:

```
postgresql://<user>:<password>@<host>:<port>/<database>
```

## 2. Configure the backend

```bash
cd backend
cp .env.example .env
# edit .env:
#   FLASK_ENV=production
#   SECRET_KEY=<random 64 chars>
#   JWT_SECRET_KEY=<different random 64 chars>
#   DATABASE_URL=postgresql://...
#   RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET / RAZORPAY_WEBHOOK_SECRET
#   UPI_MERCHANT_VPA
#   CORS_ORIGINS=https://your-customer-app-domain,https://your-admin-domain
```

Generate strong secrets:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 3. Install dependencies and run migrations against Postgres

```bash
pip install -r requirements.txt --break-system-packages
export FLASK_APP=app.py
flask db upgrade
python seed.py     # optional: demo data; skip in a real production launch
```

The migration in `migrations/versions/` was generated and verified against a
live database as part of this build (16 tables, all indexes/constraints/FKs)
— `flask db upgrade` replays the same DDL against Postgres.

## 4. Run the backend

Development: `python app.py`

Production (gunicorn, already in `requirements.txt`):

```bash
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application
```

Put this behind a reverse proxy (nginx/Caddy) that terminates TLS. The admin
dashboard is served by the same Flask app at `/admin/*` and its static
assets at `/static/*` — no separate deployment needed for it.

## 5. Deploy the customer app

```bash
cd customer-app
cp .env.example .env
# set VITE_API_BASE_URL=https://api.yourdomain.com
npm install
npm run build        # outputs to customer-app/dist/
```

`dist/` is a static site — deploy it to any static host (Netlify, Vercel,
S3+CloudFront, or served by nginx alongside the backend). It talks to the
backend purely over `VITE_API_BASE_URL` + `/api/*`.

## 6. Razorpay webhook

In the Razorpay dashboard, add a webhook pointing at:

```
https://api.yourdomain.com/api/payments/razorpay/webhook
```

and set `RAZORPAY_WEBHOOK_SECRET` in `.env` to match. Card/netbanking
payments are still authoritatively confirmed via the signed client-side
callback to `/api/payments/razorpay/verify` (HMAC-verified server-side); the
webhook is a secondary confirmation channel.

## 7. File uploads (branding logos, QR codes, reports)

`backend/app.py` creates `uploads/`, `uploads/qrcodes/`, and
`uploads/reports/` on startup. In production, mount a persistent volume at
`backend/uploads` (or point `UPLOAD_FOLDER` at object storage — not wired by
default, but the upload/QR/report services are isolated in
`services/*_service.py` so swapping local disk for S3 is a contained change).

## 8. Smoke-test after deploy

```bash
curl https://api.yourdomain.com/health
# {"status": "ok"}
```

Then log in to `/admin/login` with a real admin account (create one via
`python seed.py` once against production, then change its password, or
insert directly via `flask shell`).
