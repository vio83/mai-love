#!/usr/bin/env bash
# Monetization technical readiness check with actionable tasks.
set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="$REPO_ROOT/data/autonomous_runtime"
mkdir -p "$OUT_DIR"

TS="$(date +%Y%m%d-%H%M%S)"
TXT_OUT="$OUT_DIR/monetization-readiness-$TS.txt"
JSON_OUT="$OUT_DIR/monetization-readiness-$TS.json"

has_env() {
  local name="$1"
  if [ -n "${!name:-}" ]; then
    echo true
  else
    echo false
  fi
}

STRIPE_SECRET=$(has_env STRIPE_SECRET_KEY)
STRIPE_WEBHOOK=$(has_env STRIPE_WEBHOOK_SECRET)
POSTHOG_KEY=$(has_env POSTHOG_API_KEY)
SENTRY_DSN=$(has_env SENTRY_DSN)

cat > "$JSON_OUT" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "billing": {
    "stripe_secret_key": $STRIPE_SECRET,
    "stripe_webhook_secret": $STRIPE_WEBHOOK
  },
  "analytics": {
    "posthog_api_key": $POSTHOG_KEY,
    "sentry_dsn": $SENTRY_DSN
  },
  "kpi_targets": {
    "activation_7d_percent": 25,
    "paid_conversion_percent": 3,
    "churn_monthly_percent_max": 6,
    "response_p95_seconds_max": 3.5
  }
}
EOF

{
  echo "MONETIZATION TECH READINESS"
  echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""
  echo "Billing"
  echo "- STRIPE_SECRET_KEY: $STRIPE_SECRET"
  echo "- STRIPE_WEBHOOK_SECRET: $STRIPE_WEBHOOK"
  echo ""
  echo "Observability/Analytics"
  echo "- POSTHOG_API_KEY: $POSTHOG_KEY"
  echo "- SENTRY_DSN: $SENTRY_DSN"
  echo ""
  echo "Next executable tasks"
  echo "1) Configure Stripe webhook endpoint in backend and save secret in .env"
  echo "2) Track events: signup_started, signup_completed, first_message_sent, upgrade_clicked"
  echo "3) Build daily KPI snapshot to data/autonomous_runtime/business-kpi.json"
  echo "4) Add churn and MRR dashboard endpoint"
  echo ""
  echo "Report JSON: $JSON_OUT"
} > "$TXT_OUT"

echo "Monetization readiness report: $TXT_OUT"
echo "Monetization readiness json:   $JSON_OUT"
