#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
🔐 API Key Rotation Checklist (immediata)

1) Revoca/Disable vecchie key nei provider:
   - Anthropic: https://console.anthropic.com/settings/keys
   - OpenAI: https://platform.openai.com/api-keys
   - Google Gemini: https://aistudio.google.com/apikey
   - Groq: https://console.groq.com/keys
   - DeepSeek: https://platform.deepseek.com/api_keys
   - Mistral: https://console.mistral.ai/api-keys/

2) Crea nuove key con scope minimo necessario.
3) Aggiorna SOLO il file locale .env (mai in repo pubblico).
4) Riavvia servizi app (backend/frontend) per rileggere env.

Comandi rapidi consigliati:
  ./scripts/security/rotate_api_keys_checklist.sh
  ./scripts/sponsor/run_weekly_content_engine.sh
EOF

if command -v open >/dev/null 2>&1; then
  open "https://console.anthropic.com/settings/keys"
  open "https://platform.openai.com/api-keys"
  open "https://aistudio.google.com/apikey"
  open "https://console.groq.com/keys"
  open "https://platform.deepseek.com/api_keys"
  open "https://console.mistral.ai/api-keys/"
fi
