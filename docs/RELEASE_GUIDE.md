# Guida al Release — VIO 83 AI Orchestra

**Data:** 18 Marzo 2026 | **Maintainer:** Viorica Porcu

Questa guida descrive il processo completo per firmare, notarizzare e distribuire VIO 83 AI Orchestra su macOS.

---

## Prerequisiti

### 1. Apple Developer Program ($99/anno)

Registrati su [developer.apple.com](https://developer.apple.com/programs/enroll/).
Necessario per:
- Firma del codice con certificato Developer ID
- Notarizzazione Apple (richiesta per macOS Gatekeeper dal 2019)
- Distribuzione fuori dal Mac App Store

### 2. Certificati necessari

Nel tuo account Apple Developer, crea:
- **Developer ID Application** — firma l'app (.app)
- **Developer ID Installer** — firma i .pkg (opzionale)

Scarica ed installa il certificato nel tuo portachiavi macOS.

### 3. App-specific password

Su [appleid.apple.com](https://appleid.apple.com) → Security → Generate Password.
Usa questa password per la notarizzazione (`APPLE_PASSWORD`).

---

## Setup una-tantum sul Mac

### Step 1: Genera le chiavi Tauri Updater

```bash
# Esegui UNA VOLTA sola
chmod +x scripts/generate-updater-keys.sh
./scripts/generate-updater-keys.sh
```

Questo script:
1. Genera la coppia di chiavi minisign in `.tauri-keys/`
2. Aggiorna automaticamente `src-tauri/tauri.conf.json` con la chiave pubblica
3. Fornisce istruzioni per i GitHub Secrets

### Step 2: Configura le variabili d'ambiente (`.env.release`)

Crea il file `.env.release` (non committare mai!):

```bash
# Apple Developer
APPLE_ID=tua@email.com
APPLE_TEAM_ID=XXXXXXXXXX
APPLE_PASSWORD=xxxx-xxxx-xxxx-xxxx
APPLE_CERTIFICATE="base64 del .p12"
APPLE_CERTIFICATE_PASSWORD=password-del-certificato

# Tauri Updater
TAURI_PRIVATE_KEY=$(cat .tauri-keys/vio83-updater)
TAURI_KEY_PASSWORD=password-inserita-durante-generazione
```

### Step 3: Aggiungi i GitHub Secrets

In GitHub → Repository → Settings → Secrets and variables → Actions:

| Secret | Valore |
|--------|--------|
| `TAURI_PRIVATE_KEY` | contenuto di `.tauri-keys/vio83-updater` |
| `TAURI_KEY_PASSWORD` | password inserita alla generazione |
| `APPLE_ID` | tua email Apple Developer |
| `APPLE_PASSWORD` | app-specific password |
| `APPLE_TEAM_ID` | Team ID (10 caratteri) |
| `APPLE_CERTIFICATE` | base64 del certificato .p12 |
| `APPLE_CERTIFICATE_PASSWORD` | password del .p12 |
| `KEYCHAIN_PASSWORD` | password casuale per il keychain CI |

---

## Processo di Release

### Release automatico (raccomandato)

```bash
# 1. Aggiorna versione in tutti i file necessari
./scripts/bump-version.sh 0.9.0

# 2. Aggiorna CHANGELOG.md
# (aggiungi sezione ## [0.9.0] con le novità)

# 3. Commit e tag
git add -A
git commit -m "chore(release): v0.9.0-beta"
git tag v0.9.0-beta
git push origin main --tags

# 4. GitHub Actions si attiva automaticamente:
# → Compila Tauri (universal macOS: arm64 + x86_64)
# → Firma con Developer ID
# → Notarizza con Apple
# → Crea GitHub Release con .dmg e latest.json
# → L'auto-updater nell'app trova il nuovo release
```

### Release manuale (locale)

```bash
# Carica le variabili
source .env.release

# Build universale firmato
npm run tauri build -- \
  --target universal-apple-darwin

# Il .dmg firmato è in:
# src-tauri/target/universal-apple-darwin/release/bundle/dmg/

# Verifica firma
codesign --verify --deep --strict \
  "src-tauri/target/universal-apple-darwin/release/bundle/macos/VIO 83 AI Orchestra.app"

# Verifica notarizzazione
spctl --assess --type exec \
  "src-tauri/target/universal-apple-darwin/release/bundle/macos/VIO 83 AI Orchestra.app"
```

---

## Checklist pre-release

Prima di ogni release, verifica:

- [ ] `version` aggiornato in `src-tauri/tauri.conf.json`
- [ ] `version` aggiornato in `src-tauri/Cargo.toml`
- [ ] `version` aggiornato in `package.json`
- [ ] `backend/api/server.py` — versione aggiornata
- [ ] CHANGELOG.md aggiornato con la nuova sezione
- [ ] Tutti i test passano: `python3 -m pytest tests/backend/ -v`
- [ ] Build frontend OK: `npm run build`
- [ ] Nessuna API key hardcoded nel codice
- [ ] `.env` non committato
- [ ] `.tauri-keys/` non committato

---

## Struttura del release

```
GitHub Release v0.9.0-beta
├── VIO.83.AI.Orchestra_0.9.0_universal.dmg    ← installer firmato + notarizzato
├── VIO.83.AI.Orchestra_0.9.0_aarch64.app.tar.gz    ← per auto-updater arm64
├── VIO.83.AI.Orchestra_0.9.0_aarch64.app.tar.gz.sig ← firma updater
├── VIO.83.AI.Orchestra_0.9.0_x86_64.app.tar.gz
├── VIO.83.AI.Orchestra_0.9.0_x86_64.app.tar.gz.sig
└── latest.json    ← manifesto auto-updater
```

### Formato `latest.json`

```json
{
  "version": "v0.9.0-beta",
  "notes": "VIO 83 AI Orchestra v0.9.0-beta",
  "pub_date": "2026-03-18T10:00:00Z",
  "platforms": {
    "darwin-aarch64": {
      "signature": "dW50cnVzdGVkIGNvbW...",
      "url": "https://github.com/vio83/vio83-ai-orchestra/releases/download/v0.9.0-beta/VIO.83.AI.Orchestra_0.9.0_aarch64.app.tar.gz"
    },
    "darwin-x86_64": {
      "signature": "dW50cnVzdGVkIGNvbW...",
      "url": "https://github.com/vio83/vio83-ai-orchestra/releases/download/v0.9.0-beta/VIO.83.AI.Orchestra_0.9.0_x86_64.app.tar.gz"
    }
  }
}
```

---

## Distribuzione post-release

### Canali di distribuzione

1. **GitHub Releases** (principale): https://github.com/vio83/vio83-ai-orchestra/releases
2. **Direct download link**: https://github.com/vio83/vio83-ai-orchestra/releases/latest/download/VIO.83.AI.Orchestra_VERSIONE_universal.dmg
3. **Auto-updater**: gli utenti esistenti ricevono notifica automatica nell'app

### Test del DMG finale

Prima di pubblicare, testa su Mac:
```bash
# Installa dalla DMG
# Verifica che:
# 1. L'app si apre senza Gatekeeper warning
# 2. Il backend si avvia (http://127.0.0.1:4000/health)
# 3. L'onboarding appare al primo avvio
# 4. La chat funziona in modalità locale (Ollama)
```

---

## Costi stimati

| Voce | Costo |
|------|-------|
| Apple Developer Program | $99/anno |
| GitHub (repo pubblico) | Gratuito |
| Distribuzione DMG | Gratuito (GitHub Releases) |
| **Totale** | **$99/anno** |

---

_Contatti: porcu.v.83@gmail.com_
_Repo: https://github.com/vio83/vio83-ai-orchestra_
