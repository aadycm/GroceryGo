# Deploying to Railway (backend + Postgres) + Vercel (customer app)

This is the exact sequence used to take GroceryGo from "works locally" to
live URLs. It assumes `docs/DEPLOYMENT_GUIDE.md` (generic) and
`docs/ENV_VARIABLES.md` (full variable reference) as background.

Config files this relies on:
- `backend/Procfile` — `web: gunicorn -w 4 -b 0.0.0.0:$PORT wsgi:application`, plus a `release: flask db upgrade` phase
- `backend/railway.json` — Nixpacks build, same start command as the Procfile
- `customer-app/vercel.json` — static build (`dist/`) with an SPA rewrite to `index.html`

## 1. Backend on Railway

```bash
cd backend
railway login
railway init            # create/link a Railway project
railway add --database postgres   # provisions Postgres, sets DATABASE_URL automatically
railway variables --set "SECRET_KEY=$(python3 -c 'import secrets;print(secrets.token_hex(32))')"
railway variables --set "JWT_SECRET_KEY=$(python3 -c 'import secrets;print(secrets.token_hex(32))')"
railway variables --set "FLASK_ENV=production"
railway variables --set "CORS_ORIGINS=*"   # temporary; locked down after the frontend URL exists
railway up
railway domain           # generates a public *.up.railway.app URL
curl https://<railway-domain>/health   # expect {"status":"ok"}
```

## 2. Customer app on Vercel

```bash
cd customer-app
echo "VITE_API_BASE_URL=https://<railway-domain>" > .env.production
vercel login
vercel --prod
```

## 3. Lock down CORS

Once the Vercel URL is known:

```bash
cd backend
railway variables --set "CORS_ORIGINS=https://<vercel-domain>"
railway up
```

## 4. Seed demo data (optional)

```bash
railway run python seed.py
```

## 5. Smoke test

- `curl https://<railway-domain>/health` → `{"status":"ok"}`
- Admin: `https://<railway-domain>/admin/login` with `owner@freshmart.test` / `Owner@12345`
- Customer app: `https://<vercel-domain>` with `customer@freshmart.test` / `Customer@12345`

Razorpay/UPI credentials are separate — see `docs/ENV_VARIABLES.md` — and are
not required for cash-payment flows to work end-to-end.
