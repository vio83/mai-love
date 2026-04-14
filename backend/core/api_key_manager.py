 # ============================================================
# VIO 83 AI ORCHESTRA — API Key Auto-Generator & Vault
# Copyright © 2026 Viorica Porcu (vio83) — All rights reserved
# ============================================================
"""
Sistema di auto-generazione API keys per utente.

Analogia hotel:
- Ogni utente (ospite) riceve una chiave unica per la sua stanza
- La chiave è derivata dalla sua email (impronta digitale)
- Ogni AI provider ha la sua chiave specifica
- Il passe-partout (master key) può aprire tutte le porte

Meccanismo:
1. L'utente registra la sua email (impronta digitale)
2. Per ogni AI nel suo piano, viene auto-generata una VIO key
3. La VIO key = proxy token che il sistema usa per routare
   le richieste attraverso le API key master del platform
4. Le master API keys reali sono sul server VIO (passe-partout)
5. Le VIO keys utente sono token derivati, non chiavi reali

Sicurezza:
- Le chiavi reali dei provider (OpenAI, Anthropic, etc.) NON
  vengono mai esposte all'utente
- Ogni VIO key è un HMAC(email_hash + provider + timestamp)
- Le VIO keys possono essere revocate/rigenerate istantaneamente
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ─── Costanti ────────────────────────────────────────────────────────

VIO_KEY_PREFIX = "vio83"
KEY_DERIVATION_SECRET_ENV = "VIO_KEY_DERIVATION_SECRET"
DB_PATH = Path("data/vio83_users.db")  # Stesso DB degli utenti

# Provider supportati nell'ecosistema VIO
SUPPORTED_PROVRS = {
    "ollama":      {"tier": "local",  "free": True,  "display": "Ollama (Locale)"},
    "groq":        {"tier": "free",   "free": True,  "display": "Groq Cloud"},
    "together":    {"tier": "free",   "free": True,  "display": "Together AI"},
    "openrouter":  {"tier": "free",   "free": True,  "display": "OpenRouter"},
    "deepseek":    {"tier": "paid",   "free": False, "display": "DeepSeek"},
    "mistral":     {"tier": "paid",   "free": False, "display": "Mistral AI"},
    "anthropic":   {"tier": "paid",   "free": False, "display": "Claude (Anthropic)"},
    "openai":      {"tier": "paid",   "free": False, "display": "GPT-4 (OpenAI)"},
    "xai":         {"tier": "paid",   "free": False, "display": "Grok (xAI)"},
    "gemini":      {"tier": "paid",   "free": False, "display": "Gemini (Google)"},
    "perplexity":  {"tier": "paid",   "free": False, "display": "Perplexity"},
}


@dataclass(frozen=True, slots=True)
class VioApiKey:
    """Una API key auto-generata per un utente + provider specifico."""
    key_id: str           # UUID
    user_id: str
    provider: str
    vio_key: str          # vio83_<provider>_<hash> — il token proxy
    created_at: float
    expires_at: float
    is_active: bool = True
    last_used: float = 0.0
    usage_count: int = 0


# ─── Key derivation ─────────────────────────────────────────────────

def _get_derivation_secret() -> str:
    """Ottieni il secret per la derivazione delle chiavi."""
    return os.environ.get(KEY_DERIVATION_SECRET_ENV, "vio83-orchestra-key-derivation-2026")


def derive_vio_key(email_hash: str, provider: str, timestamp: float) -> str:
    """
    Auto-genera una VIO API key unica per utente + provider.

    La chiave è un token derivato deterministicamente da:
    - email_hash (impronta digitale dell'utente)
    - provider (quale AI)
    - timestamp (quando generata)
    - derivation secret (segreto del platform)

    Formato: vio83_<provider>_<signature>
    """
    secret = _get_derivation_secret()
    payload = f"{email_hash}:{provider}:{timestamp}:{secret}"
    signature = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]
    return f"{VIO_KEY_PREFIX}_{provider}_{signature}"


def verify_vio_key_format(key: str) -> Optional[str]:
    """
    Verifica formato VIO key e ritorna il provider.
    Returns None se formato invalido.
    """
    if not key or not key.startswith(f"{VIO_KEY_PREFIX}_"):
        return None
    parts = key.split("_", 2)
    if len(parts) != 3:
        return None
    provider = parts[1]
    if provider not in SUPPORTED_PROVRS:
        return None
    return provider


# ─── API Key Vault Manager ──────────────────────────────────────────

class ApiKeyVaultManager:
    """
    Gestisce l'auto-generazione e il ciclo di vita delle API keys.

    Per ogni utente registrato:
    1. In base al piano acquistato, genera VIO keys per i provider inclusi
    2. Ogni VIO key è unica, legata all'email, revocabile
    3. Le master API keys reali restano solo nel server (passe-partout)
    4. L'utente vede solo le sue VIO keys personalizzate

    Come funziona nell'hotel:
    - L'utente (ospite) ha la sua chiave (VIO key)
    - L'hotel (VIO server) ha il passe-partout (master API keys)
    - La chiave dell'ospite apre SOLO la sua stanza (il suo set di AI)
    - Il passe-partout apre tutto (per admin/manutenzione)
    """

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _init_db(self) -> None:
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS user_api_keys (
                key_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                vio_key TEXT UNIQUE NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                is_active INTEGER DEFAULT 1,
                last_used REAL DEFAULT 0,
                usage_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user_id, provider)
            );

            CREATE TABLE IF NOT EXISTS key_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_uak_user ON user_api_keys(user_id);
            CREATE INDEX IF NOT EXISTS idx_uak_provr ON user_api_keys(provider);
            CREATE INDEX IF NOT EXISTS idx_uak_viokey ON user_api_keys(vio_key);
            CREATE INDEX IF NOT EXISTS idx_keylog_time ON key_usage_log(timestamp);
        """)

    # ─── Auto-generazione chiavi ────────────────────────────────────

    def generate_keys_for_user(
        self,
        user_id: str,
        email_hash: str,
        plan_provrs: list[str],
    ) -> list[VioApiKey]:
        """
        Auto-genera VIO API keys per tutti i provider nel piano dell'utente.

        Come un hotel che prepara le chiavi per tutte le stanze
        che il cliente ha prenotato.
        """
        generated: list[VioApiKey] = []
        now = time.time()
        expiry = now + (365 * 86400)  # 1 anno

        for provider in plan_provrs:
            if provider not in SUPPORTED_PROVRS:
                continue

            # Controlla se esiste già una chiave attiva
            existing = self._conn.execute(
                "SELECT key_id FROM user_api_keys WHERE user_id = ? AND provider = ? AND is_active = 1",
                (user_id, provider)
            ).fetchone()
            if existing:
                continue

            # Auto-genera la VIO key
            vio_key = derive_vio_key(email_hash, provider, now)
            key_id = str(secrets.token_hex(8))

            self._conn.execute(
                """INSERT INTO user_api_keys
                (key_id, user_id, provider, vio_key, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (key_id, user_id, provider, vio_key, now, expiry)
            )

            generated.append(VioApiKey(
                key_id=key_id, user_id=user_id, provider=provider,
                vio_key=vio_key, created_at=now, expires_at=expiry,
            ))

            self._log_key_action(key_id, user_id, provider, "generated")

        self._conn.commit()
        return generated

    # ─── Verifica e utilizzo chiave ─────────────────────────────────

    def verify_and_use_key(self, vio_key: str) -> Optional[VioApiKey]:
        """
        Verifica una VIO key e registra l'utilizzo.
        Come inserire la chiave nella serratura: funziona solo se è la giusta.
        """
        now = time.time()
        row = self._conn.execute(
            """SELECT key_id, user_id, provider, vio_key, created_at,
                      expires_at, is_active, last_used, usage_count
            FROM user_api_keys
            WHERE vio_key = ? AND is_active = 1 AND expires_at > ?""",
            (vio_key, now)
        ).fetchone()

        if not row:
            return None

        key = VioApiKey(
            key_id=row[0], user_id=row[1], provider=row[2],
            vio_key=row[3], created_at=row[4], expires_at=row[5],
            is_active=bool(row[6]), last_used=now, usage_count=row[8] + 1,
        )

        # Aggiorna utilizzo
        self._conn.execute(
            "UPDATE user_api_keys SET last_used = ?, usage_count = usage_count + 1 WHERE key_id = ?",
            (now, key.key_id)
        )
        self._conn.commit()

        return key

    # ─── Rigenerazione chiave ───────────────────────────────────────

    def regenerate_key(self, user_id: str, email_hash: str, provider: str) -> Optional[VioApiKey]:
        """
        Rigenera una VIO key per un provider.
        Come quando il cliente perde la chiave: l'hotel
        disattiva la vecchia e ne crea una nuova.
        """
        now = time.time()

        # Disattiva la vecchia chiave
        self._conn.execute(
            "UPDATE user_api_keys SET is_active = 0 WHERE user_id = ? AND provider = ?",
            (user_id, provider)
        )

        # Genera nuova chiave
        vio_key = derive_vio_key(email_hash, provider, now)
        key_id = str(secrets.token_hex(8))
        expiry = now + (365 * 86400)

        self._conn.execute(
            """INSERT INTO user_api_keys
            (key_id, user_id, provider, vio_key, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (key_id, user_id, provider, vio_key, now, expiry)
        )
        self._conn.commit()

        self._log_key_action(key_id, user_id, provider, "regenerated")

        return VioApiKey(
            key_id=key_id, user_id=user_id, provider=provider,
            vio_key=vio_key, created_at=now, expires_at=expiry,
        )

    # ─── Lista chiavi utente ────────────────────────────────────────

    def get_user_keys(self, user_id: str) -> list[dict]:
        """Lista tutte le VIO keys attive di un utente."""
        rows = self._conn.execute(
            """SELECT key_id, provider, vio_key, created_at, expires_at,
                      last_used, usage_count
            FROM user_api_keys
            WHERE user_id = ? AND is_active = 1
            ORDER BY provider""",
            (user_id,)
        ).fetchall()

        return [
            {
                "key_id": r[0],
                "provider": r[1],
                "vio_key": self._mask_key(r[2]),
                "provr_display": SUPPORTED_PROVRS.get(r[1], {}).get("display", r[1]),
                "created_at": r[3],
                "expires_at": r[4],
                "last_used": r[5],
                "usage_count": r[6],
            }
            for r in rows
        ]

    def get_user_active_provrs(self, user_id: str) -> list[str]:
        """Lista provider attivi per un utente."""
        rows = self._conn.execute(
            "SELECT provider FROM user_api_keys WHERE user_id = ? AND is_active = 1",
            (user_id,)
        ).fetchall()
        return [r[0] for r in rows]

    # ─── Revoca chiave ──────────────────────────────────────────────

    def revoke_key(self, user_id: str, provider: str) -> bool:
        """Revoca una chiave (come bloccare una chiave persa)."""
        self._conn.execute(
            "UPDATE user_api_keys SET is_active = 0 WHERE user_id = ? AND provider = ?",
            (user_id, provider)
        )
        self._conn.commit()
        self._log_key_action("", user_id, provider, "revoked")
        return True

    def revoke_all_user_keys(self, user_id: str) -> int:
        """Revoca tutte le chiavi di un utente (checkout dall'hotel)."""
        cursor = self._conn.execute(
            "UPDATE user_api_keys SET is_active = 0 WHERE user_id = ? AND is_active = 1",
            (user_id,)
        )
        self._conn.commit()
        return cursor.rowcount

    # ─── Master key resolution ──────────────────────────────────────

    def resolve_master_key(self, provider: str) -> Optional[str]:
        """
        Risolvi la master API key reale per un provider.
        Questo è il PASSE-PARTOUT: le chiavi reali dei provider
        che il sistema usa internamente per le chiamate AI.

        Le master keys vengono dalle variabili d'ambiente (.env).
        MAI esposte all'utente.
        """
        env_map = {
            "groq": "GROQ_API_KEY",
            "together": "TOGETHER_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "xai": "XAI_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "perplexity": "PERPLEXITY_API_KEY",
        }
        env_var = env_map.get(provider)
        if not env_var:
            return None
        return os.environ.get(env_var)

    # ─── Utility ────────────────────────────────────────────────────

    def _mask_key(self, key: str) -> str:
        """Maschera una VIO key per visualizzazione sicura."""
        if len(key) <= 16:
            return key[:8] + "..."
        return key[:16] + "..." + key[-4:]

    def _log_key_action(self, key_id: str, user_id: str, provider: str, action: str) -> None:
        try:
            self._conn.execute(
                "INSERT INTO key_usage_log (key_id, user_id, provider, action, timestamp) VALUES (?, ?, ?, ?, ?)",
                (key_id, user_id, provider, action, time.time())
            )
            self._conn.commit()
        except Exception:
            pass

    def get_stats(self) -> dict:
        total_keys = self._conn.execute(
            "SELECT COUNT(*) FROM user_api_keys WHERE is_active = 1"
        ).fetchone()[0]
        by_provr = {}
        for row in self._conn.execute(
            "SELECT provider, COUNT(*) FROM user_api_keys WHERE is_active = 1 GROUP BY provider"
        ):
            by_provr[row[0]] = row[1]
        return {"total_active_keys": total_keys, "by_provr": by_provr}

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


# ─── Singleton ──────────────────────────────────────────────────────

_INSTANCE: Optional[ApiKeyVaultManager] = None


def get_key_vault() -> ApiKeyVaultManager:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ApiKeyVaultManager()
    return _INSTANCE
