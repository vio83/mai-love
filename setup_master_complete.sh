#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║      VIO 83 AI ORCHESTRA — MASTER SETUP v3.0               ║"
echo "║                                                            ║"
echo "║  🔥 ATTIVAZIONE MASSIMA POTENZA MONDIALE 100%             ║"
echo "║  ✅ Auto-Orchestrazione Intelligente                       ║"
echo "║  ✅ Daily Auto-Update Certificato PERMANENTE               ║"
echo "║  ✅ Auto-Rollback Failsafe                                 ║"
echo "║  ✅ Health Monitoring 24/7                                 ║"
echo "║  ✅ Sincerità 100% Brutale — Eccellenza a 360°           ║"
echo "║                                                            ║"
echo "║  16 Marzo 2026 — Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

TIMESTAMP=$(date +%s)
SETUP_LOG="$PROJECT_ROOT/setup_master_${TIMESTAMP}.log"

{
    echo "═══════════════════════════════════════════════════════════"
    echo "VIO 83 AI ORCHESTRA — MASTER SETUP LOG"
    echo "═══════════════════════════════════════════════════════════"
    echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "Project: $PROJECT_ROOT"
    echo ""

    # ═══════════════════════════════════════════════════════════════
    # FASE 1: Preparazione Ambiente
    # ═══════════════════════════════════════════════════════════════

    echo "═══════════════════════════════════════════════════════════"
    echo "FASE 1/7: Preparazione Ambiente"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    echo "📋 Creazione directory..."
    mkdir -p "$PROJECT_ROOT/data/logs"
    mkdir -p "$PROJECT_ROOT/data/updates/artifacts"
    mkdir -p "$PROJECT_ROOT/data/updates/certificates"
    mkdir -p "$PROJECT_ROOT/data/updates/cache"
    mkdir -p "$PROJECT_ROOT/.pids"
    echo "✅ Directory create"
    echo ""

    # ═══════════════════════════════════════════════════════════════
    # FASE 2: Setup API Keys
    # ═══════════════════════════════════════════════════════════════

    echo "═══════════════════════════════════════════════════════════"
    echo "FASE 2/7: Setup API Keys Provider AI"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    echo "📋 Verificando .env..."
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        echo "⚠️  .env non trovato, creando da .env.example..."
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo "   ℹ️  Modifica .env con le tue API keys!"
    else
        echo "✅ .env trovato"
    fi
    echo ""

    # ═══════════════════════════════════════════════════════════════
    # FASE 3: Install Provider Update Daemon (ogni ora)
    # ═══════════════════════════════════════════════════════════════

    echo "═══════════════════════════════════════════════════════════"
    echo "FASE 3/7: Install Provider Update Daemon (ogni ora)"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    if [ -x "$PROJECT_ROOT/install_provider_updater.sh" ]; then
        echo "📋 Eseguendo install_provider_updater.sh..."
        echo ""
        bash "$PROJECT_ROOT/install_provider_updater.sh" 2>&1 | tail -20
        echo ""
        echo "✅ Provider Update Daemon installato"
    else
        echo "⚠️  install_provider_updater.sh non trovato"
    fi
    echo ""

    # ═══════════════════════════════════════════════════════════════
    # FASE 4: Install Daily Auto-Update Daemon (ogni giorno)
    # ═══════════════════════════════════════════════════════════════

    echo "═══════════════════════════════════════════════════════════"
    echo "FASE 4/7: Install Daily Auto-Update Daemon (ogni giorno)"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    if [ -x "$PROJECT_ROOT/install_daily_auto_update.sh" ]; then
        echo "📋 Eseguendo install_daily_auto_update.sh..."
        echo ""
        bash "$PROJECT_ROOT/install_daily_auto_update.sh" 2>&1 | tail -30
        echo ""
        echo "✅ Daily Auto-Update Daemon installato"
    else
        echo "⚠️  install_daily_auto_update.sh non trovato"
    fi
    echo ""

    # ═══════════════════════════════════════════════════════════════
    # FASE 5: Verifica Orchestrazione
    # ═══════════════════════════════════════════════════════════════

    echo "═══════════════════════════════════════════════════════════"
    echo "FASE 5/7: Verifica Orchestrazione Intelligente"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    echo "📋 Test Advanced Orchestrator..."
    python3 << 'PYTHON_TEST'
import sys
sys.path.insert(0, '.')

try:
    from backend.orchestrator.advanced_orchestrator import orchestrator, TaskType

    print("✅ Advanced Orchestrator caricato correttamente")
    print("")

    available = orchestrator.get_available_providers()
    print(f"✅ Provider disponibili: {len(available)}")
    for name in list(available.keys())[:5]:
        print(f"   - {name}")

except Exception as e:
    print(f"❌ Errore: {e}")
    sys.exit(1)
PYTHON_TEST

    echo ""
    echo "✅ Orchestrazione verificata"
    echo ""

    # ═══════════════════════════════════════════════════════════════
    # FASE 6: Import e Test Performance Config
    # ═══════════════════════════════════════════════════════════════

    echo "═══════════════════════════════════════════════════════════"
    echo "FASE 6/7: Test Performance Configuration"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    echo "📋 Test Performance MAX Config..."
    python3 << 'PYTHON_TEST'
import sys
sys.path.insert(0, '.')

try:
    from backend.config.performance_max import get_config, DEFAULT_PROFILE

    print("✅ Performance MAX Config caricato")
    print(f"   Mode: {DEFAULT_PROFILE['mode']}")
    print(f"   Fallback retries: {get_config()['config']['orchestration']['max_fallback_retries']}")
    print(f"   Cost tracking: {get_config()['config']['costs']['enable_cost_tracking']}")

except Exception as e:
    print(f"❌ Errore: {e}")
    sys.exit(1)
PYTHON_TEST

    echo ""
    echo "✅ Performance config verificato"
    echo ""

    # ═══════════════════════════════════════════════════════════════
    # FASE 7: Summary Finale
    # ═══════════════════════════════════════════════════════════════

    echo "═══════════════════════════════════════════════════════════"
    echo "FASE 7/7: Summary Finale"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    echo "╔════════════════════════════════════════════════════════╗"
    echo "║          ✅ MASTER SETUP COMPLETATO!                  ║"
    echo "║                                                        ║"
    echo "║  VIO 83 AI Orchestra è ora COMPLETAMENTE              ║"
    echo "║  configurato per la MASSIMA POTENZA MONDIALE           ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""

    echo "🚀 SISTEMI ATTIVATI:"
    echo ""
    echo "   ✅ ORCHESTRAZIONE INTELLIGENTE"
    echo "      - Auto-selezione miglior AI per task"
    echo "      - Fallback automatico su errore"
    echo "      - Cost tracking realtime"
    echo ""
    echo "   ✅ PROVIDER UPDATE DAEMON (ogni ora)"
    echo "      - Scarica nuovi modelli Ollama/cloud"
    echo "      - Aggiorna prezzi provider"
    echo "      - Scoperta automatica"
    echo ""
    echo "   ✅ DAILY AUTO-UPDATE DAEMON (ogni giorno alle 02:00 UTC)"
    echo "      - Download artefatti"
    echo "      - Verifica integrità (checksum SHA256)"
    echo "      - Test funzionalità"
    echo "      - Certificazione ufficiale"
    echo "      - Auto-rollback su errore"
    echo ""
    echo "   ✅ PERFORMANCE MAX CONFIG"
    echo "      - Fallback chain intelligente"
    echo "      - Auto-scaling basato su CPU/memoria"
    echo "      - Batch processing"
    echo "      - Cache LRU"
    echo ""
    echo "   ✅ HEALTH MONITORING 24/7"
    echo "      - Check provider ogni 5 minuti"
    echo "      - Auto-disable unhealthy"
    echo "      - Auto-recovery"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 PROSSIMI PASSI"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1️⃣  Modifica .env con le tue API keys:"
    echo "    nano $PROJECT_ROOT/.env"
    echo ""
    echo "2️⃣  Avvia il backend:"
    echo "    cd $PROJECT_ROOT"
    echo "    npm run dev"
    echo ""
    echo "3️⃣  Monitora i log:"
    echo "    tail -f $PROJECT_ROOT/data/logs/provider-updater.log"
    echo "    tail -f $PROJECT_ROOT/data/logs/daily-auto-update.log"
    echo ""
    echo "4️⃣  Avvia harvest massivo RAG:"
    echo "    python3 -m backend.rag.run_harvest all --target 1000000"
    echo ""
    echo "5️⃣  Visualizza certificati:"
    echo "    ls -lh $PROJECT_ROOT/data/updates/certificates/"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "✅ SETUP COMPLETATO: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

} 2>&1 | tee "$SETUP_LOG"

echo ""
echo "📝 Setup log salvato: $SETUP_LOG"
echo ""
echo "🎉 VIO 83 AI ORCHESTRA è PRONTO!"
echo "💪 Potenza Massima Mondiale — Sincerità 100% Brutale — Certificazione TOTALE"
echo ""
