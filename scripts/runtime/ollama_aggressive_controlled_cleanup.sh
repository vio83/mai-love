#!/usr/bin/env bash
set -euo pipefail

# Keep only the essential production-safe trio for current workflow:
# - qwen2.5-coder:3b (coding)
# - llama3.2:3b (general local chat)
# - nomic-embed-text:latest (embeddings)

KEEP_MODELS=(
  "qwen2.5-coder:3b"
  "llama3.2:3b"
  "nomic-embed-text:latest"
)

contains_keep() {
  local model="$1"
  for keep in "${KEEP_MODELS[@]}"; do
    if [[ "$model" == "$keep" ]]; then
      return 0
    fi
  done
  return 1
}

before_size_mb="$(du -sm "$HOME/.ollama/models" 2>/dev/null | awk '{print $1}')"
before_free_mb="$(df -m / | awk 'NR==2 {print $4}')"

while read -r model; do
  [[ -z "$model" ]] && continue
  if ! contains_keep "$model"; then
    ollama rm "$model" >/dev/null 2>&1 || true
  fi
done < <(ollama list | awk 'NR>1 {print $1}')

after_size_mb="$(du -sm "$HOME/.ollama/models" 2>/dev/null | awk '{print $1}')"
after_free_mb="$(df -m / | awk 'NR==2 {print $4}')"

{
  echo "BEFORE_OLLAMA_MB=$before_size_mb"
  echo "AFTER_OLLAMA_MB=$after_size_mb"
  echo "OLLAMA_MB_FREED=$((before_size_mb-after_size_mb))"
  echo "BEFORE_FREE_MB=$before_free_mb"
  echo "AFTER_FREE_MB=$after_free_mb"
  echo "FREE_MB_GAIN=$((after_free_mb-before_free_mb))"
  echo "--- MODELS_LEFT ---"
  ollama list
  echo "--- DISK ---"
  df -h /
} > /tmp/vio_ollama_cleanup_report.txt
