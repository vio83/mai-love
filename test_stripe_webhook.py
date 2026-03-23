#!/usr/bin/env python3
import json
import hmac
import hashlib
import subprocess
import time

# 1. Secret da .env
with open(".env") as f:
    for line in f:
        if line.startswith("STRIPE_WEBHOOK_SECRET="):
            secret = line.split("=", 1)[1].strip()
            break

# 2. Payload Stripe (test event: checkout.session.completed)
payload = {
    "id": "evt_test_123456789",
    "type": "checkout.session.completed",
    "created": int(time.time()),
    "livemode": False,
    "data": {"object": {"id": "cs_test_123", "customer": "cus_test_123"}}
}
payload_bytes = json.dumps(payload).encode("utf-8")

# 3. Signature (t=timestamp,v1=hash)
ts = str(int(time.time()))
signed_payload = f"{ts}.".encode("utf-8") + payload_bytes
sig = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
stripe_header = f"t={ts},v1={sig}"

# 4. POST al webhook
print("=== STRIPE WEBHOOK REGRESSION TEST ===")
print(f"\n🔄 Sending test event...")
print(f"   Endpoint: POST /billing/webhook/stripe")
print(f"   Event Type: {payload['type']}")
print(f"   Signature: t={ts},v1={sig[:16]}...")

import requests
try:
    resp = requests.post(
        "http://127.0.0.1:4000/billing/webhook/stripe",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "stripe-signature": stripe_header
        },
        timeout=5
    )
    print(f"\n✅ HTTP {resp.status_code}")
    print(f"   Response: {resp.json()}")
except Exception as e:
    print(f"\n❌ Error: {e}")
