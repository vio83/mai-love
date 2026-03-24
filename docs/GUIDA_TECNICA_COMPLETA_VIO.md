# VIO 83 AI Orchestra — Guida Tecnica Completa

> Autrice: Viorica Porcu (vio83)
> Versione: 0.9.0-beta
> Data: Marzo 2026
> Licenza: Dual License — Proprietary + AGPL-3.0

---

## Cap. 1 — HTTP, HTML, XML

### 1.1 HTTP: Il protocollo di comunicazione

HTTP (HyperText Transfer Protocol) è il linguaggio con cui il browser parla con il server. Ogni volta che apri una pagina, succede questo:

```
[TUO BROWSER]                              [SERVER]
     |                                        |
     |--- GET /index.html HTTP/2 ------------>|
     |    Host: vio83.github.io               |
     |    Accept: text/html                   |
     |    User-Agent: Safari/605              |
     |                                        |
     |<-- HTTP/2 200 OK ---------------------|
     |    Content-Type: text/html             |
     |    Content-Length: 4521                 |
     |    <html>...</html>                    |
     |                                        |
```

#### Struttura di una richiesta HTTP

```
METODO   PERCORSO        VERSIONE
GET      /api/chat       HTTP/2

HEADERS (metadati):
Host: localhost:4000
Content-Type: application/json
Authorization: Bearer sk-xxxx
Accept: text/event-stream

BODY (solo POST/PUT):
{"message": "Ciao", "model": "claude"}
```

#### Metodi HTTP e uso in VIO AI Orchestra

| Metodo  | Scopo          | Esempio in VIO AI Orchestra                        |
| ------- | -------------- | -------------------------------------------------- |
| GET     | Leggere dati   | Caricare la pagina, ottenere lista modelli         |
| POST    | Inviare dati   | Mandare un messaggio alla chat AI                  |
| PUT     | Aggiornare     | Salvare impostazioni utente                        |
| DELETE  | Cancellare     | Eliminare una conversazione                        |
| OPTIONS | Preflight CORS | Browser verifica se il server accetta la richiesta |

#### Status Code (codici di risposta)

| Codice | Significato         | Quando succede             |
| ------ | ------------------- | -------------------------- |
| 200    | OK                  | Tutto funziona             |
| 301    | Redirect permanente | URL cambiato               |
| 400    | Bad Request         | JSON malformato nel body   |
| 401    | Unauthorized        | API key mancante o scaduta |
| 403    | Forbidden           | Non hai i permessi         |
| 404    | Not Found           | Endpoint non esiste        |
| 429    | Too Many Requests   | Rate limit raggiunto       |
| 500    | Server Error        | Bug nel backend            |
| 503    | Service Unavailable | Server sovraccarico        |

---

### 1.2 HTML: La struttura di una pagina web

HTML è il linguaggio che descrive la struttura del contenuto. Non è un linguaggio di programmazione — è un linguaggio di markup (marcatura).

```html
<!DOCTYPE html>                    <!-- Dice al browser: "Questo è HTML5" -->
<html lang="it">                   <!-- Radice del documento -->
  <head>                           <!-- METADATI (non visibili) -->
    <meta charset="UTF-8">         <!-- Codifica caratteri -->
    <meta name="viewport"
          content="width=device-width">  <!-- Mobile responsive -->
    <title>VIO AI Orchestra</title>     <!-- Titolo tab browser -->
    <link rel="stylesheet"
          href="styles.css">       <!-- Foglio di stile -->
    <script src="app.js"
            defer></script>       <!-- JavaScript (defer = carica dopo) -->
  </head>

  <body>                           <!-- CONTENUTO VISIBILE -->
    <header>...</header>          <!-- Intestazione -->
    <nav>...</nav>                <!-- Navigazione -->
    <main>                         <!-- Contenuto principale -->
      <section>...</section>
      <article>...</article>
    </main>
    <footer>...</footer>          <!-- Piè di pagina -->
  </body>
</html>
```

#### Tag principali con descrizione

