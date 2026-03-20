#!/bin/bash
# ============================================================
# VIO 83 — FIX PROXY FANTASMA SU MAC
# Il tuo Mac ha un proxy "proxy.example.com" configurato che
# blocca Homebrew, curl, git, npm e tutto il networking.
# Questo script rimuove TUTTE le configurazioni proxy false.
# ============================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}🔧 VIO 83 — FIX PROXY MAC                         ${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# ═══════════════════════════════════════════════════════
# 1. RIMUOVI PROXY DALLE VARIABILI D'AMBIENTE SHELL
# ═══════════════════════════════════════════════════════
echo -e "\n${YELLOW}[1/5] Rimuovendo proxy dalle variabili d'ambiente...${NC}"

# Rimuovi dalle variabili correnti
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy NO_PROXY no_proxy ftp_proxy FTP_PROXY 2>/dev/null || true

# Rimuovi da tutti i file di profilo shell
SHELL_FILES=(
  "$HOME/.zshrc"
  "$HOME/.zprofile"
  "$HOME/.zshenv"
  "$HOME/.bashrc"
  "$HOME/.bash_profile"
  "$HOME/.profile"
  "$HOME/.zlogin"
)

for file in "${SHELL_FILES[@]}"; do
  if [ -f "$file" ]; then
    # Backup prima di modificare
    cp "$file" "${file}.bak-pre-proxy-fix" 2>/dev/null || true
    # Rimuovi TUTTE le righe che contengono proxy settings
    sed -i '' '/[Hh][Tt][Tt][Pp]_[Pp][Rr][Oo][Xx][Yy]/d' "$file" 2>/dev/null || true
    sed -i '' '/[Hh][Tt][Tt][Pp][Ss]_[Pp][Rr][Oo][Xx][Yy]/d' "$file" 2>/dev/null || true
    sed -i '' '/[Aa][Ll][Ll]_[Pp][Rr][Oo][Xx][Yy]/d' "$file" 2>/dev/null || true
    sed -i '' '/[Ff][Tt][Pp]_[Pp][Rr][Oo][Xx][Yy]/d' "$file" 2>/dev/null || true
    sed -i '' '/[Nn][Oo]_[Pp][Rr][Oo][Xx][Yy]/d' "$file" 2>/dev/null || true
    sed -i '' '/proxy\.example\.com/d' "$file" 2>/dev/null || true
    echo -e "  ${GREEN}✅ Pulito: $file${NC}"
  fi
done

# ═══════════════════════════════════════════════════════
# 2. RIMUOVI PROXY DA GIT CONFIG
# ═══════════════════════════════════════════════════════
echo -e "\n${YELLOW}[2/5] Rimuovendo proxy da Git config...${NC}"

git config --global --unset http.proxy 2>/dev/null || true
git config --global --unset https.proxy 2>/dev/null || true
git config --global --unset http.https://github.com.proxy 2>/dev/null || true
git config --global --unset http.https://formulae.brew.sh.proxy 2>/dev/null || true

# Rimuovi proxy anche dal config locale del progetto
if [ -d "$HOME/Projects/vio83-ai-orchestra/.git" ]; then
  cd "$HOME/Projects/vio83-ai-orchestra"
  git config --local --unset http.proxy 2>/dev/null || true
  git config --local --unset https.proxy 2>/dev/null || true
fi

echo -e "  ${GREEN}✅ Git proxy rimosso (global + local)${NC}"

# ═══════════════════════════════════════════════════════
# 3. RIMUOVI PROXY DA NPM
# ═══════════════════════════════════════════════════════
echo -e "\n${YELLOW}[3/5] Rimuovendo proxy da npm...${NC}"

npm config delete proxy 2>/dev/null || true
npm config delete https-proxy 2>/dev/null || true
npm config delete http-proxy 2>/dev/null || true

# Rimuovi anche dal file .npmrc se esiste
if [ -f "$HOME/.npmrc" ]; then
  sed -i '' '/proxy/d' "$HOME/.npmrc" 2>/dev/null || true
  echo -e "  ${GREEN}✅ Pulito: ~/.npmrc${NC}"
fi

echo -e "  ${GREEN}✅ npm proxy rimosso${NC}"

# ═══════════════════════════════════════════════════════
# 4. RIMUOVI PROXY DALLE IMPOSTAZIONI DI RETE macOS
# ═══════════════════════════════════════════════════════
echo -e "\n${YELLOW}[4/5] Rimuovendo proxy dalle impostazioni di rete macOS...${NC}"

