#!/bin/bash
# ============================================================
# VIO 83 AI ORCHESTRA — Setup Provider AI Gratuiti + Economici
# Questo script ti guida a ottenere ALL le API keys necessarie
# per la massima potenza mondiale di tutti gli AI provider
# Data: 16 Marzo 2026
# ============================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  VIO 83 AI ORCHESTRA — Setup AI Providers                  ║"
echo "║  Attivazione MASSIMA POTENZA MONDIALE — 100% Eccellenza   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Backup .env
if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%s)"
    echo "✅ Backup .env creato"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🟡 CLOUD GRATUITI (API key GRATIS con limiti GENEROSI)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. GROQ (già presente)
echo "1️⃣  GROQ - Già configurata ✅"
echo "   • 14,400 richieste/giorno GRATIS"
echo "   • Llama 3.3 70B (velocissimo)"
echo "   • https://console.groq.com/keys"
echo ""

# 2. TOGETHER AI
echo "2️⃣  TOGETHER AI — API key gratis?"
echo "   • \$1 credito gratis alla registrazione"
echo "   • Llama 3.3 70B, DeepSeek R1 (50+ modelli)"
echo "   • https://api.together.xyz/settings/api-keys"
echo ""
read -p "Hai la chiave Together AI? (incolla qui o premi Enter per skip): " together_key
if [ -n "$together_key" ]; then
    sed -i '' "s/TOGETHER_API_KEY=.*/TOGETHER_API_KEY=$together_key/" "$ENV_FILE"
    echo "   ✅ TOGETHER_API_KEY configurata"
else
    echo "   ⏭️  Salta (puoi aggiungere dopo)"
fi
echo ""

# 3. OPENROUTER
echo "3️⃣  OPENROUTER — API key gratis?"
echo "   • Modelli gratuiti ILLIMITATI"
echo "   • Free Llama 3.3 70B, DeepSeek R1, Gemma 2"
echo "   • + \$1 credito bonus"
echo "   • https://openrouter.ai/keys"
echo ""
read -p "Hai la chiave OpenRouter? (incolla qui o premi Enter per skip): " openrouter_key
if [ -n "$openrouter_key" ]; then
    sed -i '' "s/OPENROUTER_API_KEY=.*/OPENROUTER_API_KEY=$openrouter_key/" "$ENV_FILE"
    echo "   ✅ OPENROUTER_API_KEY configurata"
else
    echo "   ⏭️  Salta (puoi aggiungere dopo)"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🟠 CLOUD ECONOMICI (< \$1 per 1M token)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 4. DEEPSEEK
echo "4️⃣  DEEPSEEK — Economicissimo"
echo "   • \$0.27 per 1M token INPUT (il più cheap)"
echo "   • DeepSeek R1 (migliore reasoning/math)"
echo "   • DeepSeek Chat V3"
echo "   • https://platform.deepseek.com/api_keys"
echo ""
read -p "Hai la chiave DeepSeek? (incolla qui o premi Enter per skip): " deepseek_key
if [ -n "$deepseek_key" ]; then
    sed -i '' "s/DEEPSEEK_API_KEY=.*/DEEPSEEK_API_KEY=$deepseek_key/" "$ENV_FILE"
    echo "   ✅ DEEPSEEK_API_KEY configurata"
else
    echo "   ⏭️  Salta (puoi aggiungere dopo)"
fi
echo ""

# 5. MISTRAL
echo "5️⃣  MISTRAL — Miglior cost/performance"
echo "   • \$0.20 per 1M token INPUT"
echo "   • Mistral Large (multilingual, code)"
echo "   • Mistral Small (veloce, economico)"
echo "   • https://console.mistral.ai/api-keys/"
echo ""
read -p "Hai la chiave Mistral? (incolla qui o premi Enter per skip): " mistral_key
if [ -n "$mistral_key" ]; then
    sed -i '' "s/MISTRAL_API_KEY=.*/MISTRAL_API_KEY=$mistral_key/" "$ENV_FILE"
    echo "   ✅ MISTRAL_API_KEY configurata"
else
    echo "   ⏭️  Salta (puoi aggiungere dopo)"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔴 CLOUD PREMIUM (Già configurate: Claude, GPT-4, Gemini)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 6. xAI GROK
echo "6️⃣  xAI GROK — Realtime + News"
echo "   • Grok 4 (2M context, realtime)"
echo "   • Migliore per web search"
echo "   • https://console.x.ai/"
echo ""
read -p "Hai la chiave xAI? (incolla qui o premi Enter per skip): " xai_key
if [ -n "$xai_key" ]; then
    sed -i '' "s/XAI_API_KEY=.*/XAI_API_KEY=$xai_key/" "$ENV_FILE"
    echo "   ✅ XAI_API_KEY configurata"
else
    echo "   ⏭️  Salta (puoi aggiungere dopo)"
fi
echo ""

# 7. PERPLEXITY
echo "7️⃣  PERPLEXITY — Deep Research Agent"
echo "   • Perplexity Pro Search"
echo "   • Deep Research (multi-step web search)"
echo "   • Migliore per ricerca profonda"
echo "   • https://console.perplexity.ai/"
echo ""
read -p "Hai la chiave Perplexity? (incolla qui o premi Enter per skip): " perplexity_key
if [ -n "$perplexity_key" ]; then
    sed -i '' "s/PERPLEXITY_API_KEY=.*/PERPLEXITY_API_KEY=$perplexity_key/" "$ENV_FILE"
    echo "   ✅ PERPLEXITY_API_KEY configurata"
else
    echo "   ⏭️  Salta (puoi aggiungere dopo)"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SETUP COMPLETATO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Provider attuali in .env:"
echo ""
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('$ENV_FILE')

providers = {
    'GROQ_API_KEY': '🟢 Groq',
    'TOGETHER_API_KEY': '🟡 Together AI',
    'OPENROUTER_API_KEY': '🟡 OpenRouter',
    'DEEPSEEK_API_KEY': '🟠 DeepSeek',
    'MISTRAL_API_KEY': '🟠 Mistral',
    'ANTHROPIC_API_KEY': '🔴 Claude',
    'OPENAI_API_KEY': '🔴 GPT-4',
    'GEMINI_API_KEY': '🔴 Gemini',
    'XAI_API_KEY': '🔴 xAI Grok',
    'PERPLEXITY_API_KEY': '🔴 Perplexity',
}

for env_key, name in providers.items():
    val = os.environ.get(env_key, '')
    status = '✅' if val and val.strip() and not val.startswith('sk') and len(val) > 10 else '❌'
    print(f'{status} {name}')
"
echo ""
echo "🚀 Prossimo passo: npm run dev"
echo ""
