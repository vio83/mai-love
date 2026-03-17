#!/usr/bin/env python3
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

URL = "http://127.0.0.1:4000/chat/stream"


def run_case(model: str, max_tokens: int) -> dict:
    payload = {
        "message": "Rispondi con la sola parola: OK",
        "mode": "cloud",
        "provider": "claude",
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 0,
    }

    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter()
    first_token_ms: int | None = None
    api_latency_ms: int | None = None
    output_preview = ""

    with urllib.request.urlopen(req, timeout=120) as response:
        for raw in response:
            line = raw.decode("utf-8", errors="ignore").strip()
            if not line.startswith("data: "):
                continue

            try:
                event = json.loads(line[6:])
            except json.JSONDecodeError:
                continue

            token = event.get("token")
            if token and first_token_ms is None:
                first_token_ms = int((time.perf_counter() - started) * 1000)

            if token and len(output_preview) < 80:
                output_preview += token

            if event.get("done"):
                api_latency_ms = event.get("latency_ms")
                break

    wall_ms = int((time.perf_counter() - started) * 1000)

    return {
        "model": model,
        "max_tokens": max_tokens,
        "first_token_ms": first_token_ms,
        "wall_ms": wall_ms,
        "api_latency_ms": api_latency_ms,
        "response_preview": output_preview[:80],
    }


def main() -> int:
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": [
            run_case("smollm2:135m", 64),
            run_case("qwen2.5-coder:3b", 128),
        ],
    }

    out_path = Path("data/config/perf-stream-latency-check.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())