# Trova la network interface attiva (Wi-Fi o Ethernet)
ACTIVE_SERVICE=""
while IFS= read -r line; do
  sname=$(echo "$line" | sed 's/^(.*)$/\1/' | sed 's/[\(\)]//g' | xargs)
  if [ -n "$sname" ]; then
    # Verifica se il servizio ha un proxy configurato
    wp=$(networksetup -getwebproxy "$sname" 2>/dev/null | grep -i "Enabled: Yes" || true)
    sp=$(networksetup -getsecurewebproxy "$sname" 2>/dev/null | grep -i "Enabled: Yes" || true)
    if [ -n "$wp" ] || [ -n "$sp" ]; then
      ACTIVE_SERVICE="$sname"
    fi
  fi
done < <(networksetup -listallnetworkservices 2>/dev/null | tail -n +2)

# Disabilita proxy su TUTTI i servizi di rete
for service in "Wi-Fi" "Ethernet" "USB 10/100/1000 LAN" "Thunderbolt Bridge" "iPhone USB"; do
  networksetup -setwebproxystate "$service" off 2>/dev/null || true
  networksetup -setsecurewebproxystate "$service" off 2>/dev/null || true
  networksetup -setsocksfirewallproxystate "$service" off 2>/dev/null || true
  networksetup -setautoproxystate "$service" off 2>/dev/null || true
  # Svuota anche i campi proxy (server e porta)
  networksetup -setwebproxy "$service" "" 0 2>/dev/null || true
  networksetup -setsecurewebproxy "$service" "" 0 2>/dev/null || true
done

echo -e "  ${GREEN}✅ Proxy di rete macOS disabilitati su tutte le interfacce${NC}"

# ═══════════════════════════════════════════════════════
# 5. RIMUOVI PROXY DA HOMEBREW
# ═══════════════════════════════════════════════════════
echo -e "\n${YELLOW}[5/5] Configurando Homebrew senza proxy...${NC}"

# Rimuovi variabili Homebrew specifiche
unset HOMEBREW_HTTP_PROXY HOMEBREW_HTTPS_PROXY HOMEBREW_ALL_PROXY 2>/dev/null || true

# Aggiungi unset permanente al .zshrc
ZSHRC="$HOME/.zshrc"
if ! grep -q "# VIO83: No proxy" "$ZSHRC" 2>/dev/null; then
  cat >> "$ZSHRC" << 'NOPROXY'

# VIO83: No proxy — fix permanente (20 Marzo 2026)
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy ftp_proxy FTP_PROXY NO_PROXY no_proxy HOMEBREW_HTTP_PROXY HOMEBREW_HTTPS_PROXY HOMEBREW_ALL_PROXY 2>/dev/null
NOPROXY
  echo -e "  ${GREEN}✅ Aggiunto unset permanente a .zshrc${NC}"
fi

echo -e "  ${GREEN}✅ Homebrew proxy rimosso${NC}"

# ═══════════════════════════════════════════════════════
# VERIFICA FINALE
# ═══════════════════════════════════════════════════════
echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}🔍 VERIFICA FINALE                                 ${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo ""
echo "Variabili proxy attive:"
env | grep -i proxy || echo -e "  ${GREEN}✅ NESSUN PROXY ATTIVO${NC}"

echo ""
echo "Git proxy config:"
git config --global --get http.proxy 2>/dev/null && echo -e "  ${RED}❌ Ancora presente!${NC}" || echo -e "  ${GREEN}✅ Nessun git proxy${NC}"

echo ""
echo -e "Test connessione diretta:"
if curl -s --connect-timeout 5 --noproxy '*' "https://api.github.com/zen" >/dev/null 2>&1; then
  echo -e "  ${GREEN}✅ GitHub API: raggiungibile${NC}"
else
  echo -e "  ${RED}❌ GitHub API: non raggiungibile (problema di rete, non proxy)${NC}"
fi

if curl -s --connect-timeout 5 --noproxy '*' "https://formulae.brew.sh" >/dev/null 2>&1; then
  echo -e "  ${GREEN}✅ Homebrew: raggiungibile${NC}"
else
  echo -e "  ${RED}❌ Homebrew: non raggiungibile${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  PROXY FIX COMPLETATO!                          ║${NC}"
echo -e "${GREEN}║                                                  ║${NC}"
echo -e "${GREEN}║  IMPORTANTE: Chiudi e riapri il terminale,      ║${NC}"
echo -e "${GREEN}║  oppure esegui: source ~/.zshrc                 ║${NC}"
echo -e "${GREEN}║                                                  ║${NC}"
echo -e "${GREEN}║  Poi ri-esegui: ./scripts/setup-vio-complete.sh ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