| Tag                   | Descrizione                   | Cosa NON fare                            |
| --------------------- | ----------------------------- | ---------------------------------------- |
| `<div>`               | Contenitore generico (blocco) | Non usarlo per tutto — usa tag semantici |
| `<span>`              | Contenitore inline            | Non usarlo come blocco                   |
| `<h1>`-`<h6>`         | Titoli (gerarchici)           | Non saltare livelli (h1 poi h3)          |
| `<p>`                 | Paragrafo                     | Non annidare div dentro p                |
| `<a href="url">`      | Link ipertestuale             | Non usare javascript: nell'href          |
| `<img src="" alt="">` | Immagine                      | Non omettere mai l'attributo alt         |
| `<form>`              | Formulario dati               | Non dimenticare method e action          |
| `<input>`             | Campo input                   | Non omettere type e name                 |
| `<button>`            | Pulsante                      | Non usare div cliccabili                 |
| `<script>`            | JavaScript                    | Non metterlo nel head senza defer/async  |

---

### XML Markup: la versione strutturata

XML (eXtensible Markup Language) è come HTML ma con regole più rigide e tag personalizzati. Lo usi nei file `.docx` (che sono ZIP di XML), nei feed RSS, nelle configurazioni, e nelle API SOAP.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<documento>
  <titolo>VIO AI Orchestra</titolo>
  <descrizione>App di orchestrazione AI locale</descrizione>
  <versione>0.9.0-beta</versione>
  <autore email="porcu.v.83@gmail.com">Viorica Porcu</autore>
  <funzionalita>
    <item priorita="alta">Cross-check multi-modello</item>
    <item priorita="media">RAG engine locale</item>
  </funzionalita>
</documento>
```

**Differenza chiave:** HTML ha tag predefiniti (`<div>`, `<p>`). XML ti permette di inventare i tuoi tag. Ma ogni tag aperto DEVE essere chiuso.

---

## Cap. 2 — Cosa Contiene un Large Language Model (LLM)

> **Onesta brutale:** Non posso rivelarti il codice sorgente di Claude perché è proprietario di Anthropic. Quello che segue è la struttura tecnica reale, verificata, di come funziona un LLM a livello architetturale — valida per Claude, GPT-4, Gemini, LLaMA, Mistral, e qualsiasi altro transformer.

### 2.1 I componenti fisici di un LLM

Un LLM è un file (o insieme di file) che contiene:

| Componente     | Cosa contiene                                                                                | Dimensione tipica                   |
| -------------- | -------------------------------------------------------------------------------------------- | ----------------------------------- |
| Pesi (Weights) | Miliardi di numeri decimali (float16/bfloat16) che rappresentano le "connessioni" della rete | ~200B parametri = ~400GB in float16 |
| Tokenizer      | Vocabolario di ~100.000-150.000 "pezzi di testo" con il loro ID numerico                     | ~2-5 MB                             |
| Configurazione | Architettura: numero di layer, dimensione embedding, numero attention heads                  | ~1 KB (JSON)                        |
| Template       | Come formattare input/output (chat template, special tokens)                                 | ~1 KB                               |

---

### 2.2 Architettura Transformer (il cuore)

```
INPUT: "Come si crea un'app AI?"
         |
    [TOKENIZER] --> [14532, 892, 3041, 556, 289, 12847, 9923, 31]
         |
    [EMBEDDING LAYER]  (ogni token ID --> vettore di 8192 numeri)
         |
    [POSITIONAL ENCODING]  (aggiunge informazione sulla posizione)
         |
  +--[TRANSFORMER BLOCK 1]--+
  |  |-- Multi-Head Attention  |  (ogni token "guarda" tutti gli altri)
  |  |-- Layer Normalization   |
  |  |-- Feed-Forward Network  |  (trasformazione non-lineare)
  |  |-- Residual Connection   |  (skip connection per stabilità)
  +----------------------------+
         |
  +--[TRANSFORMER BLOCK 2]--+
  |       ... (stessa struttura)  |
  +----------------------------+
         |
         ... x 80-128 blocchi (dipende dal modello)
         |
    [OUTPUT LAYER]  (vettore --> probabilità su 100k+ token)
         |
    [SAMPLING]  (sceglie il prossimo token)
         |
