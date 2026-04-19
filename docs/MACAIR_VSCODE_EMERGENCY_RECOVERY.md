# Mac Air VS Code emergency recovery

## Most likely cause

On the Mac Air, the current repository contains multiple macOS launchd installers and heavy AI-extension setup scripts. On an 8 GB machine, the combined load of Ollama, Continue, Copilot, Twinny, CodeGPT, and always-on watchdogs can make VS Code freeze or fail to behave normally.

## Safe recovery script

Run on the Mac Air:

bash ~/Projects/vio83-ai-orchestra/scripts/runtime/macair_vscode_emergency_recovery.sh

## What it does

- unloads the VIO83 launch agents
- stops heavy local AI background processes
- clears non-critical VS Code caches
- writes a minimal safe settings file
- preserves a backup of the original user settings on the Desktop

## Important note

This is a recovery path, not a bypass. It does not alter account authentication or security controls.
