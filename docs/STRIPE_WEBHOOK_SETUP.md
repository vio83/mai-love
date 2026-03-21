# 🪝 Setup Stripe Webhook — VIO AI Orchestra

## Opzione 1: Testing Locale (con ngrok)

### Passo 1 — Installa/avvia ngrok
```bash
# Se non hai ngrok, installa:
brew install ngrok

# Avvia tunnel sulla porta 4000 del backend
ngrok http 4000
```

Vedrai output come:
```
Forwarding                    https://xxxxx-xx-xx-xx-xx.ngrok.io -> http://localhost:4000
```

### Passo 2 — Crea endpoint webhook in Stripe
1. **Stripe Dashboard → Sviluppatori → Webhooks → Aggiungi endpoint**
2. **URL endpoint**: `https://xxxxx-xx-xx-xx-xx.ngrok.io/billing/webhook/stripe`
3. **Seleziona eventi**:
   - ✅ `checkout.session.completed`
   - ✅ `payment_intent.succeeded`
   - ✅ `charge.refunded`

4. Clicca **Aggiungi endpoint** → copia il **Webhook signing secret** (`whsec_...`)

### Passo 3 — Aggiorna il .env
```bash
# Apri .env e sostituisci:
STRIPE_WEBHOOK_SECRET=whsec_tuoWhsecDaStripe
```

### Passo 4 — Test locale
```bash
# Terminal 1: avvia backend
cd /Users/padronavio/Projects/vio83-ai-orchestra
python3 -m uvicorn backend.api.server:app --reload --port 4000

# Terminal 2: invia webhook di test
python3 scripts/stripe/test_webhook.py
```

Se vedi `✅ Risposta: 200`, il webhook funziona! 

---

## Opzione 2: Produzione (dopo il deploy)

Quando il tuo app è online su un dominio (es. `https://vio83.github.io`):

1. **Stripe Dashboard → Webhooks → Aggiungi endpoint**
2. **URL endpoint**: `https://vio83.github.io/billing/webhook/stripe`
3. Stesso processo di prima

---

## Debugging

Se il webhook fallisce:

### ❌ `Connection refused`
- Verifica che il backend stia correndo su porta 4000
- ```bash
  curl -i http://localhost:4000/health
  ```

### ❌ `Signature verification failed`
- Assicurati che `STRIPE_WEBHOOK_SECRET` nel `.env` sia **esatto**
- Non hanno spazi prima/dopo

### ❌ `400 Bad Request`
- Controlla che il payload JSON sia valido
- Vedi i log del backend su `data/logs/`

---

## Verificare il webhook in Stripe Dashboard

1. **Stripe → Webhooks → [Il tuo endpoint]**
2. Vedrai una lista di eventi inviati
3. Clicca su ciascuno per vedere:
   - Request payload
   - Response status
   - Retry log

---

## API Endpoints pronti

Una volta configurato, il backend ha:

- `POST /billing/webhook/stripe` — riceve webhooks da Stripe
- `GET /kpi/business` — vedi metriche MRR, churn, ARPU
- `GET /investors` — lista CRM investitori (opzionale, se attivato)

---

## Prossimi step

1. **[OGGI]** Setup webhook e test locale
2. **[DOMANI]** Aggiungere pulsante "Pay with Stripe" nel frontend
3. **[SETTIMANA PROSSIMA]** Sincronizza pagamenti con CRM investitori

Hai domande? Chiedi pure.
