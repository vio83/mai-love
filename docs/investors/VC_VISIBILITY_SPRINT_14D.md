# VC Visibility Sprint 14 Giorni — VIO AI Orchestra

## Obiettivo

Portare VIO AI Orchestra davanti a venture capital reali con pipeline misurabile e contatti concreti.

## KPI Sprint

- 40 invii qualificati (email/apply/LinkedIn)
- 10 risposte
- 4 call fissate
- 1 term sheet o 1 grant avanzato

## Giorno 1

- Esegui: `python3 scripts/investor/build_vc_visibility_pack.py`
- Apri: `docs/investors/vc_priority_queue.csv`
- Seleziona top 15 per score.

## Giorno 2-3

- Invia 15 email personalizzate da `docs/investors/outreach/`.
- Aggiorna CRM status a `contacted` via endpoint:
  - `PATCH /investors/{id}/status` body: `{ "status": "contacted", "last_contact": "2026-03-21" }`

## Giorno 4

- LinkedIn outreach ai partner (no spam):
  - 2 righe: traction + link repo + ask call 15 min.
- Target: CDP, Primo, P101, United.

## Giorno 5

- Applica a grant non dilutivi (priorità assoluta):
  - NLnet: [https://nlnet.nl/propose/](https://nlnet.nl/propose/)
  - NGI0: [https://nlnet.nl/NGI0/](https://nlnet.nl/NGI0/)
  - Prototype Fund: [https://prototypefund.de/en/apply/](https://prototypefund.de/en/apply/)

## Giorno 6-7

- Product Hunt prep + launch.
- Crea post LinkedIn founder con KPI e screenshot prodotto.

## Giorno 8

- Follow-up 1 sui non rispondenti.
- Cambia status in `follow_up`.

## Giorno 9-10

- Applica acceleratori:
  - YC: [https://www.ycombinator.com/apply/](https://www.ycombinator.com/apply/)
  - Techstars: [https://www.techstars.com/apply](https://www.techstars.com/apply)
  - EIT Digital: [https://www.eitdigital.eu/startup-activity/](https://www.eitdigital.eu/startup-activity/)

## Giorno 11

- Invia update pubblico: "what we built in 30 days".
- Inserisci CTA call Calendly.

## Giorno 12

- Follow-up 2 sui lead caldi.
- Cambia status in `meeting_set` quando fissata call.

## Giorno 13

- Investor update deck v2 (solo numeri).
- Aggiorna `docs/INVESTOR_PITCH_DECK_2026.md` con nuovi KPI.

## Giorno 14

- Review funnel endpoint: `GET /investors/summary/funnel`
- Decisione: round equity vs grant-first.

## Regole Brutali

- No storytelling senza numeri.
- No email generiche.
- Ogni contatto deve avere prossimo step e data follow-up.
- Nessun target senza motivo di fit (AI/open-source/dev-tools).
