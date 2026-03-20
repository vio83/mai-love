# Monetization Technical Checklist 2026

## Objective
Ship a monetizable AI product with reliable billing, metering, and KPI visibility.

## Executable tasks

### A) Billing hooks (Stripe)
1. Add env vars in backend runtime:
   - `STRIPE_SECRET_KEY`
   - `STRIPE_WEBHOOK_SECRET`
2. Implement endpoint `/billing/webhook` with signature verification.
3. Persist events:
   - `invoice.paid`
   - `invoice.payment_failed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`

### B) Metering
1. Define usage unit:
   - `input_tokens`
   - `output_tokens`
   - `requests_count`
2. Persist metering per user/tenant daily.
3. Add monthly hard limit by plan tier.

### C) KPI dashboard
1. Add backend endpoint `/kpi/business`.
2. Minimum KPIs:
   - MRR
   - Active paid users
   - Conversion rate free->paid
   - Churn monthly
   - ARPU
3. Save daily snapshot JSON to `data/autonomous_runtime/business-kpi.json`.

### D) Alerting
1. Alert on failed billing webhooks.
2. Alert on churn spike (> 2x 30d baseline).
3. Alert on p95 latency > target.

## Local run

```bash
bash scripts/monetization/run_monetization_readiness.sh
```

The command writes reports under `data/autonomous_runtime/`.
