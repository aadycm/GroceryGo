# Finishing this in ~2 hours

Everything in this build has been implemented, migrated, seeded, and tested
already (32/32 backend tests pass, TypeScript compiles with zero errors, the
customer app production-builds cleanly, all 16 database tables are live).
What's left is entirely things that need *your* input — credentials,
verification on your machine, and a go/no-go on going live. Rough time
budget below; adjust as needed.

## 0. Credentials checklist (do this first, ~15 min)

You'll need to get these before anything below works with real payments:

| Item | Where to get it | Used for |
|---|---|---|
| PostgreSQL connection string | Neon.tech / Supabase / Railway (free tier, ~5 min signup) or `brew install postgresql` locally | `DATABASE_URL` |
| Razorpay Key ID + Secret | razorpay.com dashboard → Settings → API Keys (test mode is instant, no approval wait) | `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` |
| Razorpay webhook secret | Razorpay dashboard → Webhooks → create one (can point at a placeholder URL for now) | `RAZORPAY_WEBHOOK_SECRET` |
| UPI merchant VPA | Your business UPI ID (or a test one for now, e.g. `success@razorpay` for Razorpay's test UPI) | `UPI_MERCHANT_VPA` |
| Logo file (optional) | Your own asset, or skip — branding works without one | Uploaded via admin dashboard, not an env var |

Without these, everything runs (SQLite fallback, cash payments work fully),
you just can't test real UPI/card payments or a real Postgres instance.

## 1. Backend up and running (~20 min)

```bash
cd backend
pip install -r requirements.txt --break-system-packages
cp .env.example .env
# Fill in DATABASE_URL (or leave unset to use SQLite for now), Razorpay keys, UPI VPA
export FLASK_APP=app.py FLASK_ENV=development
flask db upgrade
python seed.py
python app.py
```

Check: `curl http://localhost:5000/health` → `{"status": "ok"}`

## 2. Admin dashboard (~10 min)

Open `http://localhost:5000/admin/login`, sign in as
`owner@freshmart.test` / `Owner@12345`. Walk through: Dashboard → Inventory
(try a restock) → Orders → Reports (export a PDF) → Branding (change the
app name, see it reflected in the sidebar).

## 3. Customer app (~15 min)

```bash
cd customer-app
npm install
npm run dev
```

Open `http://localhost:5173`, log in as `customer@freshmart.test` /
`Customer@12345`. Browse → add to cart → checkout → pay with Cash (works
immediately) → check Order History → track the order.

## 4. Test real payments (~15 min, needs Razorpay keys from step 0)

- UPI: place an order, choose UPI at checkout, confirm a QR renders.
- Card/Netbanking: choose Card, confirm the Razorpay Checkout widget opens
  (use Razorpay's documented test card numbers in test mode).

## 5. Switch to real PostgreSQL (~15 min, needs step 0)

```bash
export DATABASE_URL=postgresql://...
flask db upgrade   # replays the same migration against Postgres
python seed.py     # optional demo data
```

## 6. Decide what to seed for real launch (~10 min)

`seed.py` creates demo users/products for testing. Before a real launch,
either edit it to reflect your actual FreshMart catalog and staff, or write
your real products through the admin dashboard's Inventory page instead.

## 7. Deploy (~30–40 min, see `DEPLOYMENT_GUIDE.md`)

Pick a host for the backend (Render/Railway/Fly.io/a VM), point
`DATABASE_URL` at your Postgres instance, deploy the customer app's
`npm run build` output to a static host, set `CORS_ORIGINS` to your real
domains, and point Razorpay's webhook at your deployed backend.

---

Everything through step 6 can run entirely on your laptop with no
deployment. Step 7 is the only piece that takes you outside "it works
locally" — budget it separately once steps 1–6 are confirmed working for
you.
