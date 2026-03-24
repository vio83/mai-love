# ============================================================
# VIO 83 AI ORCHESTRA — Copyright (c) 2026 Viorica Porcu (vio83)
# DUAL LICENSE: Proprietary + AGPL-3.0 — See LICENSE files
# ALL RIGHTS RESERVED — https://github.com/vio83/vio83-ai-orchestra
# ============================================================
"""
VIO 83 AI ORCHESTRA — Multi-Layer Cache Engine
Sistema di caching a due livelli:
- L1: In-memory LRU cache (velocissimo, volatile)
- L2: SQLite disk cache (persistente tra riavvii, con TTL)

Features:
- TTL (Time To Live) configurabile per entry
- LRU eviction per L1 (max entries configurabile)
- Cache stats e hit/miss ratio
- Cache invalidation per pattern
- Thread-safe con lock
- Serializzazione automatica JSON
"""

import os
import json
import time
import hashlib
import sqlite3
import threading
from collections import OrderedDict
from typing import Any, Optional, Callable
from functools import wraps


class L1MemoryCache:
    """
    Cache in-memory LRU (Least Recently Used).
    Velocità: ~100ns per lookup.
    Volatile: si perde al riavvio.
    """

    def __init__(self, max_size: int = 2048, default_ttl: int = 300):
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Recupera valore dalla cache L1."""
        with self._lock:
            if key in self._cache:
                value, expires = self._cache[key]
                if expires > time.time():
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return value
                else:
                    del self._cache[key]
            self._misses += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Salva valore nella cache L1."""
        ttl = ttl or self._default_ttl
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, time.time() + ttl)
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def delete(self, key: str):
        """Rimuovi entry specifica."""
        with self._lock:
            self._cache.pop(key, None)

    def invalidate_pattern(self, pattern: str):
        """Invalida tutte le entry che contengono il pattern nella chiave."""
        with self._lock:
            keys_to_delete = [k for k in self._cache if pattern in k]
            for k in keys_to_delete:
                del self._cache[k]

    def clear(self):
        """Svuota tutta la cache."""
        with self._lock:
            self._cache.clear()

    @property
    def stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "type": "memory_lru",
            "entries": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": round(self._hits / total, 4) if total > 0 else 0,
        }


class L2DiskCache:
    """
    Cache persistente su disco (SQLite).
    Sopravvive ai riavvii. TTL per entry.
    """

    def __init__(self, db_path: str = "./data/cache.db", default_ttl: int = 3600):
        self._db_path = db_path
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at REAL NOT NULL,
                created_at REAL NOT NULL,
                access_count INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")
        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path, timeout=5)

    def get(self, key: str) -> Optional[Any]:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
            ).fetchone()
            if row:
                value_json, expires_at = row
                if expires_at > time.time():
                    conn.execute(
                        "UPDATE cache SET access_count = access_count + 1 WHERE key = ?",
                        (key,)
                    )
                    conn.commit()
                    self._hits += 1
                    return json.loads(value_json)
                else:
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                    conn.commit()
            self._misses += 1
            return None
        finally:
            conn.close()

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        ttl = ttl or self._default_ttl
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at, created_at, access_count) "
                "VALUES (?, ?, ?, ?, 0)",
                (key, json.dumps(value, ensure_ascii=False), time.time() + ttl, time.time())
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, key: str):
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
        finally:
            conn.close()

    def invalidate_pattern(self, pattern: str):
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM cache WHERE key LIKE ?", (f"%{pattern}%",))
            conn.commit()
        finally:
            conn.close()

    def cleanup_expired(self) -> int:
        """Rimuovi tutte le entry scadute. Ritorna il numero eliminato."""
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                "DELETE FROM cache WHERE expires_at < ?", (time.time(),)
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def clear(self):
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM cache")
            conn.commit()
        finally:
            conn.close()

    @property
    def stats(self) -> dict:
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT COUNT(*) FROM cache WHERE expires_at > ?", (time.time(),)).fetchone()
            total_entries = row[0] if row else 0
            total = self._hits + self._misses
            return {
                "type": "disk_sqlite",
                "entries": total_entries,
                "hits": self._hits,
                "misses": self._misses,
                "hit_ratio": round(self._hits / total, 4) if total > 0 else 0,
                "db_path": self._db_path,
            }
        finally:
            conn.close()


