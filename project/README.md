# ital project

## Environment switch (`dev` / `prod`)

The project now switches environment via `DJANGO_SETTINGS_MODULE`.

- Development: `ital.settings.dev`
- Production: `ital.settings.prod`

Set it in `project/.env`:

```env
DJANGO_SETTINGS_MODULE=ital.settings.dev
```

or:

```env
DJANGO_SETTINGS_MODULE=ital.settings.prod
```

## Docker

Run all docker commands from `project/`.

- Dev:
```bash
cd project
docker compose up --build
```

- Prod-like run:
```bash
cd project
docker compose -f docker-compose.prod.yml up --build
```

`Dockerfile` defaults to production runtime (`gunicorn` + `collectstatic`), while `docker-compose.yml` overrides command/settings for dev workflow.

## Go-Live Runbook

### 0) Prepare production env file

Create `project/.env.prod` (separate from `.env` used in development).

### 1) Build and start prod stack

```bash
cd project
docker compose -f docker-compose.prod.yml up -d --build
```

### 2) Apply migrations

```bash
cd project
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### 3) Run release preflight

```bash
cd project
docker compose -f docker-compose.prod.yml exec web sh scripts/preflight_release.sh --skip-tests
```

For full validation (with tests):

```bash
cd project
docker compose -f docker-compose.prod.yml exec web sh scripts/preflight_release.sh
```

### 4) Check health endpoint

```bash
curl -fsS http://localhost:8000/healthz
```

Expected response: `ok`

### 5) Create DB backup before/after release

From repository root:

```bash
./scripts/backup_postgres.sh
```

Backup file is written to `./backups/`.

## Stripe payments

Required env vars:

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

Webhook endpoint:

```text
/checkout/stripe/webhook/
```

Local forwarding example with Stripe CLI:

```bash
stripe listen --forward-to localhost:8000/checkout/stripe/webhook/
```

## Fake catalog seeding

Generate a large fake catalog for local browsing and performance checks:

```bash
python manage.py seed_fake_catalog --categories 24 --products-per-category 120 --subcategories 4 --variants 3
```

Useful flags:

```bash
python manage.py seed_fake_catalog --seed 123
python manage.py seed_fake_catalog --categories 40 --products-per-category 200
```

## Load testing

Install Locust in your virtualenv if needed:

```bash
pip install locust
```

Run the test suite against local dev server:

```bash
locust -f loadtests/locustfile.py --host=http://127.0.0.1:8000
```

Suggested first run:

```bash
locust -f loadtests/locustfile.py --host=http://127.0.0.1:8000 --users 100 --spawn-rate 10 --run-time 10m --headless
```

To stress one hot product with stock contention, set a product detail path:

```bash
HOT_PRODUCT_PATH=/shop/<public_id>/<slug>/ locust -f loadtests/locustfile.py --host=http://127.0.0.1:8000 --users 100 --spawn-rate 20 --run-time 5m --headless
```

## Prod Profile Checklist

Before release, confirm:

```env
DJANGO_SETTINGS_MODULE=ital.settings.prod
DEBUG=False
ALLOWED_HOSTS=your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

Run:

```bash
python manage.py check --deploy
python scripts/check_architecture.py
python manage.py makemigrations --check --dry-run
pytest
```

`scripts/check_architecture.py` validates layer boundaries for `orders`, `catalog`, and `products`.

## Payment Runbook

### Key rotation
1. Create a new Stripe API key and webhook secret in Stripe Dashboard.
2. Update `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` in production secrets.
3. Restart app workers.
4. Verify with a sandbox/live test payment.
5. Revoke old keys in Stripe Dashboard.

### Payment desync (Stripe paid, app pending)
1. Find Stripe session id from Stripe Dashboard (`cs_...`).
2. Find local payment by `external_id`.
3. If missing webhook event, replay from Stripe Dashboard or Stripe CLI:
```bash
stripe events resend <event_id> --webhook-endpoint=<endpoint_id>
```
4. Check that payment/order status was updated.

### Manual reconciliation
1. Export paid sessions/events from Stripe for the period.
2. Compare to local `orders_payment` rows (`provider=stripe`, `status=paid`).
3. Investigate missing/extra entries using `ProcessedStripeEvent` table.

### Alerts (log-based)
Create alerts for:
1. `Stripe webhook signature validation failed`
2. `Stripe webhook duplicate event skipped` (abnormally high rate)
3. `Stripe webhook for unknown session`
4. `Stripe API error while creating payment`