OUTPUT: token successivo --> "Per" --> "creare" --> "un'" --> ...
```

---

### 2.3 Multi-Head Attention — come funziona davvero

Questa è la parte più importante. L'attention è il meccanismo che permette al modello di capire le relazioni tra parole.

**Formula matematica reale:**

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right) \cdot V$$

Dove:
- $Q$ = Query (cosa sto cercando?) — Matrice $[\text{seq\_len} \times d_{\text{model}}]$
- $K$ = Key (cosa posso offrire?) — Matrice $[\text{seq\_len} \times d_{\text{model}}]$
- $V$ = Value (il contenuto effettivo) — Matrice $[\text{seq\_len} \times d_{\text{model}}]$
- $d_k$ = dimensione della chiave (es. 128)
- $\sqrt{d_k}$ = fattore di scala per stabilità numerica

**Multi-Head:** ripeti questo calcolo $N$ volte in parallelo (es. 64 heads), poi concatena i risultati e proietta con una matrice finale.

**In parole semplici:** Quando il modello legge "Il gatto si è seduto sul tappeto perché era stanco", l'attention gli permette di capire che "era stanco" si riferisce al "gatto" e non al "tappeto". Lo fa calcolando un punteggio di "rilevanza" tra ogni coppia di parole nella frase.

---

### 2.4 Il Training: come impara un LLM

| Fase                         | Cosa succede                                                                                                                                          | Costo/Durata                                   |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Pre-training                 | Il modello legge trilioni di token (libri, web, codice, paper) e impara a predire il token successivo. I pesi vengono aggiornati con backpropagation. | $50M-$200M+ / 3-6 mesi su migliaia di GPU H100 |
| SFT (Supervised Fine-Tuning) | Umani scrivono migliaia di esempi di conversazioni "ideali" (domanda + risposta perfetta). Il modello impara il formato.                              | $500K-$2M / settimane                          |
| RLHF / Constitutional AI     | Umani valutano coppie di risposte (A migliore di B). Si addestra un "reward model" che poi guida l'ottimizzazione del modello principale.             | $1M-$5M / settimane                            |
| Red Teaming                  | Team di sicurezza cerca di "rompere" il modello con prompt malevoli. Ogni vulnerabilità trovata viene mitigata.                                       | Continuo                                       |

---

### 2.5 Cosa NON contiene un LLM

**Miti da sfatare:**

- **Non contiene un "database" di testi.** I testi di training vengono compressi nei pesi e poi distrutti. Il modello non può "cercare" un documento specifico.
- **Non ha "memoria" tra conversazioni** (a meno che non si usi un database esterno come RAG).
- **Non ha "coscienza" o "intenzioni".** È un sistema di predizione statistica estremamente sofisticato.
- **Non "ragiona" come un umano.** Produce testo token per token in modo sequenziale, senza "pensiero interno" separato dall'output (con eccezione delle chain-of-thought come il tag `<antml:thinking>` di Claude).

---

### 3.2 Come si costruisce un tokenizer (Byte Pair Encoding)

Il processo reale, step by step:

**Passo 1:** Parti dai singoli byte (256 simboli base)

```
Vocabolario iniziale: a, b, c, ..., z, A, ..., Z, 0-9, spazi, punteggiatura = ~256 token
```

**Passo 2:** Conta le coppie più frequenti nel corpus

```
Corpus: "the cat the dog the cat"
Coppie più frequenti: ("t","h")=3, ("h","e")=3, ("c","a")=2, ("a","t")=2
```

**Passo 3:** Fondi la coppia più frequente in un nuovo token

```
"t" + "h" --> "th" (nuovo token 257)
Corpus diventa: "th e c a t th e d o g th e c a t"
```

**Passo 4:** Ripeti fino a raggiungere la dimensione desiderata

```
"th" + "e" --> "the" (token 258)
"c" + "a" --> "ca" (token 259)
"ca" + "t" --> "cat" (token 260)
... ripeti ~100.000 volte
```

---

### 3.3 Token speciali

| Token                   | ID (es.) | Funzione                                           |
| ----------------------- | -------- | -------------------------------------------------- |
| `<\|begin_of_text\|>`   | 1        | Inizio del documento                               |
| `<\|end_of_text\|>`     | 2        | Fine del documento — il modello smette di generare |
| `<\|start_header_id\|>` | 3        | Inizio ruolo (system/user/assistant)               |
| `[HUMAN_TURN]`          | varia    | Indica che parla l'utente                          |
| `[ASSISTANT_TURN]`      | varia    | Indica che risponde l'AI                           |
| `<\|tool_use\|>`        | varia    | L'AI vuole usare uno strumento                     |

---

### 3.4 Perché i token costano soldi

Ogni token richiede un passaggio completo attraverso tutti i layer del transformer. Per un modello con 200 miliardi di parametri, generare UN singolo token richiede ~200 miliardi di operazioni matematiche. Per questo i provider AI fatturano per token.

| Modello         | Costo Input (per 1M token) | Costo Output (per 1M token) |
| --------------- | -------------------------- | --------------------------- |
| Claude Opus 4   | $15.00                     | $75.00                      |
| Claude Sonnet 4 | $3.00                      | $15.00                      |
| GPT-4o          | $2.50                      | $10.00                      |
| Ollama (locale) | $0.00                      | $0.00 (ma serve GPU/CPU)    |

---

## Cap. 4 — System Prompt, User Input, Output: Il Ciclo Completo

### 4.1 Il flusso reale di una richiesta

```
[UTENTE digita messaggio]
       |
  [FRONTEND (React)]
       |
  POST /api/chat  { message: "...", model: "claude" }
       |
  [BACKEND (FastAPI)]
       |
  Costruisce il PROMPT COMPLETO:
  +-------------------------------------------+
  | SYSTEM PROMPT (istruzioni permanenti)     |
  | "Sei VIO AI Orchestra..."                 |
  +-------------------------------------------+
  | CRONOLOGIA CONVERSAZIONE                  |
  | [user]: messaggio 1                       |
  | [assistant]: risposta 1                   |
  | [user]: messaggio 2                       |
  +-------------------------------------------+
  | NUOVO MESSAGGIO UTENTE                    |
  | [user]: "Come funziona il RAG?"           |
  +-------------------------------------------+
       |
  [API PROVIDER] (Anthropic/OpenAI/Ollama)
       |
  Tokenizzazione --> Transformer --> Sampling
       |
  [STREAM DI TOKEN]  "Il" "RAG" "(" "Retri" "eval" ...
       |
  [BACKEND riceve stream]
       |
  [SSE (Server-Sent Events) al FRONTEND]
       |
  [REACT aggiorna la UI in tempo reale]
