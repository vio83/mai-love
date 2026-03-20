# VIO + AI LOVE Readiness Masterplan 2026

## 1) CI Run Failed Zero

Obiettivo: 0 loop di rerun, 0 failure ricorsivi su Pages.

Checklist:
- [ ] Nessun gitlink orfano: `git ls-files --stage | grep '^160000'` deve restituire vuoto.
- [ ] Branch protection con required checks bloccanti.
- [ ] CI autopilot con limite rerun per run ID (circuit breaker) attivo.
- [ ] Alerting su causa (checkout/submodule/build/test) non solo su status failure.
- [ ] Runbook incidente CI in docs con azioni 5 minuti.

KPI:
- CI success rate >= 98%
- MTTR CI < 15 minuti
- Rerun manuali/settimana <= 2

## 2) Runtime & Product Engineering

Obiettivo: velocita + stabilita + cost control.

Checklist:
- [ ] Latenza p95 front->backend->provider misurata e monitorata.
- [ ] Timeouts per provider AI con fallback ordinati.
- [ ] Budget token/costo per request e per utente.
- [ ] Test regressione su prompt set fisso (golden dataset).
- [ ] Dashboard tecnica e business unica.

KPI:
- p95 total response < 3.5s (chat breve)
- Error rate backend < 1%
- Costo medio per risposta in target di margine

## 3) Mac + VS Code + Claude Desktop Stack

Obiettivo: postazione di sviluppo/operazioni pronta per release continua.

Checklist tecnica:
- [ ] Homebrew aggiornato
- [ ] Git + gh + jq + curl + wget
- [ ] Node LTS + npm aggiornato
- [ ] Python 3.14 + venv funzionante
- [ ] Rust + cargo + Tauri CLI
- [ ] Docker Desktop operativo
- [ ] Ollama attivo + modelli locali base
- [ ] LaunchAgent runtime validati

Checklist VS Code:
- [ ] Python + Pylance
- [ ] ESLint + Prettier
- [ ] GitHub Actions extension
- [ ] Error Lens
- [ ] Markdown lint + spell check

Checklist Claude Desktop / Copilot workflow:
- [ ] Prompt operativi versionati nel repo
- [ ] Regole di commit atomici enforce
- [ ] Script audit readiness giornaliero
- [ ] Script verify pre-push con gate minimi

## 4) Monetizzazione & Go-To-Market

Obiettivo: passare da progetto tecnico a business sostenibile.

Checklist:
- [ ] Pricing tiers (Free/Pro/Team/Enterprise)
- [ ] Metering usage per tenant
- [ ] Billing (Stripe) con webhook robusti
- [ ] CRM pipeline sponsor/partner
- [ ] Landing con CTA misurabili

KPI business:
- Activation 7d >= 25%
- Retention 30d >= 20%
- Conversione paid >= 3%
- Churn mensile <= 6%

## 5) Security & Compliance

Checklist:
- [ ] Secret scanning e rotation policy
- [ ] Dependency scanning bloccante in release
- [ ] SBOM e tracciabilita build
- [ ] Policy privacy + DPA enterprise

## 6) Comando operativo giornaliero

Esegui:

```bash
bash scripts/runtime/audit_readiness_2026.sh
```

Poi apri l'output in:
- `data/autonomous_runtime/readiness-audit-latest.txt`

Se qualsiasi sezione e rossa, niente nuove feature finche non torni in verde.
