# ============================================================
# VIO 83 AI ORCHESTRA — User Authentication System
# Copyright © 2026 Viorica Porcu (vio83) — All rights reserved
# ============================================================
"""
Sistema di autenticazione utente basato su email ("impronta digitale").

Ogni utente:
1. Acquista l'app → riceve codice acquisto
2. Si registra con email personale (unica al mondo)
3. L'email diventa la sua "impronta digitale"
4. API keys auto-generate in base a email + piano scelto

Schema hotel:
- Email = chiave della stanza (unica per ogni ospite)
- Master key = passe-partout amministrativo
- Piano = tipo di stanza (quali servizi AI includere)
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    _ARGON2 = PasswordHasher(
        time_cost=3,        # 3 iterazioni
        memory_cost=65536,  # 64 MB
        parallelism=1,      # 1 thread
    )
    HAS_ARGON2 = True
except ImportError:
    HAS_ARGON2 = False

# ─── Costanti ────────────────────────────────────────────────────────

_RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
TOKEN_EXPIRY_SECONDS = 86400 * 30  # 30 giorni
MASTER_KEY_ENV = "VIO_MASTER_KEY"
PURCHASE_SECRET_ENV = "VIO_PURCHASE_SECRET"
DB_PATH = Path("data/vio83_users.db")


@dataclass(slots=True)
class UserProfile:
    """Profilo utente registrato."""
    user_id: str
    email: str
    email_hash: str  # SHA-256 dell'email = impronta digitale
    plan_id: str
    activated_at: float
    last_login: float
    is_active: bool = True


@dataclass(slots=True)
class AuthToken:
    """Token di sessione utente."""
    token: str
    user_id: str
    email: str
    plan_id: str
    created_at: float
    expires_at: float


@dataclass(slots=True)
class AuthResult:
    """Risultato di un'operazione di autenticazione."""
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[UserProfile] = None


# ─── Utility sicure ─────────────────────────────────────────────────

