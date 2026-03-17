#!/usr/bin/env python3
"""Real Max Local Optimizer

- Benchmarks installed Ollama models on complex prompts
- Selects best local model using latency + quality proxy
- Persists best preference into .env and JSON report
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import statistics
import time
from pathlib import Path
from typing import Any
from urllib import request, error

ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / ".env"
DEFAULT_OUT = ROOT / "data" / "config" / "real-max-optimizer-report.json"
HISTORY_OUT = ROOT / "data" / "config" / "real-max-optimizer-history.json"


def _normalize_host(host: str) -> str:
    value = (host or "").strip() or "http://localhost:11434"
    if not value.startswith("http://") and not value.startswith("https://"):
        value = f"http://{value}"
    return value.rstrip("/")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def env_map() -> dict[str, str]:
    data: dict[str, str] = {}
    if not ENV_PATH.exists():
        return data
    for raw in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def write_env_updates(updates: dict[str, str]) -> None:
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    out: list[str] = []
    seen: set[str] = set()

    for raw in lines:
        s = raw.strip()
        if s and not s.startswith("#") and "=" in raw:
            key = raw.split("=", 1)[0].strip()
            if key in updates:
                out.append(f"{key}={updates[key]}")
                seen.add(key)
                continue
        out.append(raw)

    if out and out[-1].strip() != "":
        out.append("")

    for key, value in updates.items():
        if key not in seen:
            out.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def http_json(url: str, payload: dict | None = None, timeout: float = 45.0) -> dict[str, Any]:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers=headers)
    with request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ollama_tags(host: str) -> list[str]:
    try:
        data = http_json(f"{host}/api/tags")
        models = data.get("models", []) if isinstance(data, dict) else []
        return [m.get("name", "") for m in models if isinstance(m, dict) and m.get("name")]
    except Exception:
        return []


def discover_ollama_host(cli_host: str, env: dict[str, str]) -> tuple[str, list[str], list[dict[str, Any]]]:
    candidates_raw = [
        cli_host,
        os.environ.get("OLLAMA_HOST", ""),
        env.get("OLLAMA_HOST", ""),
        "http://localhost:11434",
        "http://127.0.0.1:11434",
    ]

    candidates: list[str] = []
    seen: set[str] = set()
    for raw in candidates_raw:
        host = _normalize_host(raw)
        if host in seen:
            continue
        seen.add(host)
        candidates.append(host)

    probe: list[dict[str, Any]] = []
    selected = candidates[0] if candidates else "http://localhost:11434"
    selected_models: list[str] = []

    for host in candidates:
        try:
            data = http_json(f"{host}/api/tags", timeout=8.0)
            models = data.get("models", []) if isinstance(data, dict) else []
            names = [m.get("name", "") for m in models if isinstance(m, dict) and m.get("name")]
            probe.append({"host": host, "reachable": True, "models": len(names), "error": None})
            selected = host
            selected_models = names
            return selected, selected_models, probe
        except Exception as exc:
            probe.append({"host": host, "reachable": False, "models": 0, "error": str(exc)})

    return selected, selected_models, probe


def quality_proxy(text: str) -> float:
    if not text:
        return 0.0
    score = 0.0
    length = len(text)
    score += min(25.0, length / 60.0)

    markers = ["\n- ", "\n1.", "##", "###", "```", "step", "passo", "risch", "test", "kpi", "latency"]
    score += min(30.0, sum(1 for m in markers if m.lower() in text.lower()) * 3.0)

    jargon = ["fallback", "orchestr", "benchmark", "ottim", "profilo", "error", "validation", "schema"]
    score += min(20.0, sum(1 for j in jargon if j in text.lower()) * 2.5)

    concise_penalty = 0.0
    if length < 180:
        concise_penalty = 12.0

    return max(0.0, min(100.0, score - concise_penalty))


def benchmark_model(
    host: str,
    model: str,
    prompts: list[str],
    temp: float,
    max_tokens: int,
    request_timeout: float,
) -> dict[str, Any]:
    latencies: list[int] = []
    qualities: list[float] = []
    chars: list[int] = []
    ok = 0
    errors: list[str] = []
    consecutive_failures = 0

    for prompt in prompts:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": temp, "num_predict": max_tokens},
        }
        started = time.time()
        try:
            data = http_json(f"{host}/api/chat", payload=payload, timeout=request_timeout)
            elapsed = int((time.time() - started) * 1000)
            text = data.get("message", {}).get("content", "")
            latencies.append(elapsed)
            qualities.append(quality_proxy(text))
            chars.append(len(text))
            ok += 1
            consecutive_failures = 0
        except (error.URLError, TimeoutError, Exception) as exc:
            errors.append(str(exc))
            consecutive_failures += 1
            if consecutive_failures >= 2:
                break

    total = max(1, len(prompts))
    success_rate = ok / total
    avg_latency = int(statistics.mean(latencies)) if latencies else 999999
    avg_quality = float(statistics.mean(qualities)) if qualities else 0.0
    avg_chars = int(statistics.mean(chars)) if chars else 0

    # 100 = migliore; latency più bassa => speed score più alto
    speed_score = max(0.0, min(100.0, 100.0 - (avg_latency / 40.0)))
    total_score = success_rate * 50.0 + avg_quality * 0.35 + speed_score * 0.15

    return {
        "model": model,
        "success_rate": round(success_rate, 4),
        "avg_latency_ms": avg_latency,
        "avg_quality": round(avg_quality, 2),
        "avg_chars": avg_chars,
        "speed_score": round(speed_score, 2),
        "score": round(total_score, 2),
        "errors": errors[:3],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.environ.get("OLLAMA_HOST", "http://localhost:11434"))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--write-env", action="store_true")
    parser.add_argument("--max-tokens", type=int, default=260)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--request-timeout", type=float, default=18.0)
    args = parser.parse_args()

    env = env_map()
    configured_candidates = env.get(
        "VIO_REAL_MAX_CANDIDATES",
        "qwen2.5-coder:3b,llama3.2:3b,mistral:latest,llama3:latest,gemma2:2b",
    )
    candidates = [x.strip() for x in configured_candidates.split(",") if x.strip()]

    prompts = [
        "Progetta una strategia no-hybrid local-only per orchestrare task complessi con fallback locale e KPI di affidabilità.",
        "Scrivi piano operativo tecnico per debugging ad alta criticità con priorità, test, rollback e metriche.",
        "Genera un mini design doc per pipeline automation robusta con sicurezza, osservabilità e performance.",
    ]

    requested_host = _normalize_host(args.host)
    selected_host, installed, host_probe = discover_ollama_host(requested_host, env)
    if installed:
        target_models = [m for m in candidates if m in installed] or installed[:5]
    else:
        target_models = candidates

    current_profile = (env.get("VIO_EXECUTION_PROFILE") or "real-max").strip().lower()
    current_no_hybrid = (env.get("VIO_NO_HYBRID") or "false").strip().lower() in {"1", "true", "yes", "on"}

    results: list[dict[str, Any]] = []
    for model in target_models:
        results.append(
            benchmark_model(
                selected_host,
                model,
                prompts,
                args.temperature,
                args.max_tokens,
                args.request_timeout,
            )
        )

    # Riprova una volta con localhost se host selezionato non ha prodotto successi
    # (copre casi in cui OLLAMA_HOST è impostato male o momentaneamente non raggiungibile).
    has_any_success = any((item.get("success_rate", 0.0) or 0.0) > 0 for item in results)
    if not has_any_success and selected_host != "http://localhost:11434":
        retry_host = "http://localhost:11434"
        retry_models = ollama_tags(retry_host)
        retry_targets = [m for m in candidates if m in retry_models] or (retry_models[:5] if retry_models else target_models)
        if retry_targets:
            retry_results: list[dict[str, Any]] = []
            for model in retry_targets:
                retry_results.append(
                    benchmark_model(
                        retry_host,
                        model,
                        prompts,
                        args.temperature,
                        args.max_tokens,
                        args.request_timeout,
                    )
                )
            retry_success = any((item.get("success_rate", 0.0) or 0.0) > 0 for item in retry_results)
            if retry_success:
                selected_host = retry_host
                installed = retry_models
                target_models = retry_targets
                results = retry_results

    results.sort(key=lambda r: r.get("score", 0.0), reverse=True)
    best = results[0] if results else None
    has_any_success = any((item.get("success_rate", 0.0) or 0.0) > 0 for item in results)

    report = {
        "generated_at": now_iso(),
        "status": "ok" if best and has_any_success else "degraded",
        "requested_host": requested_host,
        "host": selected_host,
        "host_candidates": [item["host"] for item in host_probe],
        "host_probe": host_probe,
        "installed_models": installed,
        "tested_models": target_models,
        "best_model": best.get("model") if best else None,
        "best_score": best.get("score") if best else 0.0,
        "profile": "real-max-local",
        "no_hybrid": True,
        "results": results,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    history = []
    if HISTORY_OUT.exists():
        try:
            history = json.loads(HISTORY_OUT.read_text(encoding="utf-8"))
            if not isinstance(history, list):
                history = []
        except Exception:
            history = []

    history.append({
        "generated_at": report["generated_at"],
        "best_model": report["best_model"],
        "best_score": report["best_score"],
        "profile": current_profile,
        "no_hybrid": current_no_hybrid,
    })
    HISTORY_OUT.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_OUT.write_text(json.dumps(history[-120:], ensure_ascii=False, indent=2), encoding="utf-8")

    if args.write_env and best and has_any_success:
        write_env_updates(
            {
                "VIO_REAL_MAX_AUTOTUNE": "true",
                "VIO_LOCAL_MODEL_PREFERENCE": best["model"],
                "VIO_REAL_MAX_LAST_OPTIMIZED_AT": report["generated_at"],
                "VIO_REAL_MAX_LAST_SCORE": str(best["score"]),
                "VIO_REAL_MAX_LAST_HOST": selected_host,
            }
        )

    print(json.dumps(report, ensure_ascii=False))
    return 0 if (best and has_any_success) else 2


if __name__ == "__main__":
    raise SystemExit(main())
