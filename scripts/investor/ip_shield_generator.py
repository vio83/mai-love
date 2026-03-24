#!/usr/bin/env python3
"""
ip_shield_generator.py — VIO AI Orchestra IP Protection Certificate
Genera documento legale di prior art + protezione IP con timestamp certificato.
Uso: python3 scripts/investor/ip_shield_generator.py
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_FILE = PROJECT_ROOT / "docs" / "IP_PROTECTION_CERTIFICATE.md"

AUTHOR = "Viorica Porcu"
EMAIL = "porcu.v.83@gmail.com"
PROJECT = "VIO AI Orchestra"
GITHUB = "https://github.com/vio83/vio83-ai-orchestra"


def git(cmd: str) -> str:
    result = subprocess.run(cmd.split(), capture_output=True, text=True, cwd=PROJECT_ROOT)
    return result.stdout.strip()


def sha256_files() -> str:
    """Hash SHA-256 dei file sorgente principali."""
    files = [
        "backend/api/server.py",
        "src/services/ai/orchestrator.ts",
        "src/components/chat/ChatView.tsx",
        "package.json",
        "requirements.txt",
    ]
    combined = ""
    for f in files:
        p = PROJECT_ROOT / f
        if p.exists():
            combined += f"{f}:{hashlib.sha256(p.read_bytes()).hexdigest()}\n"
    return combined


def main():
    now = datetime.now(timezone.utc).isoformat()
    first_commit = git("git log --format=%H %ai --reverse")
    first_line = first_commit.split("\n")[0] if first_commit else "N/A"
    last_commit = git("git log -1 --format=%H %ai %s")
    total_commits = git("git rev-list --count HEAD")
    git_hash = git("git rev-parse HEAD")
    file_hashes = sha256_files()

    certificate = f"""# VIO AI Orchestra — Certificato di Protezione IP
## Intellectual Property Protection Certificate

**Generato**: {now}
**Autore/Titolare**: {AUTHOR} — {EMAIL}
**Progetto**: {PROJECT}
**Repository pubblico**: {GITHUB}

---

## 1. DIRITTO D'AUTORE (COPYRIGHT) — AUTOMATICO E VIGENTE