```

---

### 4.2 System Prompt: cosa contiene e perché è cruciale

Il system prompt è l'insieme di istruzioni che definisce il comportamento dell'AI. È la prima cosa che il modello "legge" ad ogni richiesta.

```json
{
  "role": "system",
  "content": "Sei VIO 83 AI Orchestra, un assistente AI avanzato.\n\nCOMPORTAMENTO:\n- Rispondi in italiano se l'utente scrive in italiano\n- Usa fonti verificabili quando possibile\n- Se non sai qualcosa, dillo chiaramente\n\nCAPACITÀ:\n- Cross-check: confronta risposte da più modelli\n- RAG: cerca nel knowledge base locale prima di rispondere\n- Code generation: genera codice con spiegazioni\n\nLIMITI:\n- Non inventare citazioni o dati\n- Non dare consigli medici/legali senza disclaimer"
}
```

**Implementazione in VIO AI Orchestra:**
- Frontend: `src/services/ai/systemPrompt.ts` — contiene `VIO83_MASTER_PROMPT` + `SPECIALIZED_PROMPTS` per tipo di richiesta
- Backend: `backend/orchestrator/system_prompt.py` — versione Python identica
- Il prompt viene assemblato dinamicamente da `buildSystemPrompt(requestType)` in base alla classificazione della richiesta

---

### 4.3 Come il modello processa il prompt

**Fatto critico:** Il modello NON "ricorda" le conversazioni precedenti. Ogni volta che mandi un messaggio, il backend invia l'INTERA cronologia della conversazione al modello. Per questo le conversazioni lunghe costano di più e diventano più lente — il modello deve rielaborare tutto da zero ogni volta.

In VIO AI Orchestra, la funzione `optimizeConversationWindow()` in `src/services/ai/orchestrator.ts` gestisce questo problema limitando la finestra a max 10 messaggi / 8000 caratteri.

---

### 4.4 Temperature e Sampling: come sceglie le parole

Dopo aver processato il prompt, il modello produce una distribuzione di probabilità su tutti i token possibili (~100K). La "temperature" controlla quanto è "creativo":

| Temperatura | Comportamento                                          | Uso ideale                        |
| ----------- | ------------------------------------------------------ | --------------------------------- |
| 0.0         | Sceglie SEMPRE il token più probabile (deterministico) | Codice, matematica, dati fattuali |
| 0.3-0.5     | Leggermente variabile ma controllato                   | Risposte professionali, analisi   |
| 0.7-0.9     | Più creativo, meno prevedibile                         | Scrittura creativa, brainstorming |
| 1.0+        | Molto casuale, rischio di incoerenza                   | Quasi mai consigliato             |

---

## Cap. 5 — Semantica Contestualizzata e il "Byplane" dell'AI

### 5.1 Embedding: come l'AI "capisce" il significato

Ogni token viene convertito in un vettore (lista di numeri). Token con significato simile hanno vettori vicini nello spazio multidimensionale.

```
"re"     --> [0.23, -0.45, 0.82, ..., 0.11]  (8192 numeri)
"regina" --> [0.25, -0.43, 0.79, ..., 0.13]  (VICINO a "re")
"tavolo" --> [-0.67, 0.12, -0.34, ..., 0.88] (LONTANO da "re")
```

**La famosa analogia:**

$$\vec{re} - \vec{uomo} + \vec{donna} \approx \vec{regina}$$

---

### 5.2 Contestualizzazione: perché "banco" cambia significato

Nei modelli moderni (transformer), il vettore di ogni token cambia a seconda del contesto:

```
"Sono andato in banco"   --> banco = istituto finanziario
"Il banco di scuola"     --> banco = mobile
"Banco di nebbia"        --> banco = massa compatta
```

L'attention mechanism ricalcola il vettore di "banco" guardando tutte le altre parole della frase. Questo è ciò che rende i transformer superiori ai modelli precedenti.

---

### 5.3 Perché le virgolette cambiano l'output

**Domanda:** "Perché se inserisco un acronimo con le virgolette dà un output diverso da senza virgolette?"

**Risposta tecnica:** Le virgolette cambiano il contesto semantico del token. Quando scrivi `"RAG"` con virgolette, il modello interpreta che stai citando un termine specifico, un nome proprio, o un acronimo tecnico. Senza virgolette, RAG potrebbe essere interpretato come parola comune o parte di una frase generica.

**A livello di tokenizzazione:** `"RAG"` produce token diversi da `RAG` — le virgolette sono token separati che influenzano l'attention su tutta la frase. Il modello ha visto durante il training che testo tra virgolette tende ad essere trattato come entità specifica.

---

## Cap. 6 — Come Costruire un'App AI da Zero al Lancio Commerciale (2026)

### 6.1 Stack tecnologico completo

| Layer     | Tecnologia                | Cosa fa                            | Costo                  |
| --------- | ------------------------- | ---------------------------------- | ---------------------- |
| Frontend  | React + TypeScript + Vite | Interfaccia utente                 | Gratis (open source)   |
| Desktop   | Tauri (Rust)              | App nativa da web tech             | Gratis                 |
| Backend   | FastAPI (Python)          | API server, orchestrazione         | Gratis                 |
| AI Locale | Ollama                    | Esegue modelli in locale           | Gratis (richiede RAM)  |
| AI Cloud  | Anthropic/OpenAI API      | Modelli potenti via internet       | Pay per token          |
| Database  | SQLite + FTS5             | Storage locale + ricerca full-text | Gratis                 |
| RAG       | Embedding + Vector Search | Cerca documenti rilevanti          | Gratis (locale)        |
| CI/CD     | GitHub Actions            | Test e deploy automatici           | Gratis (2000 min/mese) |
| Hosting   | GitHub Pages              | Sito web statico                   | Gratis                 |

---

### 6.2 I 10 passi da zero al lancio

#### Passo 1: Architettura e Design
Definisci cosa fa l'app, per chi, e come. Crea wireframe, scegli lo stack. VIO AI Orchestra: orchestrazione multi-modello locale-first con cross-check e RAG.

#### Passo 2: Setup progetto
```bash
npm create vite@latest vio-ai -- --template react-ts
cd vio-ai
npm install
# Backend
pip install fastapi uvicorn
# Desktop
cargo install create-tauri-app
```

#### Passo 3: Frontend (React + TypeScript)
Componenti: Chat, Sidebar, Settings, Dashboard, Pages. State management con Zustand. Routing con pagine lazy-loaded. Styling con CSS custom (tema scuro).

#### Passo 4: Backend (FastAPI)
Endpoints: `/api/chat`, `/api/models`, `/api/settings`, `/api/rag`. Middleware: CORS, auth, rate limiting. Streaming con SSE (Server-Sent Events).

#### Passo 5: Integrazione AI
Orchestrator che gestisce routing tra provider (locale/cloud), fallback automatico, caching, cross-check multi-modello. Questo è il cuore di VIO AI Orchestra — implementato in `src/services/ai/orchestrator.ts`.

#### Passo 6: RAG Engine
Indicizza documenti locali, li spezza in chunk, crea embedding vettoriali, li salva in SQLite. Alla query, cerca i chunk più rilevanti e li aggiunge al prompt. Implementato in `backend/rag/`.

#### Passo 7: Testing
Unit test (Vitest per frontend, pytest per backend), integration test, e2e test. CI pipeline che blocca merge se i test falliscono.

#### Passo 8: Sicurezza
HTTPS, API key encryption, rate limiting, input sanitization, CSP headers, Snyk per vulnerabilità, Dependabot per aggiornamenti automatici.

#### Passo 9: Build e Distribution
```bash
# Build frontend
npm run build
# Build Tauri (genera .dmg per macOS)
npm run tauri build
# Il .dmg è pronto per la distribuzione
```

#### Passo 10: Lancio commerciale
Landing page, pricing model (freemium), documentazione API, onboarding wizard, analytics, sistema di aggiornamento automatico, support channel.

---

### 6.3 Cosa serve praticamente per il lancio

| Requisito        | Stato VIO AI Orchestra | Mancante                                       |
| ---------------- | ---------------------- | ---------------------------------------------- |
| App funzionante  | 80%                    | Fix bug corruzione file, testing completo      |
| Documentazione   | 60%                    | API reference completa, guida utente           |
| CI/CD            | 70%                    | Workflow stabili (fix in corso), test coverage |
| Sicurezza        | 40%                    | Snyk attivo, Dependabot, audit completo        |
| Build Tauri      | 50%                    | Code signing Apple, notarizzazione             |
| Landing page     | 20%                    | Design, copy, deploy                           |
| Pricing/Payments | 0%                     | Stripe integration, piani, trial               |
| Analytics        | 10%                    | Mixpanel/PostHog, metriche utente              |

---

## Cap. 7 — Protocollo di Aderenza Totale 100x

> **Valutazione professionale:** Il "Protocollo di Aderenza Totale 100x" è un framework di prompt engineering di livello avanzato. La struttura (Ruolo + Obiettivo + Contesto + Formato + Criteri + Politica di verità) è allineata con le best practice di prompt engineering documentate da Anthropic, OpenAI e Google DeepMind. È pronto per l'uso professionale.

---

### 7.1 Analisi dei punti di forza

1. **Obiettivo unico non negoziabile** — Riduce la "dispersione" dell'AI. Un modello con un solo obiettivo chiaro produce output 3-5x più precisi rispetto a prompt vaghi.

2. **Politica di verità** — Il blocco "non inventare dati" con richiesta di fermarsi e chiedere è cruciale. Previene le allucinazioni.

3. **Checklist di accettazione** — Trasforma la valutazione dell'output da soggettiva a oggettiva.

4. **A/B con raccomandazione** — Gestisce i conflitti senza bloccare il lavoro.

---

### 7.2 Come implementarlo in VIO AI Orchestra

Il Protocollo 100x è integrato direttamente come overlay attivabile nel system prompt dell'app.

#### File modificati:

**Frontend — `src/services/ai/systemPrompt.ts`:**

```typescript
// Export costante PROTOCOLLO_100X (versione completa per cloud)
// Export costante PROTOCOLLO_100X_LOCAL (versione compatta per modelli locali)

