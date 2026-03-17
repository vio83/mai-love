# VIO 83 AI Orchestra — Release Profile

> Criteri oggettivi per ogni stadio di release. Niente marketing — solo gate misurabili.

---

## Alpha Pubblica

**Target audience:** developer e early adopter che accettano bug noti.

| Gate | Criterio | Stato |
|------|----------|-------|
| TypeScript compila | `npx tsc --noEmit` exit 0 | ✅ |
| ESLint verde | `npm run lint` (0 errori, 0 warning) | ✅ |
| Frontend build | `npm run build` exit 0 | ✅ |
| Backend compila | `python -m compileall -q backend/` | ✅ |
| Unit test frontend | `npm run test:frontend` 5/5 pass | ✅ |
| Unit test backend | `python -m unittest discover -s tests/backend` 3/3 pass | ✅ |
| Chat streaming funziona | Ollama risponde via SSE su localhost:4000 | ✅ |
| Knowledge Base attivata | `/kb/stats` restituisce dati (FTS5 fallback) | ✅ |
| README allineato | Nessuna affermazione cloud/multi-provider come fatto runtime | ✅ |
| Bug noti documentati | File KNOWN_ISSUES.md o issue tracker aggiornato | ⬜ |

**Release tag:** `v0.x.y-alpha`

---

## Beta Tecnica

**Target audience:** utenti tecnici che vogliono usarlo quotidianamente.

| Gate | Criterio | Stato |
|------|----------|-------|
| Tutti i gate Alpha | — | ⬜ |
| Tauri build macOS | `cargo check` in CI + `npm run tauri:build` locale | ⬜ |
| E2E smoke test | `scripts/ci/backend_smoke.sh` verde in CI | ⬜ |
| Cross-check locale | Due modelli Ollama concordano/discordano correttamente | ⬜ |
| KB con dati reali | Almeno 100 documenti indicizzati in FTS5 | ⬜ |
| Performance baseline | Latenza media < 3s per risposta breve su M1 8GB | ⬜ |
| Zero regressioni | Nessun test fallito dopo merge di nuove feature | ⬜ |
| Docs utente | README + QUICK_START attuali e testati su macchina pulita | ⬜ |

**Release tag:** `v0.x.y-beta`

---

## Release Candidate (RC)

**Target audience:** chiunque voglia provare la versione "quasi finale".

| Gate | Criterio | Stato |
|------|----------|-------|
| Tutti i gate Beta | — | ⬜ |
| CI verde su PR + main | Frontend + Backend + Tauri check in GitHub Actions | ⬜ |
| Test coverage > 60% | Misurato con vitest --coverage e coverage.py | ⬜ |
| Accessibilità base | Label ARIA su controlli interattivi principali | ⬜ |
| Changelog | CHANGELOG.md con tutte le modifiche dalla beta | ⬜ |
| Security audit | Nessuna dipendenza con CVE critica (`npm audit --audit-level=high`) | ⬜ |
| Nessun `any` residuo | Zero `@typescript-eslint/no-explicit-any` nel lint | ⬜ |

**Release tag:** `v1.0.0-rc.1`

---

## Commerciale (v1.0)

**Target audience:** utenti finali, sponsor, potenziali clienti.

| Gate | Criterio | Stato |
|------|----------|-------|
| Tutti i gate RC | — | ⬜ |
| Tauri build firmato | Code signing + notarizzazione macOS | ⬜ |
| Zero telemetria | Audit confermato: nessuna chiamata di rete non richiesta | ⬜ |
| Licenza chiara | AGPL-3.0 community + licenza proprietaria commerciale | ✅ |
| Landing page | GitHub Pages con info onesta e download link | ⬜ |
| Sponsor tier attivi | GitHub Sponsors + Ko-fi configurati e pubblicati | ✅ |
| User guide | Guida completa con screenshot aggiornati | ⬜ |

**Release tag:** `v1.0.0`

---

## Note

- I gate sono **bloccanti**: non si passa al livello successivo finché tutti i gate precedenti sono verdi.
- Lo stato viene aggiornato manualmente in questo documento dopo ogni sessione di sviluppo.
- Il cloud routing potrà essere abilitato in una release futura come feature opt-in, ma non è necessario per v1.0.