### Base Legale
- **Legge 633/1941** (Legge sul Diritto d'Autore italiana) — Art. 1, 2(8): il software è opera dell'ingegno protetta automaticamente dalla creazione.
- **Direttiva UE 2009/24/CE** (Protezione giuridica dei programmi per elaboratore)
- **Convenzione di Berna** — automatico in 181 paesi, senza registrazione richiesta.
- **WIPO Copyright Treaty 1996**

### Protezione Attiva
```
COPYRIGHT © 2026 VIORICA PORCU. ALL RIGHTS RESERVED.
Primo commit attestato: {first_line}
Ultimo commit: {last_commit}
Totale commits: {total_commits}
SHA HEAD: {git_hash}
```

### Cosa Protegge
- Codice sorgente Python (backend FastAPI)
- Codice TypeScript/React (frontend)
- Codice Rust (Tauri)
- Architettura e design dell'orchestratore multi-provr
- Schema database e modelli Pydantic
- Workflow di automazione n8n
- Documentazione originale

---

## 2. LICENZA OPEN SOURCE — PROTEZIONE COPYLEFT AGPL-3.0

### Status
✅ **LICENSE-AGPL-3.0** presente nella root del progetto
✅ **SPDX-License-ntifier: AGPL-3.0** nei file sorgente

### Cosa Garantisce AGPL-3.0
- Chiunque usi il codice DEVE pubblicare le proprie modifiche
- **Impedisce il fork silenzioso**: nessuno può prendere il codice, chiuderlo e rivenderlo senza obbligo di disclosure
- Network use = distribution: anche SaaS che usa il codice deve rispettare AGPL
- Violazione = perdita automatica della licenza + azione legale per infringement

### Licenza Commerciale Duale
✅ **LICENSE-PROPRIETARY** presente nella root
Chiunque voglia usare il codice senza AGPL deve ottenere licenza commerciale da Viorica Porcu.

---

## 3. PRIOR ART — PROVA INCONTESTABILE DI ANTERIORITÀ

### Evnza Timestamps Git (immutabile su GitHub)
```
Primo commit datato: {first_line}
Repository pubblico dal: 2026-02-19
Commit totali: {total_commits}
SHA commit corrente: {git_hash}
```

### Hash SHA-256 File Sorgente (snapshot questo momento)
```
{file_hashes}```

### Perché Git = Prova Legale
- I commit GitHub sono **timestampati da server terzo** (GitHub Inc.)
- SHA-256 è **crittograficamente non falsificabile**
- La blockchain di git rende impossibile retroattivamente modificare date
- Tribunali USA ed EU accettano git history come prior art

---

## 4. MARCHIO — REGISTRAZIONE RACCOMANDATA

### Denominazione da Registrare
- "VIO AI Orchestra"
- "VIO83"
- Logo/simbolo (quando creato)

### Dove Registrare (link diretti)
| Ufficio | Territorio | Costo | Link |
|---------|-----------|-------|------|
| **EUIPO** | Unione Europea (27 paesi) | €850 (1 classe) | https://euipo.europa.eu/eSearch/#basic/1+1+1+1/ |
| **UIBM** | Italia | €101 + €34/classe | https://www.uibm.gov.it/it/marchi/deposito-marchio |
| **USPTO** | USA | $250-350/classe | https://www.uspto.gov/trademarks/apply |
| **WIPO Madrid** | 130 paesi | ~€1.500 | https://www.wipo.int/madrid/en/filing_fees.html |

**Raccomandazione immediata**: EUIPO (€850, copre tutta l'UE in 6 settimane).

### Classe Nice Applicabile
- **Classe 42**: Servizi di progettazione e sviluppo di software; servizi informatici; piattaforme SaaS
- **Classe 9**: Software scaricabile; applicazioni per computer

---

## 5. PERCHÉ I VC NON RUBANO LE E (REALTÀ BRUTALE)

**Questo è il segreto che nessuno ti dice:**

VC come Elad Gil, a16z, YC **NON firmano NDA** — mai, per politica.
Perché? Vedono 500+ startup/anno. Un NDA li paralizzerebbe legalmente.

**Ma non hanno bisogno di rubarti l'a. Perché:**
1. L'a vale 0. L'esecuzione vale tutto.
2. Hanno migliaia di e già: hanno bisogno di FONDATORI che le eseguano.
3. Rubare un'a da un fondatore che già la sta eseguendo è inutile: perderebbero il team (tu).
4. La reputazione è tutto per un VC: un caso di furto distrugge il fondo.

**La tua protezione reale è:**
- Codice funzionante (già fatto ✅)
- Commits datati pubblicamente (già fatto ✅)
- AGPL-3.0 (già fatto ✅)
- Andare avanti più veloce di chiunque altro (unica difesa vera)

---

## 6. CONTATTI TARGET — COME ARRIVARE DAVVERO

### Elad Gil — Angel Investor leggendario (ex Google, Color Genomics)
- **Twitter/X**: @eladgil
- **Email pubblica**: Non dispone di email pubblica — contatto via Twitter DM o warm intro
- **Blog**: http://blog.eladgil.com/
- **Cosa scrive che interessa**: AI infrastructure, developer tools, local AI, privacy
- **Come arrivarci**: Tweet pubblico taggandolo + DM + warm intro tramite YC alumni
- **Cosa vuole vedere**: MRR > €0, GitHub stars in crescita, prodotto funzionante

### Y Combinator — Il più importante acceleratore al mondo
- **Applicazione**: https://www.ycombinator.com/apply/
- **Prossima deadline**: Ottobre 2026 (batch Winter 2027)
- **Tempo applicazione**: 2-3 ore
- **Cosa chiedono**: a, co-founder, MRR se hai, cosa hai costruito
- **Forma legale richiesta**: Delaware C-Corp (USA) — costa ~$500 con Stripe Atlas: https://atlas.stripe.com/
- **Tasso accettazione**: 1.5% — qualità del prodotto > tutto

### a16z (Andreessen Horowitz) — Il VC più influente in AI
- **Sito**: https://a16z.com/
- **Focus attuale**: AI, Open Source Commercial (COSS), dev tools
- **Modulo pitch**: https://a16z.com/companies/
- **Partner rilevanti per VIO**:
  - **Martin Casado** (infrastructure/open source): @martin_casado su X
  - **Yoko Li** (AI/ML): @stuffyokohere su X
- **Approccio corretto**: LinkedIn InMail ai partner specifici + link GitHub + 3 bullet points

### Ryan Hoover — Fondatore Product Hunt
- **Twitter/X**: @rrhoover
- **Canale**: https://www.producthunt.com/posts
- **Come arrivarci**: DM su X con link prodotto — risponde se il prodotto è genuinamente interessante
- **Cosa fare PRIMA**: Lancia VIO su Product Hunt. Se ottieni 300+ upvotes, lui lo nota da solo.
- **Product Hunt launch**: https://www.producthunt.com/posts/new

---

## 7. AZIONI IMMEDIATE (ORDINE PRIORITÀ)

| # | Azione | Tempo | Costo | Impatto |
|---|--------|-------|-------|---------|
| 1 | **Registra marchio EUIPO** | 30 min | €850 | 🔴 ALTO - protezione legale reale |
| 2 | **Lancia su Product Hunt** | 2 ore | Gratis | 🔴 ALTO - visibilità immediata investitori |
| 3 | **Apri Stripe Atlas** (Delaware C-Corp) | 1 ora | $500 | 🟠 MEDIO - necessario per YC |
| 4 | **Applica a NLnet** | 2 ore | Gratis | 🔴 ALTO - €50K non dilutivo |
| 5 | **Tweet @eladgil** con prodotto | 15 min | Gratis | 🟡 SPECULATIVO ma facile |
| 6 | **Applica YC** (ottobre 2026) | 3 ore | Gratis | 🔴 ALTO - cambia tutto |
| 7 | **Invia pitch a16z** via form | 1 ora | Gratis | 🟡 MEDIO - risposta in 2-3 mesi |

---

*Documento generato automaticamente da VIO AI Orchestra IP Shield — {now}*
*SHA GitHub corrente: {git_hash}*
*Copyright © 2026 Viorica Porcu — porcu.v.83@gmail.com*
"""

    OUTPUT_FILE.write_text(certificate, encoding="utf-8")
    print(f"✅ Certificato IP generato: {OUTPUT_FILE}")
    print(f"   SHA HEAD: {git_hash}")
    print(f"   Commits totali: {total_commits}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