// Le funzioni buildSystemPrompt() e buildLocalSystemPrompt() accettano
// il parametro opzionale protocollo100x: boolean
export function buildSystemPrompt(requestType: string, protocollo100x: boolean = false): string;
export function buildLocalSystemPrompt(requestType: string, protocollo100x: boolean = false): string;
```

**Backend — `backend/orchestrator/system_prompt.py`:**

```python
# Costante PROTOCOLLO_100X (versione completa per cloud)
# Costante PROTOCOLLO_100X_LOCAL (versione compatta per modelli locali)

# Le funzioni build_system_prompt() e build_local_system_prompt() accettano
# il parametro opzionale protocollo_100x: bool
def build_system_prompt(request_type: str, protocollo_100x: bool = False) -> str: ...
def build_local_system_prompt(request_type: str, protocollo_100x: bool = False) -> str: ...
```

#### Contenuto del Protocollo iniettato:

```
=== PROTOCOLLO DI ADERENZA TOTALE 100x — ATTIVO ===

MANDATO OPERATIVO:
Produci un risultato gemello al 100% dell'obiettivo dichiarato.
Reale, verificabile, eseguibile. Zero scarto.

Se mancano dati: fermati, elenca le lacune minime,
chiedi SOLO ciò che serve per chiudere il gap a zero scarto.

