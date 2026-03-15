# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ALL RIGHTS RESERVED — https://github.com/vio83/vio83-ai-orchestra
# ============================================================
"""
VIO 83 AI ORCHESTRA — Security & API Key Management
Gestione sicura delle credenziali e configurazione:

- API Key Vault: Storage sicuro delle chiavi API
- Environment Validation: Verifica .env al boot
- Key Rotation: Supporto per rotazione chiavi
- Audit Log: Traccia accessi alle chiavi
- Encryption: Obfuscazione chiavi in memoria
"""

import os
import re
import time
import hashlib
import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger("vio83.security")


@dataclass
class APIKeyInfo:
    """Informazioni su una chiave API."""
    provider: str
    env_var: str
    masked_key: str
    is_valid: bool
    key_length: int
    prefix: str
    last_used: float = 0
    use_count: int = 0
    last_error: Optional[str] = None


class APIKeyVault:
    """
    Vault sicuro per le chiavi API.
    - Le chiavi NON vengono mai loggato in chiaro
    - Mascheramento automatico (sk-...xxxx)
    - Validazione formato chiave
    - Audit trail di ogni accesso
    """

    # Pattern di validazione per ogni provider
    KEY_PATTERNS = {
        # --- Provider Gratuiti ---
        "GROQ_API_KEY": r"^gsk_[a-zA-Z0-9]{30,}$",
        "TOGETHER_API_KEY": r"^[a-fA-F0-9]{64}$",
        "OPENROUTER_API_KEY": r"^sk-or-v1-[a-zA-Z0-9]{40,}$",
        # --- Provider Economici ---
        "DEEPSEEK_API_KEY": r"^sk-[a-zA-Z0-9]{30,}$",
        "MISTRAL_API_KEY": r"^[a-zA-Z0-9]{30,}$",
        # --- Provider Standard ---
        "ANTHROPIC_API_KEY": r"^sk-ant-[a-zA-Z0-9\-_]{40,}$",
        "OPENAI_API_KEY": r"^sk-[a-zA-Z0-9\-_]{30,}$",
        "XAI_API_KEY": r"^xai-[a-zA-Z0-9\-_]{30,}$",
        "GEMINI_API_KEY": r"^AI[a-zA-Z0-9\-_]{30,}$",
    }

    PROVIDER_MAP = {
        # --- Provider Gratuiti ---
        "GROQ_API_KEY": "groq",
        "TOGETHER_API_KEY": "together",
        "OPENROUTER_API_KEY": "openrouter",
        # --- Provider Economici ---
        "DEEPSEEK_API_KEY": "deepseek",
        "MISTRAL_API_KEY": "mistral",
        # --- Provider Standard ---
        "ANTHROPIC_API_KEY": "claude",
        "OPENAI_API_KEY": "gpt4",
        "XAI_API_KEY": "grok",
        "GEMINI_API_KEY": "google",
    }

    def __init__(self):
        self._audit_log: list[dict] = []
        self._key_info: dict[str, APIKeyInfo] = {}
        self._initialized = False

    def initialize(self):
        """Scansiona l'ambiente e valida tutte le chiavi."""
        logger.info("[Security] Inizializzazione API Key Vault...")

        for env_var, provider in self.PROVIDER_MAP.items():
            key = os.environ.get(env_var, "")
            if key:
                is_valid = self._validate_key(env_var, key)
                masked = self._mask_key(key)
                self._key_info[env_var] = APIKeyInfo(
                    provider=provider,
                    env_var=env_var,
                    masked_key=masked,
                    is_valid=is_valid,
                    key_length=len(key),
                    prefix=key[:8] + "..." if len(key) > 8 else "***",
                )
                status = "✓ valida" if is_valid else "⚠ formato sospetto"
                logger.info(f"  [{provider}] {masked} ({status})")
            else:
                self._key_info[env_var] = APIKeyInfo(
                    provider=provider,
                    env_var=env_var,
                    masked_key="(non configurata)",
                    is_valid=False,
                    key_length=0,
                    prefix="",
                )

        self._initialized = True
        valid_count = sum(1 for k in self._key_info.values() if k.is_valid)
        total = len(self._key_info)
        logger.info(f"[Security] Vault inizializzato: {valid_count}/{total} chiavi valide")

    def get_key(self, env_var: str) -> Optional[str]:
        """
        Recupera una chiave API dall'ambiente.
        Registra l'accesso nell'audit log.
        """
        key = os.environ.get(env_var)
        if key and env_var in self._key_info:
            self._key_info[env_var].last_used = time.time()
            self._key_info[env_var].use_count += 1
            self._audit_log.append({
                "action": "key_access",
                "env_var": env_var,
                "provider": self._key_info[env_var].provider,
                "timestamp": time.time(),
            })
        return key

    def get_key_for_provider(self, provider: str) -> Optional[str]:
        """Recupera la chiave per un provider specifico."""
        for env_var, info in self._key_info.items():
            if info.provider == provider and info.is_valid:
                return self.get_key(env_var)
        return None

    def _validate_key(self, env_var: str, key: str) -> bool:
        """Valida il formato della chiave."""
        pattern = self.KEY_PATTERNS.get(env_var)
        if pattern:
            return bool(re.match(pattern, key))
        return len(key) >= 20  # Fallback: almeno 20 caratteri

    @staticmethod
    def _mask_key(key: str) -> str:
        """Maschera la chiave per logging sicuro."""
        if len(key) <= 8:
            return "****"
        return f"{key[:4]}...{key[-4:]}"

    @property
    def available_providers(self) -> list[str]:
        """Lista provider con chiave valida."""
        return [info.provider for info in self._key_info.values() if info.is_valid]

    @property
    def stats(self) -> dict:
        return {
            "initialized": self._initialized,
            "total_keys": len(self._key_info),
            "valid_keys": sum(1 for k in self._key_info.values() if k.is_valid),
            "providers": {
                info.provider: {
                    "masked_key": info.masked_key,
                    "is_valid": info.is_valid,
                    "use_count": info.use_count,
                }
                for info in self._key_info.values()
            },
            "audit_log_size": len(self._audit_log),
        }


