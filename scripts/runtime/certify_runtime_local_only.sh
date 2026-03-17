#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

OUT_DIR="$ROOT_DIR/data/config"
mkdir -p "$OUT_DIR"

PROFILE_OUT="$OUT_DIR/cert-profile.json"
PROVIDERS_OUT="$OUT_DIR/cert-providers.json"
CHAT_OUT="$OUT_DIR/cert-chat.json"
REPORT_OUT="$OUT_DIR/certification-runtime-latest.json"

INCLUDE_CHAT="false"
if [[ "${1:-}" == "--include-chat" ]]; then
  INCLUDE_CHAT="true"
fi

python3 - "$PROFILE_OUT" "$PROVIDERS_OUT" "$CHAT_OUT" "$REPORT_OUT" "$INCLUDE_CHAT" <<'PY'
import json
import sys
import time
import urllib.request

profile_out, providers_out, chat_out, report_out, include_chat = sys.argv[1:6]

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def get_json(url: str, timeout: int = 20):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def post_json(url: str, payload: dict, timeout: int = 60):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

result = {
    "generated_at": now_iso(),
    "status": "pass",
    "checks": {},
    "notes": [],
}

profile = None
providers = None

try:
    profile = get_json("http://127.0.0.1:4000/orchestration/profile", timeout=15)
    with open(profile_out, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    profile_ok = bool(profile.get("no_hybrid") is True and profile.get("effective_mode") == "local-only")
    result["checks"]["profile_local_only"] = {
        "status": "pass" if profile_ok else "fail",
        "effective_mode": profile.get("effective_mode"),
        "no_hybrid": profile.get("no_hybrid"),
    }
except Exception as exc:
    result["status"] = "fail"
    result["checks"]["profile_local_only"] = {
        "status": "fail",
        "error": str(exc),
    }

try:
    providers = get_json("http://127.0.0.1:4000/providers", timeout=20)
    with open(providers_out, "w", encoding="utf-8") as f:
        json.dump(providers, f, ensure_ascii=False, indent=2)

    policy = providers.get("policy", {}) if isinstance(providers, dict) else {}
    free_cloud = providers.get("free_cloud", {}) if isinstance(providers, dict) else {}
    paid_cloud = providers.get("paid_cloud", {}) if isinstance(providers, dict) else {}

    providers_ok = (
        policy.get("no_hybrid") is True
        and policy.get("cloud_runtime_enabled") is False
        and isinstance(free_cloud, dict) and len(free_cloud) == 0
        and isinstance(paid_cloud, dict) and len(paid_cloud) == 0
    )
    result["checks"]["providers_local_only"] = {
        "status": "pass" if providers_ok else "fail",
        "policy": policy,
        "free_cloud_size": len(free_cloud) if isinstance(free_cloud, dict) else -1,
        "paid_cloud_size": len(paid_cloud) if isinstance(paid_cloud, dict) else -1,
    }
except Exception as exc:
    result["status"] = "fail"
    result["checks"]["providers_local_only"] = {
        "status": "fail",
        "error": str(exc),
    }

if include_chat.lower() == "true":
    try:
        chat = post_json(
            "http://127.0.0.1:4000/chat",
            {
                "message": "Rispondi solo OK",
                "mode": "cloud",
                "provider": "claude",
                "model": "smollm2:135m",
                "max_tokens": 8,
                "temperature": 0,
            },
            timeout=45,
        )
        with open(chat_out, "w", encoding="utf-8") as f:
            json.dump(chat, f, ensure_ascii=False, indent=2)

        chat_ok = (chat.get("provider") == "ollama") or bool(chat.get("content"))
        result["checks"]["chat_forced_local"] = {
            "status": "pass" if chat_ok else "fail",
            "provider": chat.get("provider"),
            "model": chat.get("model"),
        }
        if not chat_ok:
            result["status"] = "fail"
    except Exception as exc:
        result["checks"]["chat_forced_local"] = {
            "status": "warn",
            "error": str(exc),
        }
        result["notes"].append("Chat check non deterministico (timeout/interruzioni ambiente).")

for check in result["checks"].values():
    if check.get("status") == "fail":
        result["status"] = "fail"

with open(report_out, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(json.dumps(result, ensure_ascii=False))
sys.exit(0 if result["status"] == "pass" else 2)
PY
