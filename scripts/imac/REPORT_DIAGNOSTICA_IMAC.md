# REPORT DIAGNOSTICA PROFESSIONALE — iMac 2009 (iMac11,1)
## Data: 4 Aprile 2026 — Analisi: Claude per Vio83

---

## STATO GENERALE: 75/100 — BUONO (con criticità risolvibili)

---

## 1. HARDWARE

| Componente | Stato | Dettaglio |
|---|---|---|
| **CPU** | ✔ BUONO | Intel Core i7 860 @ 2.80GHz, 4 core / 8 thread, L3 8MB. Nessun throttling termico rilevato. |
| **RAM** | ⚠ SUFFICIENTE | 8.0 GB (4x2GB DDR3 1066MHz), 3289 MB liberi. Upgrade a 16GB (4x4GB) raccomandato per dev+Kali. |
| **Disco** | ⚠ LENTO | Hitachi HDS722020ALA330, 2TB HDD 7200RPM. SMART: Verified OK. Write: 21.6 MB/s — COLLO DI BOTTIGLIA principale. SSD esterno USB3 consigliato per boot Kali. |
| **GPU** | ⚠ LIMITATA | ATI Radeon HD 4850, 512MB VRAM. NO Metal. Funzionale per terminale/code, non per GPU compute. |
| **Display** | ✔ OK | 27" 2560x1440, funzionante. |
| **Ventole** | ✔ OK | Macs Fan Control INSTALLATO e ATTIVO (PID 489). Critico per prevenire shutdown termici. |
| **USB** | ✔ OK | USB VIOIMAC visibile su /dev/disk1. |

### Raccomandazioni Hardware
- **PRIORITÀ 1**: SSD esterno USB 3.0 per boot Kali (il HDD interno è il limite #1)
- **PRIORITÀ 2**: Upgrade RAM a 16GB (4x4GB DDR3 1066MHz SO-DIMM, ~€30 usato)
- **PRIORITÀ 3**: Pasta termica nuova sulla CPU (se mai aperto, dopo 16 anni è secca)

---

## 2. CRITICITÀ TROVATE (3 ROSSE)

### 🔴 CRITICO #1: Volume Macintosh HD CORROTTO
```
diskutil verifyVolume / → "The volume Macintosh HD was found corrupt and needs to be repaired"
```
**Fix**: `diskutil repairVolume /` da Recovery Mode, oppure `fsck -fy` da Single User Mode (Cmd+S al boot).
**Rischio**: Crash filesystem, perdita dati, impossibilità boot futuro.

### 🔴 CRITICO #2: AirPort Atheros40 — Errori Kernel ogni 2-3 secondi
```
Kernel log flooding: AirPort_Atheros40 driver errors continuously
```
**Fix**: Disabilitare Wi-Fi e usare Ethernet cablato, oppure:
```bash
sudo kextunload -b com.apple.driver.AirPort.Atheros40
sudo networksetup -setairportpower en1 off
```
**Impatto**: Spreco CPU continuo, log flooding, potenziale instabilità kernel.

### 🔴 CRITICO #3: bird (iCloud daemon) al 89% CPU
```
bird process consuming 89% CPU — iCloud sync daemon out of control
```
**Fix**:
```bash
killall bird
launchctl unload -w /System/Library/LaunchDaemons/com.apple.bird.plist 2>/dev/null
defaults write com.apple.bird optimize -bool false
```
**Impatto**: Ruba quasi un core intero. Inutile per una macchina dev/OSINT.

---

## 3. SICUREZZA

| Aspetto | Stato |
|---|---|
| **Firewall** | ❌ DISABILITATO — da attivare immediatamente |
| **FileVault** | ❌ OFF — non prioritario per macchina locale dev |
| **SIP** | Da verificare in Recovery |
| **Gatekeeper** | Attivo |
| **86 app installate** | Molte non necessarie — pulizia aggressiva raccomandata |

---

## 4. PRESTAZIONI DISCO (il collo di bottiglia)

| Metrica | Valore | Giudizio |
|---|---|---|
| Write speed (dd) | 21.6 MB/s | ❌ LENTO (SSD = 400-500 MB/s) |
| Spazio totale | 1.8 TB | |
| Spazio libero | 1.6 TB | ✔ Abbondante |
| Tipo | HDD meccanico 7200rpm | Bottleneck principale |

**Conclusione**: Il disco meccanico è il limite #1. Kali Linux su SSD esterno USB 3.0 sarà 15-20x più veloce.

---

## 5. PIANO D'AZIONE IMMEDIATO

### FASE 0 — Fix Critici (PRIMA di tutto)
1. Riparare volume corrotto (`diskutil repairVolume /` o `fsck -fy`)
2. Killare bird e disabilitarlo permanentemente
3. Disabilitare AirPort Atheros40 (usare Ethernet)
4. Attivare firewall macOS
5. Pulizia aggressiva: rimuovere app inutili, cache, lingue, log

### FASE 1 — Ottimizzazione High Sierra
1. Disabilitare Spotlight, Time Machine, animazioni
2. Tuning kernel (sysctl)
3. Disabilitare servizi non necessari (Bluetooth, printer sharing, etc.)
4. Liberare RAM (reset swap, purge)

### FASE 2 — Kali Linux USB Boot
1. Creare USB bootabile con Kali Linux (immagine per AMD64)
2. Persistence partition per salvare configurazioni
3. Installare ambiente dev: VS Code, Claude Code, Python, Node.js
4. Configurare auto-optimization ogni 15 minuti
5. Fan control via applesmc su Linux

### FASE 3 — Security Hardening
1. Objective-See tools (LuLu, BlockBlock, KnockKnock)
2. osquery + ClamAV + OSSEC
3. Suricata IDS
4. Configurazione iptables/nftables su Kali

---

*Report generato automaticamente da VIO83 AI Orchestra — Claude Opus*