class EnvironmentValidator:
    """
    Valida la configurazione dell'ambiente al boot.
    Verifica che tutto il necessario sia presente e corretto.
    """

    REQUIRED_DIRS = ["data", ".logs"]
    OPTIONAL_FILES = [".env"]

    def __init__(self, project_dir: str = "."):
        self.project_dir = project_dir
        self._warnings: list[str] = []
        self._errors: list[str] = []

    def validate(self) -> dict:
        """Esegui validazione completa dell'ambiente."""
        self._warnings.clear()
        self._errors.clear()

        self._check_directories()
        self._check_env_file()
        self._check_python_deps()
        self._check_ollama()
        self._check_disk_space()

        return {
            "valid": len(self._errors) == 0,
            "errors": list(self._errors),
            "warnings": list(self._warnings),
        }

    def _check_directories(self):
        for dir_name in self.REQUIRED_DIRS:
            dir_path = os.path.join(self.project_dir, dir_name)
            if not os.path.isdir(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    self._warnings.append(f"Directory creata: {dir_name}/")
                except Exception as e:
                    self._errors.append(f"Impossibile creare {dir_name}/: {e}")

    def _check_env_file(self):
        env_path = os.path.join(self.project_dir, ".env")
        if not os.path.isfile(env_path):
            self._warnings.append(
                ".env non trovato. I provider cloud non saranno disponibili. "
                "Crea il file con: cp .env.example .env"
            )

    def _check_python_deps(self):
        optional_deps = {
            "httpx": "Chiamate HTTP async (pip install httpx)",
            "chromadb": "Vector database (pip install chromadb)",
            "sentence_transformers": "Embedding locali (pip install sentence-transformers)",
        }
        for module, description in optional_deps.items():
            try:
                __import__(module)
            except ImportError:
                self._warnings.append(f"Modulo opzionale mancante: {module} — {description}")
            except Exception as e:
                # ChromaDB + Pydantic V1 crasha su Python 3.14 con ConfigError
                self._warnings.append(f"Modulo {module} presente ma non caricabile: {type(e).__name__}")

    def _check_ollama(self):
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        except Exception:
            self._warnings.append(
                "Ollama non raggiungibile. Avvialo con: ollama serve"
            )

    def _check_disk_space(self):
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.project_dir)
            free_gb = free / (1024 ** 3)
            if free_gb < 1.0:
                self._errors.append(f"Spazio disco insufficiente: {free_gb:.1f}GB liberi")
            elif free_gb < 5.0:
                self._warnings.append(f"Spazio disco basso: {free_gb:.1f}GB liberi")
        except Exception:
            pass


# === SINGLETON ===
_vault: Optional[APIKeyVault] = None


def get_vault() -> APIKeyVault:
    global _vault
    if _vault is None:
        _vault = APIKeyVault()
        _vault.initialize()
    return _vault
