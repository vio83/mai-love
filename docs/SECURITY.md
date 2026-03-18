# Security Policy — VIO 83 AI Orchestra

**Versione:** 1.0.0 | **Data:** 18 Marzo 2026

---

## Versioni supportate

| Versione | Supportata |
|----------|-----------|
| 0.9.x (beta) | ✅ Sì |
| < 0.9.0 | ❌ No — aggiorna alla versione più recente |

---

## Segnalare una vulnerabilità

**NON aprire una GitHub Issue pubblica per vulnerabilità di sicurezza.**

Invia un'email privata a: **porcu.v.83@gmail.com**

Oggetto email: `[SECURITY] VIO 83 AI Orchestra — <descrizione breve>`

### Cosa includere

- Descrizione della vulnerabilità
- Passi per riprodurla (Proof of Concept se disponibile)
- Impatto stimato (confidenzialità, integrità, disponibilità)
- Versione dell'app colpita
- Sistema operativo e configurazione

### Tempi di risposta

| Fase | Tempo |
|------|-------|
| Conferma ricezione | 48 ore |
| Valutazione iniziale | 7 giorni |
| Patch per vulnerabilità critiche | 14 giorni |
| Disclosure coordinata | 90 giorni |

---

## Architettura di sicurezza

### Local-First by Design

VIO 83 AI Orchestra è progettata con il principio **privacy-first locale**:

- Tutti i dati vengono salvati esclusivamente sul dispositivo macOS dell'utente
- Il backend API è esposto **solo su `127.0.0.1:4000`** — mai su interfacce di rete pubbliche
- Nessuna telemetria, nessun analytics remoto, nessun tracking

### Superficie d'attacco

| Componente | Esposizione | Mitigazione |
|-----------|-------------|-------------|
| FastAPI backend | `localhost:4000` only | `host=127.0.0.1`, CORS configurato |
| SQLite databases | Filesystem locale | Permessi `rw-------` |
| API keys provider cloud | `.env` locale | Non committate, non sincronizzate |
| Provider cloud (HTTPS) | API key → provider | TLS 1.2+, trust_env=False |

### Rate Limiting

- `/chat` e `/chat/stream`: **30 richieste/minuto per IP** (sliding window 60s)
- Risposta in eccesso: HTTP 429 + `Retry-After: 60`

### Admin API

Endpoint distruttivi (`DELETE /conversations`, `POST /core/cache/clear`) richiedono header di autenticazione:

```
X-Admin-Token: <valore da VIO_ADMIN_TOKEN nel .env>
```

Se `VIO_ADMIN_TOKEN` non è impostato nel `.env`, questi endpoint restituiscono **503 Service Unavailable**.

---

## Cosa NON fare (per sicurezza)

```bash
# ❌ Non esporre il backend su 0.0.0.0
uvicorn backend.server:app --host 0.0.0.0  # PERICOLOSO

# ❌ Non committare mai il file .env
git add .env  # MAI

# ❌ Non condividere API keys nei log o nei file di configurazione pubblici
VIO_ADMIN_TOKEN=mio-token-segreto  # solo in .env locale, mai su GitHub
```

---

## Dipendenze e CVE

Per controllare vulnerabilità note nelle dipendenze Python:

```bash
pip install pip-audit
pip-audit -r requirements.txt
```

Per le dipendenze Node.js:

```bash
npm audit
npm audit fix
```

---

## Crediti

Ringraziamo i ricercatori di sicurezza che segnalano vulnerabilità in modo responsabile.
I contributi di security disclosure saranno riconosciuti nel CHANGELOG (a discrezione del segnalante).

---

_Contatto sicurezza: porcu.v.83@gmail.com_
_Repository: https://github.com/vio83/vio83-ai-orchestra_
