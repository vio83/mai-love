# P0/P1 Setup Guide (Mac + VS Code + VIO/AI LOVE)

## P0 — Oggi (critico)

### 1) Stripe Billing
- URL: https://stripe.com
- Cosa attivare:
  - API key: `STRIPE_SECRET_KEY`
  - Webhook signing secret: `STRIPE_WEBHOOK_SECRET`
- Endpoint backend pronto: `POST /billing/webhook/stripe`
- Test eventi minimi:
  - `invoice.paid`
  - `invoice.payment_failed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`

### 2) Sentry
- URL: https://sentry.io
- Cosa attivare:
  - DSN backend/frontend: `SENTRY_DSN`
- Obiettivo:
  - Alert errori runtime in produzione
  - Riduzione MTTR

### 3) PostHog
- URL: https://posthog.com
- Cosa attivare:
  - `POSTHOG_API_KEY`
  - `POSTHOG_HOST` (default: `https://app.posthog.com`)
- Eventi funnel minimi:
  - `signup_started`
  - `signup_completed`
  - `first_message_sent`
  - `upgrade_clicked`

## P1 — Questa settimana

### 4) GitHub policy governance
- URL: https://github.com/pricing
- Config consigliata:
  - Branch protection su `main`
  - Required checks: `CI — Release Gate`, `Python Backend — Lint & Test`
  - Code owners per path critici

### 5) OpenTelemetry + Grafana Cloud
- URL: https://opentelemetry.io
- URL: https://grafana.com/products/cloud
- Obiettivo:
  - Tracing E2E frontend/backend/provider
  - KPI operativi p95, error rate, throughput

## KPI Business endpoint già pronto
- `GET /kpi/business`
- Salva snapshot in: `data/autonomous_runtime/business-kpi.json`

## Costi indicativi (marzo 2026)
- Stripe: fee transazione, no canone fisso tipico.
- Sentry: free tier + scaling a consumo.
- PostHog: free tier + scaling a eventi.
- Grafana Cloud: free tier + scaling su metriche/log/trace.

## Task locali già disponibili
- `bootstrap-vscode-check`
- `bootstrap-vscode-install`
- `monetization-readiness`
