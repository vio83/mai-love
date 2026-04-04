# VIO83 — ISTRUZIONI COMPLETE STEP-BY-STEP

## STATO ATTUALE MAC AIR (4 Aprile 2026, 07:05)

### Security Suite Installata:
- ✔ **Firewall macOS**: ATTIVO + Stealth Mode ON
- ✔ **LuLu** (Objective-See): Firewall applicativo ATTIVO
- ✔ **KnockKnock**: Scanner startup items INSTALLATO
- ✔ **ClamAV**: Antivirus con 3.6M+ firme, scansione cron ogni notte alle 3:00
- ✔ **SIP** (System Integrity Protection): ENABLED
- ⚠ **BlockBlock**: richiede installazione manuale (vedi sotto)
- ⚠ **osquery**: richiede installazione manuale (vedi sotto)

### Comandi Security disponibili:
```bash
vio_security_status.sh    # Dashboard security rapida
vio_clamscan_now.sh       # Scansione antivirus immediata
open /Applications/KnockKnock.app  # Scansione startup items
open /Applications/LuLu.app        # Gestione firewall applicativo
```

---

## PARTE A — COMPLETARE SECURITY SUL MAC AIR (2 minuti)

### A1. Installare BlockBlock (richiede sudo)
Apri **Terminale** sul Mac Air e digita:
```bash
brew install --cask blockblock
```
Ti chiederà la password. Dopo l'installazione:
1. Vai in **Impostazioni → Privacy e Sicurezza → Full Disk Access**
2. Aggiungi **BlockBlock Helper**
3. Apri BlockBlock dalle Applicazioni

### A2. Installare osquery (richiede sudo)
```bash
brew install --cask osquery
```
Dopo l'installazione, testa con:
```bash
osqueryi "SELECT name, pid, cmdline FROM processes WHERE on_disk = 0;"
```

### A3. Concedere permessi a LuLu
1. **Impostazioni → Privacy e Sicurezza → Estensioni di rete**
2. Abilita **LuLu**
3. Al primo avvio LuLu chiederà per ogni app se permettere la connessione

---

## PARTE B — PREPARARE USB PER iMAC

### Contenuto attuale USB VIOIMAC:
```
/Volumes/VIOIMAC/
├── diagnostica_imac_pro.sh          # Diagnostica già eseguita ✔
├── FASE0_fix_critici_imac.sh        # Fix critici (volume, bird, wifi)
├── FASE0_imac_pre_kali_optimize.sh  # Ottimizzazione pre-Kali (vecchia versione)
├── FASE1_ottimizzazione_pre_kali.sh # Ottimizzazione massima
├── FASE2_crea_usb_kali_boot.sh      # Crea USB Kali (da eseguire su Mac Air)
├── FASE3_kali_dev_environment.sh    # Setup completo Kali
├── SECURITY_crowdstrike_replica_macair.sh  # Security Mac Air (già fatto)
└── REPORT_DIAGNOSTICA_IMAC.md       # Report diagnostica
```

---

## PARTE C — SULL'iMAC: ESECUZIONE STEP-BY-STEP

### PRIMA DI STACCARE LA USB DAL MAC AIR:
La USB è già pronta con tutti gli script. Puoi staccarla.

### Step 1: Inserire USB nell'iMac e aprire Terminale

1. Inserisci la USB **VIOIMAC** nell'iMac
2. Apri **Terminale** (Applicazioni → Utility → Terminale)
3. Verifica che la USB sia visibile:
```bash
ls /Volumes/VIOIMAC/
```
Dovresti vedere tutti i file .sh elencati sopra.

### Step 2: Eseguire FASE 0 — Fix Critici

**IMPORTANTE**: Il path è `/Volumes/VIOIMAC/FASE0_fix_critici_imac.sh` (nella ROOT della USB, NON in scripts/imac/)

```bash
sudo bash /Volumes/VIOIMAC/FASE0_fix_critici_imac.sh
```

Password: quella dell'utente **Chiara** sull'iMac.

**Cosa fa FASE 0:**
- Verifica/avvia Macs Fan Control (anti-surriscaldamento)
- Killa bird (iCloud daemon che mangia 89% CPU)
- Disabilita AirPort Atheros40 (errori kernel ogni 2-3 sec)
- Tenta riparazione volume Macintosh HD corrotto
- Attiva firewall + stealth mode
- Pulizia aggressiva cache, log, lingue, bloatware
- Disabilita servizi inutili (Bluetooth, Spotlight, Siri, ecc.)
- Tuning kernel performance
- Disabilita animazioni per fluidità massima
- Reset RAM e swap

**Durata stimata**: 3-5 minuti

### Step 3: Se il volume NON è stato riparato

Se lo script dice che la riparazione live è fallita:

**OPZIONE A — Recovery Mode:**
1. Riavvia iMac tenendo premuto **Cmd+R**
2. Apri **Utility Disco**
3. Seleziona **Macintosh HD**
4. Clicca **S.O.S.** (Ripara disco)
5. Al termine, riavvia normalmente

**OPZIONE B — Single User Mode:**
1. Riavvia tenendo premuto **Cmd+S**
2. Al prompt digita:
```
/sbin/fsck -fy
```
3. Se dice "FILE SYSTEM WAS MODIFIED", ripeti `fsck -fy`
4. Quando dice "appears to be OK":
```
reboot
```

### Step 4: Eseguire FASE 1 — Ottimizzazione Massima

```bash
sudo bash /Volumes/VIOIMAC/FASE1_ottimizzazione_pre_kali.sh
```

