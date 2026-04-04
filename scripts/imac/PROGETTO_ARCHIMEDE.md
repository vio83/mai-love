# PROGETTO ARCHIMEDE — Arch Linux iMac Enhanced Development Environment

## Stato: IN PREPARAZIONE (4 Aprile 2026)

---

## Panoramica

Installazione Arch Linux in dual-boot su iMac 2009 (iMac11,1) con:
- **3 livelli di protezione** contro breakage (Btrfs snapshot, kernel pinning, fan watchdog)
- **Ambiente dev completo** (Python, Node, Rust, Go, VS Code, Docker, AI tools)
- **Security stack** (ClamAV, fail2ban, UFW, rkhunter)
- **OSINT tools** (nmap, wireshark, sherlock, Kali via Docker)
- **Automazione totale** da Claude (Desktop Commander + SSH)

---

## Hardware Target

| Componente | Specifiche | Driver Linux |
|-----------|-----------|-------------|
| CPU | Intel Core i7 860 @ 2.80GHz (4C/8T) | Supportato nativamente |
| RAM | 8GB DDR3 1067MHz | Supportato nativamente |
| GPU | ATI Radeon HD 4850 512MB | `xf86-video-ati` + `radeon` kernel module |
| Storage | Hitachi 2TB 7200RPM HDD | `deadline` scheduler ottimale |
| Wi-Fi | Atheros AR5BXB92 | `ath9k` kernel module |
| Ethernet | Broadcom BCM5764 | `tg3` kernel module |
| Fan Control | Apple SMC | `applesmc` kernel module |
| Audio | Cirrus Logic CS4206 | `snd-hda-intel` |

---

## Prerequisiti (DA COMPLETARE PRIMA)

### 1. Riparazione Volume macOS
Il volume Macintosh HD è corrotto. **OBBLIGATORIO** riparare prima dell'installazione Linux:

```
Opzione A — Recovery Mode:
  1. Riavvia iMac → Cmd+R
  2. Utility Disco → Macintosh HD → S.O.S.
  3. Riavvia

Opzione B — Single User Mode:
  1. Riavvia iMac → Cmd+S
  2. /sbin/fsck -fy
  3. Ripetere finché "appears to be OK"
  4. reboot
```

### 2. Wi-Fi Hotspot
Eseguire `FIX_wifi_hotspot_ottimizzato.sh` sull'iMac per riabilitare Wi-Fi (disabilitato in FASE0).

---

## Fasi di Installazione

### FASE 0 + FASE 1 ✅ GIÀ COMPLETATE
- Fix critici iMac (bird, AirPort, firewall)
- Ottimizzazione pre-Linux (41 agenti disabilitati, HDD ottimizzato)

### FASE 2 — USB Installer (Mac Air)
**Script**: `FASE2_arch_usb_installer.sh`
- Download ISO Arch Linux (~800MB)
- Verifica SHA256
- Flash su USB 8GB
- Tempo: ~10 min (dipende da internet)

### FASE 3 — Installazione Arch (iMac)
**Script**: `FASE3_arch_auto_install.sh`
- Boot da USB → connessione hotspot iPhone
- Partizionamento: 400GB Btrfs + 8GB swap (preserva macOS)
- pacstrap sistema base + driver iMac
- GRUB dual-boot
- SSH server + fan watchdog al primo boot
- Tempo: ~20 min

### FASE 4 — Dev Environment (iMac)
**Script**: `FASE4_arch_dev_environment.sh`
- XFCE4 desktop (leggero)
- Linguaggi + VS Code + AI tools
- Docker + security + OSINT
- Auto-optimization ogni 15 min
- Tempo: ~45 min

---

## Architettura di Protezione

### Livello 1: Btrfs Snapshot
- Filesystem Btrfs con 5 subvolumes (@, @home, @snapshots, @var_log, @var_cache)
- Snapshot automatico PRIMA di ogni aggiornamento
- Rollback in 5 secondi: `btrfs subvolume snapshot`
- Pulizia automatica (mantiene ultimi 5 snapshot)

### Livello 2: Kernel Pinning
- `safe_update.sh` sostituisce `pacman -Syu`
- Verifica moduli critici (radeon, ath9k, applesmc) dopo update
- Downgrade automatico kernel se moduli mancanti
- Cache pacman preservata per downgrade

### Livello 3: Fan Control Watchdog
- Monitoraggio temperatura ogni 10 secondi
- Ventole proporzionali: 50°C=1200rpm → 85°C=6200rpm
- Shutdown di emergenza a 95°C
- Systemd service con auto-restart

---

## Accesso Remoto

SSH attivo al boot su porta 22. Dal Mac Air:
```bash
ssh vio@archimede.local
# oppure
ssh vio@[IP_iMac]
```

Permette a Claude di:
- Fixare problemi via Desktop Commander (Mac Air → SSH → iMac)
- Eseguire aggiornamenti e manutenzione
- Monitorare stato sistema

---

## Comandi Post-Installazione

| Comando | Funzione |
|---------|----------|
| `status` | Dashboard sistema completa |
| `update` | Aggiornamento sicuro con snapshot |
| `snap` | Snapshot manuale Btrfs |
| `fans` | Stato ventole |
| `temp` | Temperature sensori |
| `~/kali-docker.sh` | Container Kali Linux completo |

---

## File del Progetto

```
scripts/imac/
├── FASE0_fix_critici_imac.sh           ✅ Eseguito
├── FASE1_ottimizzazione_pre_kali.sh    ✅ Eseguito
├── FASE2_arch_usb_installer.sh         ⬜ Da eseguire su Mac Air
├── FASE3_arch_auto_install.sh          ⬜ Da eseguire su iMac (boot USB)
├── FASE4_arch_dev_environment.sh       ⬜ Da eseguire su iMac (post-install)
├── FIX_wifi_hotspot_ottimizzato.sh     ⚠ Da eseguire su iMac (prerequisito)
├── PROGETTO_ARCHIMEDE.md               📄 Questo documento
├── ISTRUZIONI_COMPLETE_STEP_BY_STEP.md 📄 Istruzioni vecchie (pre-Arch)
└── REPORT_DIAGNOSTICA_IMAC.md          📄 Report diagnostica
```

---

*Progetto ARCHIMEDE — VIO83 AI Orchestra + Claude Opus — 4 Aprile 2026*