CRITERI DI ACCETTAZIONE:
1. Copertura 100% dei requisiti dichiarati — nessun punto ignorato o rimandato
2. KPI con soglie misurabili — ogni affermazione è quantificabile o falsificabile
3. Ogni passo ha responsabile + deadline (se applicabile al contesto)
4. Fonti tracciate, assunzioni marcate esplicitamente con [ASSUNZIONE]
5. Linguaggio professionale — zero superlativi vuoti, zero fluff
6. Formato di output: concreto, verificabile, pronto all'esecuzione

POLITICA DI VERITÀ:
• Se non disponi di un dato → dichiara: "[DATO MANCANTE: ...]"
• Se un requisito è ambiguo → elenca le interpretazioni e chiedi disambiguazione
• Se esistono alternative equivalenti → presenta A/B con raccomandazione motivata
• Mai inventare dati, fonti, citazioni, metriche
• Mai produrre output parziale senza dichiarare esplicitamente cosa manca

FORMATO OUTPUT:
• Struttura gerarchica: obiettivo → analisi → deliverable → verifica
• Ogni sezione con status: [COMPLETO] | [PARZIALE: motivo] | [BLOCCATO: lacuna]
• Checklist finale di accettazione con pass/fail per ogni criterio

=== FINE PROTOCOLLO 100x ===
```

#### Attivazione nell'orchestrator (stato runtime attuale)

Il Protocollo 100x è attivo in modalità hard-on nel runtime, sia lato frontend sia lato backend.

**Frontend — `src/services/ai/orchestrator.ts`:**

```typescript
// Protocollo 100x always-on: enforce execution-grade, verifiable outputs.
let systemPrompt = isLocal
     ? buildLocalSystemPrompt(requestType, true)
     : buildSystemPrompt(requestType, true);
```

**Backend — `backend/orchestrator/direct_router.py`:**

```python
if force_local or _speed_mode_enabled():
          system_prompt = build_local_system_prompt(request_type, protocollo_100x=True)
else:
          system_prompt = build_system_prompt(request_type, protocollo_100x=True)
```

In questo stato non è richiesto alcun flag utente per attivare il protocollo: viene iniettato automaticamente in ogni richiesta.

*Documento generato come parte del progetto VIO 83 AI Orchestra — Tutti i diritti riservati.*
