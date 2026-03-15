# TASK 03 — Privacy e Sicurezza Blindata Mac/Orion

## Obiettivo
Configurare Mac padronavio per privacy e sicurezza massima su Orion browser.

## Istruzioni per Claude
Configura i seguenti livelli di protezione:

### DNS
- Attiva DNS over HTTPS (DoH) con 1.1.1.1 Cloudflare
- Backup DNS: 8.8.8.8 Google

### Firewall
- Firewall macOS al livello massimo
- Blocco connessioni in entrata non autorizzate
- Log di tutte le connessioni

### Browser Orion
- Blocco completo tracker e fingerprinting
- Blocco WebRTC leak
- Protezione identità equivalente navigazione anonima

### Script toggle vionet
- Aggiorna ~/vio_network_toggle.sh
- Deve gestire: Wi-Fi + _VIO_ + VIO + Tailscale + DNS
- Comando singolo: vionet
- NON toccare configurazione Tor esistente

## Interfacce di rete presenti
- Wi-Fi (principale)
- _VIO_ (virtuale)
- VIO (virtuale)
- Tailscale (VPN)
