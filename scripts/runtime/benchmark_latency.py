#!/usr/bin/env python3
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

URL = "http://127.0.0.1:4000/chat"


def run_case(model: str, max_tokens: int) -> dict:
    payload = {
        "message": "Rispondi con la sola parola: OK",
        "mode": "cloud",
        "provr": "claude",
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 0,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter()
    with urllib.request.urlopen(req, timeout=45) as response:
        body = json.loads(response.read().decode("utf-8"))
    wall_ms = int((time.perf_counter() - started) * 1000)

    return {
        "model": model,
        "max_tokens": max_tokens,
        "wall_ms": wall_ms,
        "api_latency_ms": body.get("latency_ms"),
        "provr": body.get("provr"),
        "response_preview": (body.get("content") or "")[:80],
    }


def main() -> int:
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": [
            run_case("smollm2:135m", 64),
            run_case("qwen2.5-coder:3b", 128),
        ],
    }

    out_path = Path("data/config/perf-latency-check.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
