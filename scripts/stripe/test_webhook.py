#!/usr/bin/env python3
"""
Test webhooks Stripe in locale — simula un evento checkout.session.completed
"""
import json
import hmac
import hashlib
import time
import os
import requests
from datetime import datetime

# Leggi dal .env
SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_test_secret")
WEBHOOK_URL = os.getenv("STRIPE_WEBHOOK_URL", "http://localhost:4000/billing/webhook/stripe")

def create_test_event():
    """Crea un evento checkout.session.completed di test"""
    event = {
        "id": f"evt_test_{int(time.time())}",
        "object": "event",
        "api_version": "2023-10-16",
        "created": int(time.time()),
        "data": {
            "object": {
                "id": f"cs_test_{int(time.time())}",
                "object": "checkout.session",
                "after_expiration": None,
                "allow_promotion_codes": None,
                "amount_subtotal": 5000,
                "amount_total": 5000,
                "automatic_tax": {"enabled": False, "status": None},
                "billing_address_collection": None,
                "cancel_url": "https://example.com/cancel",
                "client_reference_id": "test-user-123",
                "consent": None,
                "consent_collection": None,
                "currency": "eur",
                "customer": None,
                "customer_creation": None,
                "customer_details": None,
                "expires_at": int(time.time()) + 3600,
                "livemode": False,
                "locale": "it",
                "mode": "payment",
                "payment_intent": f"pi_test_{int(time.time())}",
                "payment_link": None,
                "payment_method_collection": "if_required",
                "payment_method_types": ["card"],
                "payment_status": "paid",
                "phone_number_collection": {"enabled": False},
                "recovered_from": None,
                "status": "complete",
                "submit_type": None,
                "subscription": None,
                "success_url": "https://example.com/success",
                "total_details": {"amount_discount": 0, "amount_shipping": 0, "amount_tax": 0},
                "url": None,
            },
            "previous_attributes": None,
        },
        "livemode": False,
        "pending_webhooks": 1,
        "request": {"id": None, "mpotency_key": None},
        "type": "checkout.session.completed",
    }
    return event

def compute_signature(payload: str, secret: str) -> str:
    """Calcola la firma HMAC come Stripe"""
    # Formato: timestamp.payload
    timestamp = str(int(time.time()))
    signed_content = f"{timestamp}.{payload}"
    signature = hmac.new(
        secret.encode("utf-8"),
        signed_content.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"

def send_webhook(event: dict):
    """Invia il webhook al backend"""
    payload = json.dumps(event)
    signature = compute_signature(payload, SECRET)

    headers = {
        "Content-Type": "application/json",
        "Stripe-Signature": signature,
    }

    print(f"📤 Invio webhook a: {WEBHOOK_URL}")
    print(f"📝 Payload: {json.dumps(event, indent=2)[:200]}...")
    print(f"🔐 Signature: {signature[:50]}...")

    try:
        resp = requests.post(WEBHOOK_URL, json=event, headers=headers, timeout=5)
        print(f"\n✅ Risposta: {resp.status_code}")
        print(f"📄 Body: {resp.text[:200]}")
        return resp.status_code == 200
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERRORE: Non riesco a raggiungere {WEBHOOK_URL}")
        print("💡 Assicurati che il backend sia in esecuzione su porta 4000")
        return False
    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        return False

if __name__ == "__main__":
    print("🎵 VIO 83 AI ORCHESTRA — Stripe Webhook Test")
    print("=" * 60)
    print(f"Secret: {SECRET[:20]}...")
    print(f"URL: {WEBHOOK_URL}")
    print("=" * 60)

    # Crea evento di test
    event = create_test_event()

    # Invia
    success = send_webhook(event)

    exit(0 if success else 1)
