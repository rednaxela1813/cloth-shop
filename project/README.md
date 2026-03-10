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

- Dev:
```bash
docker compose up --build
```

- Prod-like run:
```bash
docker compose -f docker-compose.prod.yml up --build
```

`Dockerfile` defaults to production runtime (`gunicorn` + `collectstatic`), while `docker-compose.yml` overrides command/settings for dev workflow.

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
