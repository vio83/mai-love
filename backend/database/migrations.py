# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ALL RIGHTS RESERVED — https://github.com/vio83/vio83-ai-orchestra
# ============================================================
"""
VIO 83 AI ORCHESTRA — Database Migrations
Sistema di migrazione schema incrementale per SQLite.
Ogni migrazione viene eseguita una sola volta, tracking in schema_version.
"""

import sqlite3
import time

from backend.database.db import get_connection

MIGRATIONS: list[tuple[int, str, str]] = [
    # (version, description, SQL)
    (1, "Initial schema — baseline",
     "SELECT 1"),  # Baseline: lo schema iniziale è creato da init_database

    (2, "Add cost_usd to provider_metrics",
     """ALTER TABLE provider_metrics ADD COLUMN cost_usd REAL DEFAULT 0.0"""),

    (3, "Add category column to provider_metrics",
     """ALTER TABLE provider_metrics ADD COLUMN category TEXT DEFAULT ''"""),

    (4, "Add cross_check_results table",
     """CREATE TABLE IF NOT EXISTS cross_check_results (
         id TEXT PRIMARY KEY,
         conversation_id TEXT,
         query TEXT NOT NULL,
         primary_provider TEXT NOT NULL,
         primary_model TEXT NOT NULL,
         secondary_provider TEXT NOT NULL,
         secondary_model TEXT NOT NULL,
         concordance_score REAL NOT NULL DEFAULT 0.0,
         level TEXT NOT NULL CHECK(level IN ('full_agree', 'partial', 'disagree')),
         verdict TEXT,
         primary_response TEXT,
         secondary_response TEXT,
         timestamp REAL NOT NULL,
         FOREIGN KEY (conversation_id)
             REFERENCES conversations(id) ON DELETE SET NULL
     )"""),

    (5, "Add workflows table",
     """CREATE TABLE IF NOT EXISTS workflows (
         id TEXT PRIMARY KEY,
         name TEXT NOT NULL,
         description TEXT DEFAULT '',
         nodes_json TEXT NOT NULL DEFAULT '[]',
         connections_json TEXT NOT NULL DEFAULT '[]',
         active INTEGER NOT NULL DEFAULT 1,
         runs INTEGER NOT NULL DEFAULT 0,
         created_at REAL NOT NULL,
         updated_at REAL NOT NULL
     )"""),

    (6, "Add rag_sources table for KB tracking",
     """CREATE TABLE IF NOT EXISTS rag_sources (
         id TEXT PRIMARY KEY,
         name TEXT NOT NULL,
         documents_count INTEGER NOT NULL DEFAULT 0,
         status TEXT NOT NULL DEFAULT 'queued'
             CHECK(status IN ('indexed', 'indexing', 'queued', 'error')),
         quality TEXT NOT NULL DEFAULT 'unverified'
             CHECK(quality IN ('gold', 'silver', 'bronze', 'unverified')),
         category TEXT DEFAULT '',
         icon TEXT DEFAULT '',
         last_updated REAL NOT NULL
     )"""),

    (7, "Index cross_check_results by conversation",
     """CREATE INDEX IF NOT EXISTS idx_crosscheck_conv
        ON cross_check_results(conversation_id)"""),

    (8, "Index workflows by updated_at",
     """CREATE INDEX IF NOT EXISTS idx_workflows_updated
        ON workflows(updated_at DESC)"""),
]


def _ensure_version_table(conn: sqlite3.Connection) -> None:
    """Crea la tabella schema_version se non esiste."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at REAL NOT NULL
        )
    """)


def get_current_version(conn: sqlite3.Connection) -> int:
    """Restituisce la versione corrente dello schema."""
    _ensure_version_table(conn)
    row = conn.execute(
        "SELECT MAX(version) as v FROM schema_version"
    ).fetchone()
    return row["v"] if row and row["v"] is not None else 0


def run_migrations() -> int:
    """
    Esegue tutte le migrazioni pendenti.
    Restituisce il numero di migrazioni applicate.
    """
    applied = 0
    with get_connection() as conn:
        current = get_current_version(conn)

        for version, description, sql in MIGRATIONS:
            if version <= current:
                continue
            try:
                conn.execute(sql)
                conn.execute(
                    "INSERT INTO schema_version (version, description, applied_at) "
                    "VALUES (?, ?, ?)",
                    (version, description, time.time()),
                )
                applied += 1
                print(f"  ✅ Migrazione v{version}: {description}")
            except sqlite3.OperationalError as exc:
                # ALTER TABLE su colonna già esistente → skip silenzioso
                msg = str(exc).lower()
                if "duplicate column" in msg or "already exists" in msg:
                    conn.execute(
                        "INSERT OR IGNORE INTO schema_version "
                        "(version, description, applied_at) VALUES (?, ?, ?)",
                        (version, description, time.time()),
                    )
                    print(f"  ⏭️  Migrazione v{version}: già applicata ({exc})")
                    applied += 1
                else:
                    raise

    if applied:
        print(f"📦 Migrazioni completate: {applied} applicate (schema v{current + applied})")
    return applied