class CacheEngine:
    """
    Multi-Layer Cache Engine.
    Cerca prima in L1 (memory), poi in L2 (disk).
    Scrive sempre in entrambi i livelli.
    """

    def __init__(
        self,
        l1_max_size: int = 2048,
        l1_ttl: int = 300,
        l2_db_path: str = "./data/cache.db",
        l2_ttl: int = 3600,
    ):
        self.l1 = L1MemoryCache(max_size=l1_max_size, default_ttl=l1_ttl)
        self.l2 = L2DiskCache(db_path=l2_db_path, default_ttl=l2_ttl)

    @staticmethod
    def make_key(*args, **kwargs) -> str:
        """Genera chiave cache deterministica da argomenti."""
        raw = json.dumps({"a": args, "k": kwargs}, sort_keys=True, default=str)
        return hashlib.blake2b(raw.encode(), digest_size=16).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Cerca in L1 poi L2."""
        result = self.l1.get(key)
        if result is not None:
            return result
        result = self.l2.get(key)
        if result is not None:
            self.l1.set(key, result)  # Promuovi a L1
            return result
        return None

    def set(self, key: str, value: Any, l1_ttl: Optional[int] = None, l2_ttl: Optional[int] = None):
        """Salva in entrambi i livelli."""
        self.l1.set(key, value, ttl=l1_ttl)
        self.l2.set(key, value, ttl=l2_ttl)

    def delete(self, key: str):
        self.l1.delete(key)
        self.l2.delete(key)

    def invalidate_pattern(self, pattern: str):
        self.l1.invalidate_pattern(pattern)
        self.l2.invalidate_pattern(pattern)

    def clear(self):
        self.l1.clear()
        self.l2.clear()

    def cleanup(self) -> int:
        return self.l2.cleanup_expired()

    @property
    def stats(self) -> dict:
        return {
            "l1": self.l1.stats,
            "l2": self.l2.stats,
        }


# === SINGLETON ===
_cache_engine: Optional[CacheEngine] = None


def get_cache(data_dir: str = "./data") -> CacheEngine:
    # Fallback a /tmp se il filesystem non supporta SQLite locking (es. VirtioFS/FUSE)
    _test_path = os.path.join(data_dir, "_sqlite_test.tmp")
    try:
        import sqlite3 as _sq
        _c = _sq.connect(_test_path, timeout=2)
        _c.execute("CREATE TABLE IF NOT EXISTS _t (x)")
        _c.commit(); _c.close()
        os.remove(_test_path)
    except Exception:
        data_dir = "/tmp/vio83_cache"
        os.makedirs(data_dir, exist_ok=True)
    """Ottieni istanza singleton del Cache Engine."""
    global _cache_engine
    if _cache_engine is None:
        _cache_engine = CacheEngine(l2_db_path=os.path.join(data_dir, "cache.db"))
    return _cache_engine


# === DECORATORE CACHE ===
def cached(ttl: int = 300, prefix: str = ""):
    """
    Decoratore per cachare automaticamente il risultato di una funzione.
    Supporta funzioni sync e async.

    Uso:
        @cached(ttl=600, prefix="ollama")
        async def call_model(prompt):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache()
            key = f"{prefix}:{func.__name__}:{cache.make_key(*args, **kwargs)}"
            result = cache.get(key)
            if result is not None:
                return result
            result = await func(*args, **kwargs)
            if result is not None:
                cache.set(key, result, l1_ttl=min(ttl, 300), l2_ttl=ttl)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache()
            key = f"{prefix}:{func.__name__}:{cache.make_key(*args, **kwargs)}"
            result = cache.get(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            if result is not None:
                cache.set(key, result, l1_ttl=min(ttl, 300), l2_ttl=ttl)
            return result

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
