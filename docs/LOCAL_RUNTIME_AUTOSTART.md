T# Local Runtime Autostart — OpenClaw / LegalRoom / n8n

Questo setup rende il runtime locale più robusto e persistente:

- avvio automatico al login macOS (LaunchAgents)
- restart automatico se un servizio cade
- monitoraggio health con probe periodici
- log e stato operativo per audit

## 1) Configurazione `.env`

Nel file `.env` imposta i comandi reali:

- `OPENCLAW_START_CMD`
- `LEGALROOM_START_CMD`
- `N8N_START_CMD` (default già presente)

Esempio (adatta ai tuoi percorsi reali):

- `OPENCLAW_START_CMD=python3 /percorso/openclaw/main.py --port 4111`
- `LEGALROOM_START_CMD=python3 /percorso/legalroom/server.py --port 4222`
- `N8N_START_CMD=npx n8n start --host 127.0.0.1 --port 5678`

## 2) Avvio manuale immediato

```bash
bash scripts/runtime/start_runtime_services.sh
```

Stop:

```bash
bash scripts/runtime/stop_runtime_services.sh
```

## 3) Avvio automatico permanente (launchd)

```bash
bash install_autostart.sh
```

Questo installer configura due LaunchAgent:

- `com.vio83.ai-orchestra.plist`
- `com.vio83.runtime-services.plist` (KeepAlive=true)

## 4) Diagnostica rapida

File utili:

- `.logs/runtime-supervisor.log`
- `.logs/runtime-openclaw.log`
- `.logs/runtime-legalroom.log`
- `.logs/runtime-n8n.log`
- `.pids/runtime-supervisor-state.json`

Verifica LaunchAgents:

```bash
launchctl list | grep -E 'com.vio83.ai-orchestra|com.vio83.runtime-services'
```

## 5) Nota di trasparenza operativa

Il Health Panel diventa stabilmente verde **solo** se i processi reali dei servizi sono avviabili e rispondono sui relativi endpoint (`4111`, `4222`, `5678`).
Nessun mock/fake health viene introdotto.
