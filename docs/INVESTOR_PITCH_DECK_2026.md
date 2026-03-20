# VIO AI Orchestra — Pitch Deck Investitori
## Pre-Seed Round: €50.000 per 10-15% equity

> **Contatto**: Viorica Porcu — porcu.v.83@gmail.com
> **GitHub**: https://github.com/vio83/mai-love
> **Web**: https://vio83.github.io/vio83-ai-orchestra/
> **Data**: Marzo 2026

---

## SLIDE 1 — IL PROBLEMA (BRUTALE)

**ChatGPT, Claude, Gemini costano soldi, tracciano dati, richiedono internet.**

Ogni volta che usi un LLM cloud:
- I tuoi dati vengono inviati a server USA
- Paghi per ogni token generato
- Sei bloccato su un unico provider
- Se il servizio cade, tu cadi con lui

**Per PMI, avvocati, medici, giornalisti, developer: questo è inaccettabile.**

---

## SLIDE 2 — LA SOLUZIONE

**VIO AI Orchestra** = L'unica app che orchestra 9+ modelli AI in locale e cloud da un'unica interfaccia desktop.

```
Premi un tasto → scegli Llama3 locale (gratis, privato)
Premi un tasto → passa a GPT-4 cloud (potente, premium)
```

**Funziona ora. Su Mac, Windows, Linux. Scaricabile gratis su GitHub.**

---

## SLIDE 3 — PRODOTTO (ESISTE GIÀ)

**Stack tecnico certificato e funzionante:**

| Layer       | Tecnologia                                      |
| ----------- | ----------------------------------------------- |
| Desktop App | Tauri 2.0 (Rust) — Mac/Win/Linux                |
| Frontend    | React 18 + TypeScript + Vite                    |
| Backend     | FastAPI Python 3.14 + Uvicorn                   |
| AI Locale   | Ollama (Llama3, Mistral, DeepSeek, Gemma, Qwen) |
| AI Cloud    | GPT-4, Claude, Gemini, Groq, Grok, DeepSeek API |
| Database    | SQLite + ChromaDB (vector search)               |
| Automazione | n8n workflows integrati                         |

**Prova dal vivo**: `git clone https://github.com/vio83/mai-love && ./orchestra.sh`

---

## SLIDE 4 — MERCATO

**TAM / SAM / SOM (conservativo)**

| Segmento                | Dimensione      | Fonte            |
| ----------------------- | --------------- | ---------------- |
| Developer tools globali | $28B entro 2028 | Gartner          |
| AI desktop software     | $12B entro 2027 | IDC              |
| Open source commercial  | $50B entro 2029 | Linux Foundation |

**Nicchia immediata (SOM)**: 200.000 developer che cercano privacy-first AI tool
A €10/mese ciascuno = **€2M ARR potenziale** con 0.1% penetrazione

---

## SLIDE 5 — BUSINESS MODEL

**Modello ibrido rodato:**

| Revenue Stream                   | Status      | Target 12mo     |
| -------------------------------- | ----------- | --------------- |
| GitHub Sponsors (mensile)        | Attivo      | €500/mese       |
| Ko-fi donazioni                  | Attivo      | €200/mese       |
| Licenza commerciale (enterprise) | Da lanciare | €2.000/mese     |
| SaaS hosted (cloud version)      | Roadmap     | €5.000/mese     |
| Consulting AI su misura          | Attivo      | €1.000/progetto |

**MRR Target a 12 mesi**: €5.000/mese → **€60.000 ARR**

---

## SLIDE 6 — COMPETITIVE ADVANTAGE

**Perché VIO AI Orchestra vince:**

|                 | VIO AI Orchestra | ChatGPT Plus | LM Studio    | Ollama CLI   |
| --------------- | ---------------- | ------------ | ------------ | ------------ |
| Multi-provider  | ✅ 9+             | ❌ 1          | ❌ Local only | ❌ Local only |
| App desktop GUI | ✅                | ❌ Web        | ✅            | ❌ CLI        |
| Cloud + Local   | ✅                | ❌            | ❌            | ❌            |
| Open Source     | ✅ AGPL           | ❌            | ✅            | ✅            |
| Automazione n8n | ✅                | ❌            | ❌            | ❌            |
| Memory/Context  | ✅                | ✅            | ❌            | ❌            |
| Prezzo base     | Gratis           | $20/mese     | Gratis       | Gratis       |

**Moat**: 12 mesi di sviluppo, codice pubblico, community, brand riconoscibile.

---

## SLIDE 7 — TRACTION (ONESTA)

**Dove siamo oggi:**

