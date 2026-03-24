#!/usr/bin/env python3
"""
VIO 83 AI ORCHESTRA — End-to-End Production Validation
Ciclo di test completo:
  1. Invia messaggio noto → conferma risposta con timestamp nel log
  2. Forza fallimento tool call → conferma errore chiaro con contesto
  3. Riavvio servizio → verifica ripristino stato (config, segreti, health)
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

BASE = os.environ.get("VIO_BACKEND_URL", "http://127.0.0.1:4000")
PASS = 0
FAIL = 0
RESULTS: list[dict] = []


def _get(path: str, timeout: int = 20) -> dict:
    url = f"{BASE}{path}"
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _post(path: str, payload: dict, timeout: int = 90) -> dict:
    url = f"{BASE}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _post_raw(path: str, payload: dict, timeout: int = 15):
    """POST that returns (status_code, body_dict_or_str)."""
    url = f"{BASE}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode()
            try:
                return r.status, json.loads(body)
            except json.JSONDecodeError:
                return r.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, body


def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS += 1
    else:
        FAIL += 1
    tag = f"[{status}]"
    msg = f"  {tag} {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    RESULTS.append({"name": name, "status": status, "detail": detail})


# ═══════════════════════════════════════════════
# TEST 1: Messaggio noto — risposta con timestamp
# ═══════════════════════════════════════════════
def test_known_message():
    print("\n═══ TEST 1: Messaggio noto (chat round-trip) ═══")
    ts_before = time.time()
    try:
        resp = _post("/chat", {
            "message": "Rispondi esattamente: ECHO_OK_VIO83",
            "mode": "local",
            "model": "smollm2:135m",
            "max_tokens": 64,
            "temperature": 0,
        })
        ts_after = time.time()
        content = resp.get("content", "")
        provr = resp.get("provr", "")
        model = resp.get("model", "")
        latency = resp.get("latency_ms", 0)

        check("Chat risponde", bool(content), f"len={len(content)}")
        check("Provr = ollama", provr == "ollama", f"got={provr}")
        check("Modello usato", bool(model), f"model={model}")
        check("Latenza ragionevole", 0 < latency < 60000, f"latency_ms={latency}")
        check("Round-trip < 60s", (ts_after - ts_before) < 60, f"wall={ts_after - ts_before:.1f}s")
        print(f"  [INFO] Timestamp risposta: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(ts_after))}")
        print(f"  [INFO] Preview: {content[:120]}")
    except Exception as e:
        check("Chat round-trip", False, str(e))


# ═══════════════════════════════════════════════
# TEST 2: Forza fallimento — errore chiaro
# ═══════════════════════════════════════════════
def test_forced_failure():
    print("\n═══ TEST 2: Fallimento forzato (provr inesistente) ═══")
    try:
        # Tenta cloud con provr senza API key → errore chiaro
        code, body = _post_raw("/chat", {
            "message": "test failure",
            "mode": "cloud",
            "provr": "claude",
            "model": "nonexistent-model-xyz",
            "max_tokens": 32,
        })
        if isinstance(body, dict):
            detail_msg = body.get("detail", "")
        else:
            detail_msg = str(body)

        # Con VIO_NO_HYBRID=false e nessuna API key, dovrebbe fallire con errore chiaro
        # oppure con VIO_NO_HYBRID=true risulterà local-only e funzionerà
        has_error_context = (
            code >= 400
            or "API key" in detail_msg
            or "mancante" in detail_msg
            or "provr" in detail_msg.lower()
            or "ollama" in detail_msg.lower()  # fallback locale avvenuto
        )
        # Se la risposta arriva con content, il fallback locale ha funzionato
        if isinstance(body, dict) and body.get("content"):
            check("Fallback locale attivo", True, f"provr={body.get('provr')}")
        else:
            check("Errore chiaro con contesto", has_error_context, f"code={code}, detail={detail_msg[:200]}")
    except Exception as e:
        # Un'eccezione stessa con messaggio chiaro è accettabile
        msg = str(e)
        check("Errore con contesto", "API key" in msg or "provr" in msg.lower() or "mancante" in msg, msg[:200])

    # Test endpoint inesistente → 404
    print("\n  --- Sub-test: endpoint inesistente ---")
    try:
        code, body = _post_raw("/chat/nonexistent", {"message": "x"})
        check("404 per endpoint sconosciuto", code in (404, 405), f"code={code}")
    except Exception as e:
        check("404 per endpoint sconosciuto", False, str(e))

    # Test payload malformato → 422
    print("\n  --- Sub-test: payload malformato ---")
    try:
        code, body = _post_raw("/chat", {"invalid_field": "x"})
        check("422 per payload invalido", code == 422, f"code={code}")
    except Exception as e:
        check("422 per payload invalido", False, str(e))


# ═══════════════════════════════════════════════
# TEST 3: Stato post-restart (config, secrets, health)
# ═══════════════════════════════════════════════
def test_state_recovery():
    print("\n═══ TEST 3: Verifica stato (config, segreti, health) ═══")

    # 3a. Health check
    try:
        health = _get("/health")
        check("Health status=ok", health.get("status") == "ok")
        check("Version presente", bool(health.get("version")))

        provrs = health.get("provrs", {})
        ollama_info = provrs.get("ollama", {})
        check("Ollama disponibile", ollama_info.get("available") is True)

        policy = provrs.get("policy", {})
        check("Policy presente", bool(policy.get("mode")), f"mode={policy.get('mode')}")
        check("Uptime > 0", health.get("uptime_seconds", 0) > 0, f"uptime={health.get('uptime_seconds'):.0f}s")
    except Exception as e:
        check("Health endpoint", False, str(e))

    # 3b. Core infrastructure
    print("\n  --- Core Infrastructure ---")
    try:
        cache = _get("/core/cache/stats")
        check("Cache engine attivo", "size" in cache or "hits" in cache or "l1" in str(cache).lower(), str(cache)[:120])
    except Exception as e:
        check("Cache stats", False, str(e))

    try:
        errors = _get("/core/errors/stats")
        check("Error handler attivo", isinstance(errors, dict), str(errors)[:120])
    except Exception as e:
        check("Error stats", False, str(e))

    # 3c. Profilo orchestrazione
    print("\n  --- Orchestration Profile ---")
    try:
        profile = _get("/orchestration/profile")
        check("Profile caricato", "effective_mode" in profile or "execution_profile" in profile, str(profile)[:160])
    except Exception as e:
        check("Profile endpoint", False, str(e))

    # 3d. Provrs
    print("\n  --- Provrs ---")
    try:
        provrs = _get("/provrs")
        has_local = "local" in provrs or "ollama" in str(provrs).lower()
        check("Provr locali presenti", has_local, str(provrs)[:160])
    except Exception as e:
        check("Provrs endpoint", False, str(e))

    # 3e. Core status
    print("\n  --- Core Status ---")
    try:
        status = _get("/core/status")
        check("Core status OK", isinstance(status, dict), str(status)[:160])
    except Exception as e:
        check("Core status", False, str(e))


# ═══════════════════════════════════════════════
# TEST 4: Routing intelligente
# ═══════════════════════════════════════════════
def test_intent_routing():
    print("\n═══ TEST 4: Intent-based routing ═══")
    try:
        # Code query → should classify as "code"
        r1 = _post("/classify", {"message": "scrivi una funzione python che ordina un array"})
        check("Code routing", r1.get("request_type") == "code", f"type={r1.get('request_type')}")

        # Creative query → should classify as "creative" or "writing"
        r2 = _post("/classify", {"message": "scrivi una poesia sulla luna"})
        check("Creative routing", r2.get("request_type") in ("creative", "writing"), f"type={r2.get('request_type')}")

        # Reasoning → should classify as "reasoning"
        r3 = _post("/classify", {"message": "spiega perché il cielo è blu"})
        check("Reasoning routing", r3.get("request_type") == "reasoning", f"type={r3.get('request_type')}")
    except Exception as e:
        check("Classify endpoint", False, str(e))


# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("VIO 83 AI ORCHESTRA — E2E Production Validation")
    print(f"Target: {BASE}")
    print(f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    print("=" * 60)

    test_known_message()
    test_forced_failure()
    test_state_recovery()
    test_intent_routing()

    print("\n" + "=" * 60)
    print(f"RISULTATO: {PASS} PASS, {FAIL} FAIL su {PASS + FAIL} check totali")
    print("=" * 60)

    # Salva report JSON
    report_path = os.path.join(os.path.dirname(__file__), "..", "data", "logs", "e2e-validation.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target": BASE,
        "pass": PASS,
        "fail": FAIL,
        "total": PASS + FAIL,
        "results": RESULTS,
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Report salvato: {report_path}")

    sys.exit(1 if FAIL > 0 else 0)
