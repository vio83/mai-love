#!/usr/bin/env python3
"""
VS Code Live Sync System
Sincronizzazione in tempo reale tra MacBook Air e iMac
Duplica modifiche VS Code come schermo mirror (AirPlay-style)
"""

import os
import json
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime
import hashlib

# Configuration
MACOS_VSCODE_DIR = Path.home() / "Library/Application Support/Code/User"
LINUX_VSCODE_DIR = Path.home() / ".config/Code/User"
IMAC_HOST = "vio@172.20.10.5"
IMAC_VSCODE_DIR = "/home/vio/.config/Code/User"

class VSCodeSyncManager:
    def __init__(self):
        self.local_vscode_dir = MACOS_VSCODE_DIR
        self.sync_log = Path("/tmp/vscode_sync.log")
        self.file_hashes = {}

    def log(self, message: str):
        """Log sync operations"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}\n"
        print(log_entry.strip())
        with open(self.sync_log, "a") as f:
            f.write(log_entry)

    def get_file_hash(self, filepath: Path) -> str:
        """Calculate file hash for change detection"""
        try:
            with open(filepath, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None

    def sync_settings_to_imac(self):
        """Sincronizza settings.json → iMac"""
        settings_file = self.local_vscode_dir / "settings.json"

        if not settings_file.exists():
            self.log(f"❌ settings.json non trovato: {settings_file}")
            return False

        try:
            # Leggi settings locali
            with open(settings_file, "r") as f:
                settings = json.load(f)

            # Modifica per italiano + tema unificato
            settings.update({
                "[it]": {
                    "editor.defaultFormatter": "esbenp.prettier-vscode",
                    "editor.formatOnSave": True
                },
                "workbench.colorTheme": "One Dark Pro",
                "editor.fontFamily": "Monaco, 'Courier New'",
                "editor.fontSize": 12,
                "editor.lineHeight": 1.6,
                "editor.tabSize": 4,
                "editor.insertSpaces": True,
                "files.autoSave": "afterDelay",
                "files.autoSaveDelay": 1000,
                "[python]": {
                    "editor.formatOnSave": True,
                    "editor.defaultFormatter": "ms-python.python",
                    "editor.codeActionsOnSave": {
                        "source.organizeImports": True
                    }
                },
                "python.linting.enabled": True,
                "python.linting.pylintEnabled": True,
                "extensions.ignoreRecommendations": False,
                "telemetry.telemetryLevel": "off",
                "git.autofetch": True,
                "git.confirmSync": False
            })

            # Serializza settings
            settings_json = json.dumps(settings, indent=2, ensure_ascii=False)

            # Invia a iMac via SCP
            temp_file = Path("/tmp/vscode_settings_sync.json")
            with open(temp_file, "w") as f:
                f.write(settings_json)

            subprocess.run([
                "scp", str(temp_file),
                f"{IMAC_HOST}:{IMAC_VSCODE_DIR}/settings.json"
            ], check=True, capture_output=True)

            self.log(f"✅ settings.json sincronizzato → iMac")
            return True

        except Exception as e:
            self.log(f"❌ Errore sync settings: {e}")
            return False

    def sync_extensions_to_imac(self):
        """Sincronizza estensioni VS Code → iMac"""
        try:
            # Lista estensioni locali
            result = subprocess.run(
                ["code", "--list-extensions"],
                capture_output=True,
                text=True
            )

            extensions = result.stdout.strip().split("\n")
            self.log(f"📦 Estensioni locali: {len(extensions)}")

            # Genera script di installazione per iMac
            install_script = "#!/bin/bash\n"
            install_script += "# Installa estensioni VS Code su iMac\n\n"

            for ext in extensions:
                if ext.strip():
                    install_script += f"code --install-extension {ext}\n"

            # Invia script a iMac
            script_file = Path("/tmp/install_vscode_extensions.sh")
            with open(script_file, "w") as f:
                f.write(install_script)

            os.chmod(script_file, 0o755)

            subprocess.run([
                "scp", str(script_file),
                f"{IMAC_HOST}:/tmp/"
            ], check=True, capture_output=True)

            # Esegui script su iMac
            subprocess.run([
                "ssh", IMAC_HOST,
                "bash /tmp/install_vscode_extensions.sh"
            ], capture_output=True)

            self.log(f"✅ Estensioni VS Code sincronizzate → iMac")
            return True

        except Exception as e:
            self.log(f"❌ Errore sync estensioni: {e}")
            return False

    def setup_italian_locale(self):
        """Configura italiano su iMac"""
        try:
            # Crea file locale settings
            italian_config = {
                "workbench.colorTheme": "One Dark Pro",
                "[it]": {
                    "editor.defaultFormatter": "esbenp.prettier-vscode"
                },
                "workbench.preferredDarkColorTheme": "One Dark Pro",
                "editor.language": "italian",
                "files.exclude": {
                    "**/__pycache__": True,
                    "**/.pytest_cache": True,
                    "**/node_modules": True
                }
            }

            # Invia a iMac
            config_json = json.dumps(italian_config, indent=2, ensure_ascii=False)
            config_file = Path("/tmp/italian_config.json")

            with open(config_file, "w") as f:
                f.write(config_json)

            subprocess.run([
                "scp", str(config_file),
                f"{IMAC_HOST}/tmp/"
            ], check=True, capture_output=True)

            self.log(f"✅ Configurazione italiano → iMac")
            return True

        except Exception as e:
            self.log(f"❌ Errore setup italiano: {e}")
            return False

    def sync_desktop_background(self):
        """Sincronizza sfondo desktop iMac → MacBook Air"""
        try:
            # Recupera sfondo da iMac
            subprocess.run([
                "scp", "-q",
                f"{IMAC_HOST}:~/.local/share/backgrounds/*",
                "/tmp/imac_backgrounds/"
            ], capture_output=True)

            self.log(f"✅ Sfondo desktop sincronizzato da iMac")
            return True

        except Exception as e:
            self.log(f"❌ Errore sync background: {e}")
            return False

    def monitor_file_changes(self):
        """Monitor file changes for real-time sync (AirPlay-style)"""
        self.log("👁️ Avvio monitoraggio vscode files...")

        monitored_files = [
            self.local_vscode_dir / "settings.json",
            self.local_vscode_dir / "keybindings.json",
        ]

        while True:
            try:
                for file_path in monitored_files:
                    if not file_path.exists():
                        continue

                    current_hash = self.get_file_hash(file_path)

                    if file_path not in self.file_hashes:
                        self.file_hashes[file_path] = current_hash
                    elif self.file_hashes[file_path] != current_hash:
                        # File changed - sync to iMac
                        self.log(f"📝 Cambio rilevato: {file_path.name}")
                        self._sync_file_to_imac(file_path)
                        self.file_hashes[file_path] = current_hash

                time.sleep(2)  # Check every 2 seconds

            except Exception as e:
                self.log(f"❌ Errore monitoraggio: {e}")
                time.sleep(5)

    def _sync_file_to_imac(self, local_file: Path):
        """Sync single file to iMac"""
        try:
            remote_file = f"{IMAC_HOST}:{IMAC_VSCODE_DIR}/{local_file.name}"
            subprocess.run(
                ["scp", "-q", str(local_file), remote_file],
                check=True,
                capture_output=True
            )
            self.log(f"🔄 {local_file.name} sincronizzato → iMac")
        except Exception as e:
            self.log(f"❌ Errore sync file: {e}")

    def run_sync_daemon(self):
        """Run full sync daemon"""
        self.log("╔══════════════════════════════════════════════════════════════╗")
        self.log("║  🔄 VS CODE LIVE SYNC DAEMON — MacBook Air → iMac           ║")
        self.log("╚══════════════════════════════════════════════════════════════╝")

        # Initial sync
        self.log("\n📤 [1/3] Sincronizzazione settings...")
        self.sync_settings_to_imac()

        self.log("\n📦 [2/3] Sincronizzazione estensioni...")
        self.sync_extensions_to_imac()

        self.log("\n🌍 [3/3] Setup italiano...")
        self.setup_italian_locale()

        self.log("\n✅ Setup iniziale completato")
        self.log("👁️  Avvio monitoraggio in tempo reale...")

        # Start background monitoring
        monitor_thread = threading.Thread(target=self.monitor_file_changes, daemon=True)
        monitor_thread.start()

        # Keep daemon alive
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            self.log("\n✋ VS Code Sync Daemon terminato")

if __name__ == "__main__":
    sync_manager = VSCodeSyncManager()
    sync_manager.run_sync_daemon()
