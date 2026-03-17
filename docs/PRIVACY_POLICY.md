# Privacy Policy — VIO 83 AI Orchestra
**Versione:** 1.0.0 | **Data:** 18 Marzo 2026 | **Autrice:** Viorica Porcu

---

## 1. Titolare del Trattamento

**Viorica Porcu** — porcu.v.83@gmail.com — https://github.com/vio83

---

## 2. Principio Base — Local-First

VIO 83 AI Orchestra è **local-first**: tutti i dati vengono salvati **esclusivamente sul dispositivo dell'utente** (Mac), in database SQLite locali. Nessun dato viene inviato a server di proprietà del progetto.

---

## 3. Dati Raccolti Localmente

| Dato | File | Scopo | Durata |
|------|------|-------|--------|
| Messaggi delle conversazioni | `data/vio83_orchestra.db` | Storico chat | Fino a cancellazione |
| Preferenze app | `data/vio83_orchestra.db` | Configurazione | Permanente |
| Metriche uso aggregate | `data/vio83_orchestra.db` | Statistiche locali | 90 giorni |
| Log di processo | `data/process_log.db` | Diagnostica | 7 giorni (rotazione auto) |
| Cache risposte AI | `data/cache.db` | Performance | TTL configurabile |
| Knowledge base | `data/knowledge_distilled.db` | RAG Engine | Fino a cancellazione |

**Non raccogliamo mai:** telemetria anonima, tracciamento comportamentale, cookie, fingerprinting.

---

## 4. Trasmissione a Provider AI (solo se configurati dall'utente)

Quando l'utente inserisce una API key di un provider cloud e invia un messaggio, **il testo viene trasmesso direttamente al provider scelto via HTTPS**. Si applicano le policy del provider:

| Provider | Privacy Policy |
|----------|----------------|
| Anthropic (Claude) | https://www.anthropic.com/privacy |
| OpenAI (GPT-4) | https://openai.com/policies/privacy-policy |
| Google (Gemini) | https://policies.google.com/privacy |
| Groq | https://groq.com/privacy-policy/ |
| Mistral AI | https://mistral.ai/privacy-policy/ |
| DeepSeek | https://www.deepseek.com/privacy |
| xAI (Grok) | https://x.ai/legal/privacy-policy |

La modalità **Ollama locale** non trasmette nulla fuori dal dispositivo.

---

## 5. Base Giuridica GDPR (Art. 6)

- **Art. 6(1)(b)** — esecuzione del contratto di licenza software
- **Art. 6(1)(f)** — legittimo interesse per il miglioramento delle performance tramite cache locale

---

## 6. Diritti dell'Utente (GDPR Art. 15-22)

| Diritto | Come esercitarlo |
|---------|-----------------|
| Accesso | Apri i file `.db` in `data/` con DB Browser for SQLite |
| Cancellazione | Elimina i file in `data/` o usa il tasto "Cancella tutto" in Impostazioni |
| Portabilità | Esporta le conversazioni dalla sezione Analytics |
| Opposizione | Disattiva cache: `VIO_CACHE_ENABLED=false` in `.env` |
| Rettifica | Modifica direttamente il database locale |

Contatto per esercizio diritti: **porcu.v.83@gmail.com**

---

## 7. Sicurezza dei Dati

- Database accessibili solo dall'utente macOS loggato (permessi `rw-------`)
- API keys in chiaro nel `.env` locale — **non condividere mai questo file**
- Backend API (porta 4000) accessibile solo da `localhost` per default
- Comunicazioni cloud via HTTPS con TLS 1.2+

---

## 8. Minori

L'applicazione non è destinata a utenti sotto i 18 anni.

---

## 9. Modifiche

Le modifiche saranno pubblicate su GitHub con data aggiornata nel frontmatter.
Repository: https://github.com/vio83/vio83-ai-orchestra

---

_Contatti: porcu.v.83@gmail.com_

## 1) Data processed locally

VIO 83 AI Orchestra is local-first:

- Conversations are stored in local SQLite databases under `data/`.
- Runtime diagnostics and metrics are stored locally.
- Optional cloud providers are used only if the user configures API keys.

## 2) Cloud providers (optional)

If you enable a cloud provider, your prompt/response data can be sent to that provider according to its own terms and policy.

## 3) User control

Users can:

- Delete local conversations.
- Disable cloud mode and use local-only mode.
- Disable analytics opt-in in app settings.

## 4) Legal basis (EU/GDPR)

For EU users, local processing is based on user consent and legitimate use of the software. Optional cloud processing requires explicit user action (API key setup and provider selection).

## 5) Contact

Project owner: Viorica Porcu (vio83)
GitHub: https://github.com/vio83/vio83-ai-orchestra
Email: porcu.v.83@gmail.com
