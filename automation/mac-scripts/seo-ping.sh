#!/bin/bash
# ============================================================
# VIO 83 AI ORCHESTRA — SEO Ping Script
# Runs every 6 hours via launchd to ping search engines
# ============================================================

LOG_FILE="$HOME/Projects/vio83-ai-orchestra/automation/logs/seo-ping.log"
mkdir -p "$(dirname "$LOG_FILE")"

echo "$(date '+%Y-%m-%d %H:%M:%S') — SEO Ping Starting" >> "$LOG_FILE"

# 1. Ping Google
curl -s "https://www.google.com/ping?sitemap=https://vio83.github.io/vio83-ai-orchestra/sitemap.xml" > /dev/null 2>&1
echo "$(date '+%Y-%m-%d %H:%M:%S') — Google pinged" >> "$LOG_FILE"

# 2. Ping Bing
curl -s "https://www.bing.com/ping?sitemap=https://vio83.github.io/vio83-ai-orchestra/sitemap.xml" > /dev/null 2>&1
echo "$(date '+%Y-%m-%d %H:%M:%S') — Bing pinged" >> "$LOG_FILE"

# 3. Ping IndexNow (Bing + Yandex + DuckDuckGo + Seznam)
curl -s -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json" \
  -d '{
    "host": "vio83.github.io",
    "key": "3e6f9ffe76d0f756d7492ec16fd4d501",
    "keyLocation": "https://vio83.github.io/vio83-ai-orchestra/3e6f9ffe76d0f756d7492ec16fd4d501.txt",
    "urlList": [
      "https://vio83.github.io/vio83-ai-orchestra/",
      "https://vio83.github.io/vio83-ai-orchestra/sitemap.xml"
    ]
  }' > /dev/null 2>&1
echo "$(date '+%Y-%m-%d %H:%M:%S') — IndexNow pinged" >> "$LOG_FILE"

# 4. Get GitHub stats
STARS=$(curl -s "https://api.github.com/repos/vio83/vio83-ai-orchestra" | python3 -c "import sys,json; print(json.load(sys.stdin).get('stargazers_count','?'))" 2>/dev/null)
echo "$(date '+%Y-%m-%d %H:%M:%S') — GitHub stars: $STARS" >> "$LOG_FILE"

echo "$(date '+%Y-%m-%d %H:%M:%S') — SEO Ping Complete ✅" >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
