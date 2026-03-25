#!/usr/bin/env bash
set -euo pipefail

payload="$(cat || true)"

python3 - <<'PY' "$payload"
import json
import re
import sys

raw = sys.argv[1] if len(sys.argv) > 1 else ""

try:
    event = json.loads(raw) if raw.strip() else {}
except Exception:
    event = {}

payload_text = raw.lower()

# Try to capture command-like fields if present in the hook payload.
tool_name = ""
for key in ("toolName", "tool_name", "tool"):
    value = event.get(key)
    if isinstance(value, str):
        tool_name = value.lower()
        break

risky_cmd_patterns = [
    r"git\s+reset\s+--hard",
    r"git\s+checkout\s+--",
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+~",
    r"sudo\s+rm\s+-rf",
]

secret_patterns = [
    r"sk-[a-z0-9]{16,}",
    r"ghp_[a-z0-9]{20,}",
    r"xox[baprs]-[a-z0-9-]{20,}",
    r"api[_-]?key\s*[:=]\s*['\"][^'\"]{8,}",
    r"authorization\s*:\s*bearer\s+[a-z0-9._-]{10,}",
]

for pattern in risky_cmd_patterns:
    if re.search(pattern, payload_text, re.IGNORECASE):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Blocked potentially destructive command pattern."
            },
            "stopReason": "Dangerous command blocked by workspace hook."
        }))
        sys.exit(0)

for pattern in secret_patterns:
    if re.search(pattern, payload_text, re.IGNORECASE):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": "Potential secret detected. Confirm intent before continuing."
            }
        }))
        sys.exit(0)

# Soft gate: ask confirmation for shell tool usage touching release critical commands.
if "terminal" in tool_name or "execute" in tool_name:
    if any(token in payload_text for token in ["tauri:build", "release:gate", "npm run build"]):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": "Release-critical command detected; confirm before running."
            }
        }))
        sys.exit(0)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": "No blocking policy matched."
    }
}))
PY