**Cosa fa FASE 1:**
- Killa 40+ processi inutili
- Disabilita 50+ launch agents/daemons
- Ottimizza disco HDD al massimo
- Pulizia deep (cache, crash reports, cestino, download vecchi)
- Ottimizza rete per Ethernet
- Configura memoria per 8GB
- Riduce overhead GPU
- Installa auto-maintenance (cron ogni 6 ore)

**Durata stimata**: 5-10 minuti

### Step 5: TORNARE AL MAC AIR — Creare USB Kali Boot

**ATTENZIONE**: Per questo step serve una SECONDA USB (minimo 16GB) oppure puoi sovrascrivere VIOIMAC dopo aver copiato gli script altrove.

Sul **Mac Air**, con la seconda USB inserita:
```bash
sudo bash /Users/padronavio/Projects/vio83-ai-orchestra/scripts/imac/FASE2_crea_usb_kali_boot.sh
```

Lo script:
1. Scarica Kali Linux ISO (~4GB)
2. Verifica SHA256
3. Ti chiede quale disco USB usare
4. Scrive l'ISO sulla USB
5. Fornisce istruzioni per persistence

**Durata stimata**: 30-60 minuti (dipende dalla velocità internet)

### Step 6: Boot iMac da USB Kali

1. Inserisci la USB Kali nell'iMac
2. **Riavvia** l'iMac
3. Tieni premuto il tasto **OPTION (Alt)** subito al suono di avvio
4. Apparirà il menu di selezione boot
5. Seleziona il disco USB (potrebbe apparire come **EFI Boot**)
6. Nel menu Kali, seleziona **Live system**

**Se il boot da USB non funziona:**
- Prova tenendo premuto **C** invece di Option
- L'iMac 2009 potrebbe richiedere **rEFInd** per boot EFI da USB

### Step 7: Dopo il boot Kali — Setup Ambiente

Una volta dentro Kali Linux, apri un terminale e:

```bash
# Connetti Ethernet (il Wi-Fi potrebbe non funzionare)
# Verifica connessione:
ping -c 3 google.com

# Clona i repository
git clone https://github.com/vio83/mai-love.git ~/Projects/vio83-ai-orchestra
git clone https://github.com/vio83/ai-scripts-elite.git ~/Projects/ai-scripts-elite

# Oppure se hai una seconda USB con gli script:
sudo bash /media/*/VIOIMAC/FASE3_kali_dev_environment.sh

# O dal repo clonato:
cd ~/Projects/vio83-ai-orchestra
sudo bash scripts/imac/FASE3_kali_dev_environment.sh
```

**Cosa fa FASE 3:**
- Fan control via applesmc (CRITICO!)
- Python 3.12+, Node.js 20, Rust, Go, Ruby
- VS Code + 19 estensioni (Copilot, GitLens, ecc.)
- Claude Code CLI
- Ollama (AI locale)
- Git configurato con i tuoi repo
- Docker + docker-compose
- Security stack completo (ClamAV, osquery, Suricata, Wazuh, fail2ban, rkhunter, UFW)
- OSINT tools (exiftool, sherlock, theHarvester, SpiderFoot, Maltego, Nmap, Wireshark)
- Auto-optimization ogni 15 minuti
- Kernel tuning Linux
- SSH server hardened
- tmux + htop + ripgrep + fzf

**Durata stimata**: 30-60 minuti

---

## PARTE D — NAVIGAZIONE SICURA

### Puoi navigare liberamente su internet?
**SÌ**, con protezione completa:

- **LuLu** controlla ogni connessione in uscita (ti chiede permesso)
- **Firewall + Stealth Mode** blocca connessioni in ingresso non autorizzate
- **ClamAV** scansiona automaticamente ogni notte
- **SIP** protegge i file di sistema

### Deep Web / Dark Web (Tor)
Per navigazione Tor **legittima** (ricerca, giornalismo, privacy):

Su Kali Linux è già disponibile:
```bash
sudo apt install tor torbrowser-launcher
torbrowser-launcher
```

Su Mac Air:
```bash
brew install --cask tor-browser
```

**NOTA**: Tor è uno strumento legale per la privacy. Usalo per ricerca e informazione come indicato.

---

## RIEPILOGO ARCHITETTURA FINALE

```
┌─────────────────────────────────┐
│         MAC AIR M1              │
│  ┌───────────────────────────┐  │
│  │ VIO83 AI Orchestra        │  │
│  │ Claude Code Desktop       │  │
│  │ VS Code + Copilot         │  │
│  │ Ollama (6 modelli)        │  │
│  └───────────────────────────┘  │
│  SECURITY:                      │
│  LuLu + KnockKnock + ClamAV    │
│  Firewall + Stealth + SIP      │
└──────────────┬──────────────────┘
               │ SSH / Git sync
┌──────────────▼──────────────────┐
│         iMAC 2009               │
│  ┌───────────────────────────┐  │
│  │ Kali Linux (USB boot)     │  │
│  │ VS Code + Claude Code     │  │
│  │ Ollama (3 modelli)        │  │
│  │ Docker containers         │  │
│  └───────────────────────────┘  │
│  SECURITY:                      │
│  ClamAV + osquery + Suricata    │
│  Wazuh + fail2ban + UFW         │
│  OSINT: sherlock, nmap, etc.    │
│  AUTO-OPTIMIZE: ogni 15 min     │
│  FAN CONTROL: applesmc          │
└─────────────────────────────────┘
```

---

*Generato il 4 Aprile 2026 — VIO83 AI Orchestra + Claude Opus*