- ✅ Prodotto funzionante e testato
- ✅ Codice pubblico su GitHub
- ✅ CI/CD automated (GitHub Actions)
- ✅ Backend certificato local-only
- ✅ 9 AI providers integrati
- ✅ Stripe onboarding in corso
- ✅ Licenza duale AGPL + Commercial
- ⏳ MRR: €0 → **obiettivo €500 entro 90 giorni**
- ⏳ Stars GitHub: in crescita organica

**Brutalmente onesta**: siamo in early traction. Il prodotto funziona. La revenue deve ancora scalare.

---

## SLIDE 8 — FOUNDER

**Viorica Porcu (@vio83)**

- Developer full-stack 10+ anni
- Python, TypeScript, Rust, FastAPI, React, Tauri
- Ha costruito VIO AI Orchestra **da sola, da zero, in 12 mesi**
- Conosce ogni riga del codice
- Non ha paura del lavoro duro

**Link verificabili:**
- GitHub: https://github.com/vio83
- Email: porcu.v.83@gmail.com
- Ko-fi: https://ko-fi.com/vio83_ai_orchestra_
- GitHub Sponsors: https://github.com/sponsors/vio83

**Non ha co-founder. Ha un prodotto che funziona.**

---

## SLIDE 9 — USO DEI FONDI (€50.000)

| Destinazione              | %   | Importo | Dettaglio                               |
| ------------------------- | --- | ------- | --------------------------------------- |
| Stipendio founder 12 mesi | 50% | €25.000 | Full-time development senza distrazioni |
| Infrastruttura + hosting  | 20% | €10.000 | Server, CDN, CI/CD, monitoring          |
| Marketing + community     | 20% | €10.000 | PH launch, ads, content, eventi         |
| Legale + compliance       | 10% | €5.000  | Costituzione SRL/LLC, GDPR, licenze     |

**Con €50.000 raggiungiamo break-even in 18 mesi.**

---

## SLIDE 10 — ROADMAP 12 MESI

```
Q1 2026 (APR-GIU):
  ✅ Stripe live + billing endpoints
  → Product Hunt launch
  → NLnet / Prototype Fund application
  → €500 MRR target

Q2 2026 (LUG-SET):
  → SaaS hosted version beta
  → Enterprise licensing
  → €2.000 MRR target
  → YC / Techstars application

Q3 2026 (OTT-DIC):
  → App store distribution (Mac App Store)
  → €5.000 MRR target
  → Seed round raise
  → Team: primo hire
```

---

## SLIDE 11 — PERCHÉ ORA

1. **AI è il mercato più caldo del decennio** — chiunque vuole strumenti AI
2. **Privacy diventa obbligo legale** — GDPR, AI Act EU impongono local-first
3. **Open source commercial ha vinto** — GitHub, VSCode, Linux: tutti modello AGPL+Commercial
4. **Il prodotto esiste già** — non stai finanziando un'idea, stai finanziando traction

---

## SLIDE 12 — LA RICHIESTA

> **€50.000 per 10-15% equity**
> Valutazione pre-money: €350.000
> Round: Pre-Seed / Angel

**Cosa offro in cambio:**
- Accesso al codice (già pubblico)
- Board advisor seat
- Report mensile trasparente su MRR, spese, milestone
- Exit strategy: acquisizione da player AI (target: $5-20M in 3-5 anni)

**Contattami:**
- Email: porcu.v.83@gmail.com
- GitHub: https://github.com/vio83
- Calendly: https://calendly.com/vio83

---

## APPENDICE — INVESTITORI TARGET (CRM ATTIVO)

Vedi: `data/investors/investor_crm.json`

**Priorità massima (grants non dilutivi):**
1. **NLnet Foundation** — https://nlnet.nl/propose/ — fino €50K, open source privacy
2. **NGI Zero** — https://nlnet.nl/NGI0/ — EU Horizon, AI privacy-first
3. **Prototype Fund** — https://prototypefund.de/en/apply/ — €47.5K, DE gov

**Priorità alta (VC open source):**
4. **OSS Capital** — https://oss.capital/ — specializzato COSS (Commercial Open Source)
5. **Heavybit** — https://www.heavybit.com/apply — dev tools specialist

**VC italiani:**
6. **P101** — https://www.p101.it/en/apply/ — modulo online
7. **Primo Ventures** — https://www.primomilanohub.com/
8. **United Ventures** — https://unitedventures.it/
9. **CDP Venture Capital** — https://www.cdpventuresgf.it/

**Acceleratori:**
10. **Y Combinator** — https://www.ycombinator.com/apply/ (deadline: ottobre 2026)
11. **Techstars** — https://www.techstars.com/apply
12. **EIT Digital** — https://www.eitdigital.eu/startup-activity/

**Piattaforme angel:**
13. **Wellfound** (ex AngelList) — https://wellfound.com/ — crea profilo subito

---

*Generato da VIO AI Orchestra Investment Engine — Marzo 2026*