def _hash_email(email: str) -> str:
    """Genera l'impronta digitale dall'email (SHA-256, irreversibile)."""
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def _hash_password(password: str, salt: str = "") -> str:
    """
    Hash password con argon2id (standard OWASP).
    Fallback a HMAC-SHA256 se argon2 non è installato.
    Il salt è incorporato nell'hash argon2 (non serve salt separato).
    """
    if HAS_ARGON2:
        return _ARGON2.hash(password)
    # Fallback legacy HMAC-SHA256 (solo se argon2 non disponibile)
    if not salt:
        salt = secrets.token_hex(16)
    return "legacy:" + hmac.new(
        salt.encode("utf-8"),
        password.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _verify_password(password: str, stored_hash: str, salt: str = "") -> bool:
    """
    Verifica password contro hash.
    Supporta sia argon2id (nuovo) che HMAC-SHA256 (legacy migration).
    """
    if HAS_ARGON2 and stored_hash.startswith("$argon2"):
        try:
            return _ARGON2.verify(stored_hash, password)
        except VerifyMismatchError:
            return False
    # Legacy HMAC-SHA256 path
    legacy_hash = stored_hash.removeprefix("legacy:")
    computed = hmac.new(
        salt.encode("utf-8"),
        password.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed, legacy_hash)


def _generate_token() -> str:
    """Genera un token di sessione sicuro (256 bit)."""
    return secrets.token_urlsafe(32)


def _generate_purchase_code(email: str) -> str:
    """
    Genera codice di verifica acquisto basato su email + secret.
    In produzione: questo viene generato dal payment provider.
    """
    secret = os.environ.get(PURCHASE_SECRET_ENV, "vio83-default-purchase-secret")
    raw = hmac.new(
        secret.encode("utf-8"),
        email.strip().lower().encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:16].upper()
    return f"VIO-{raw[:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}"


def validate_email(email: str) -> bool:
    """Valida formato email."""
    return bool(_RE_EMAIL.match(email.strip())) and len(email) <= 254


# ─── User Auth Manager ──────────────────────────────────────────────

class UserAuthManager:
    """
    Gestisce registrazione, autenticazione e sessioni utente.

    Modello: email come impronta digitale unica.
    Ogni utente = 1 email = 1 set di API keys auto-generate.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection = sqlite3.connect(":memory:")  # placeholder
        self._init_db()

    def _init_db(self) -> None:
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                email_hash TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                plan_id TEXT NOT NULL DEFAULT 'free_local',
                purchase_code TEXT,
                purchase_verified INTEGER DEFAULT 0,
                activated_at REAL NOT NULL,
                last_login REAL,
                is_active INTEGER DEFAULT 1,
                is_admin INTEGER DEFAULT 0,
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS auth_tokens (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                revoked INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS auth_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                email_hash TEXT,
                action TEXT NOT NULL,
                success INTEGER NOT NULL,
                ip_address TEXT,
                timestamp REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_hash ON users(email_hash);
            CREATE INDEX IF NOT EXISTS idx_tokens_user ON auth_tokens(user_id);
            CREATE INDEX IF NOT EXISTS idx_tokens_expiry ON auth_tokens(expires_at);
            CREATE INDEX IF NOT EXISTS idx_auth_log_time ON auth_log(timestamp);
        """)

    # ─── Registrazione ──────────────────────────────────────────────

    def register(
        self,
        email: str,
        password: str,
        purchase_code: str,
        plan_id: str = "starter",
    ) -> AuthResult:
        """
        Registra un nuovo utente.

        Flusso:
        1. Valida email (impronta digitale)
        2. Verifica codice acquisto
        3. Crea utente con email_hash unico
        4. Genera token di sessione
        """
        email = email.strip().lower()

        if not validate_email(email):
            return AuthResult(False, "Email non valida")

        if len(password) < 8:
            return AuthResult(False, "Password: minimo 8 caratteri")

        # Verifica codice acquisto
        expected_code = _generate_purchase_code(email)
        # Accetta il codice generato O il master override
        master_key = os.environ.get(MASTER_KEY_ENV, "")
        is_master = master_key and purchase_code == master_key

        if not is_master and not hmac.compare_digest(purchase_code.upper(), expected_code):
            self._log_action(None, _hash_email(email), "register_failed_code", False)
            return AuthResult(False, "Codice acquisto non valido")

        # Verifica unicità email
        email_hash = _hash_email(email)
        if self._conn.execute("SELECT 1 FROM users WHERE email_hash = ?", (email_hash,)).fetchone():
            return AuthResult(False, "Email già registrata")

        # Crea utente
        user_id = str(uuid.uuid4())
        salt = secrets.token_hex(16)
        password_hash = _hash_password(password, salt)
        now = time.time()

        self._conn.execute(
            """INSERT INTO users
            (user_id, email, email_hash, password_hash, password_salt,
             plan_id, purchase_code, purchase_verified, activated_at, last_login)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (user_id, email, email_hash, password_hash, salt,
             plan_id, purchase_code, now, now)
        )

        # Genera token
        token = _generate_token()
        self._conn.execute(
            "INSERT INTO auth_tokens (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, now, now + TOKEN_EXPIRY_SECONDS)
        )
        self._conn.commit()

        self._log_action(user_id, email_hash, "register", True)

        user = UserProfile(
            user_id=user_id, email=email, email_hash=email_hash,
            plan_id=plan_id, activated_at=now, last_login=now,
        )
        return AuthResult(True, "Registrazione completata", token=token, user=user)

    # ─── Login ──────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> AuthResult:
        """
        Autentica un utente esistente.
        Genera nuovo token di sessione.
        """
        email = email.strip().lower()
        email_hash = _hash_email(email)

        row = self._conn.execute(
            "SELECT user_id, password_hash, password_salt, plan_id, activated_at, is_active "
            "FROM users WHERE email_hash = ?",
            (email_hash,)
        ).fetchone()

        if not row:
            self._log_action(None, email_hash, "login_failed_email", False)
            return AuthResult(False, "Credenziali non valide")

        user_id, stored_hash, salt, plan_id, activated_at, is_active = row

        if not is_active:
            self._log_action(user_id, email_hash, "login_failed_inactive", False)
            return AuthResult(False, "Account disattivato")

        if not _verify_password(password, stored_hash, salt):
            self._log_action(user_id, email_hash, "login_failed_password", False)
            return AuthResult(False, "Credenziali non valide")

        # Auto-migrate da HMAC-SHA256 a argon2id al primo login valido
        if HAS_ARGON2 and not stored_hash.startswith("$argon2"):
            new_hash = _hash_password(password)
            self._conn.execute(
                "UPDATE users SET password_hash = ?, password_salt = '' WHERE user_id = ?",
                (new_hash, user_id)
            )

        # Revoca vecchi token scaduti
        now = time.time()
        self._conn.execute(
            "UPDATE auth_tokens SET revoked = 1 WHERE user_id = ? AND expires_at < ?",
            (user_id, now)
        )

        # Genera nuovo token
        token = _generate_token()
        self._conn.execute(
            "INSERT INTO auth_tokens (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, now, now + TOKEN_EXPIRY_SECONDS)
        )

        # Aggiorna last_login
        self._conn.execute(
            "UPDATE users SET last_login = ? WHERE user_id = ?",
            (now, user_id)
        )
        self._conn.commit()

        self._log_action(user_id, email_hash, "login", True)

        user = UserProfile(
            user_id=user_id, email=email, email_hash=email_hash,
            plan_id=plan_id, activated_at=activated_at, last_login=now,
        )
        return AuthResult(True, "Login effettuato", token=token, user=user)

    # ─── Verifica token ─────────────────────────────────────────────

    def verify_token(self, token: str) -> Optional[UserProfile]:
        """
        Verifica un token di sessione.
        Ritorna UserProfile se valido, None se scaduto/revocato.
        """
        if not token:
            return None

        row = self._conn.execute(
            """SELECT u.user_id, u.email, u.email_hash, u.plan_id,
                      u.activated_at, u.last_login, u.is_active
            FROM auth_tokens t
            JOIN users u ON t.user_id = u.user_id
            WHERE t.token = ? AND t.revoked = 0 AND t.expires_at > ? AND u.is_active = 1""",
            (token, time.time())
        ).fetchone()

        if not row:
            return None

        return UserProfile(
            user_id=row[0], email=row[1], email_hash=row[2],
            plan_id=row[3], activated_at=row[4], last_login=row[5],
            is_active=bool(row[6]),
        )

    # ─── Master key (passe-partout) ─────────────────────────────────

    def verify_master_key(self, key: str) -> bool:
        """
        Verifica la chiave master (passe-partout).
        Come la chiave dell'hotel che apre tutte le porte.
        """
        master = os.environ.get(MASTER_KEY_ENV, "")
        if not master:
            return False
        return hmac.compare_digest(key, master)

    # ─── Logout ─────────────────────────────────────────────────────

    def logout(self, token: str) -> bool:
        """Revoca il token (logout)."""
        self._conn.execute(
            "UPDATE auth_tokens SET revoked = 1 WHERE token = ?",
            (token,)
        )
        self._conn.commit()
        return True

    # ─── Aggiornamento piano ────────────────────────────────────────

    def update_plan(self, user_id: str, new_plan_id: str) -> bool:
        """Aggiorna il piano dell'utente (upgrade/downgrade)."""
        self._conn.execute(
            "UPDATE users SET plan_id = ? WHERE user_id = ?",
            (new_plan_id, user_id)
        )
        self._conn.commit()
        self._log_action(user_id, "", "plan_change", True)
        return True

    # ─── Utility ────────────────────────────────────────────────────

    def _log_action(self, user_id: Optional[str], email_hash: str, action: str, success: bool) -> None:
        try:
            self._conn.execute(
                "INSERT INTO auth_log (user_id, email_hash, action, success, timestamp) VALUES (?, ?, ?, ?, ?)",
                (user_id, email_hash, action, int(success), time.time())
            )
            self._conn.commit()
        except Exception:
            pass

    def get_user_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM users WHERE is_active = 1").fetchone()
        return row[0] if row else 0

    def get_stats(self) -> dict:
        total = self.get_user_count()
        plans = {}
        for row in self._conn.execute(
            "SELECT plan_id, COUNT(*) FROM users WHERE is_active = 1 GROUP BY plan_id"
        ):
            plans[row[0]] = row[1]
        return {"total_users": total, "plans": plans}

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = sqlite3.connect(":memory:")  # reset to dummy


# ─── Singleton ──────────────────────────────────────────────────────

_INSTANCE: Optional[UserAuthManager] = None


def get_user_auth() -> UserAuthManager:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = UserAuthManager()
    return _INSTANCE
