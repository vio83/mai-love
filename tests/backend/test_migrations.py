"""
Tests per il sistema di migrazione schema.
"""
import os
import sqlite3
import tempfile
import pytest

# Override DB_PATH prima dell'import per usare un DB temporaneo
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_path = _tmp.name
_tmp.close()
os.environ["VIO83_DB_PATH_OVERRIDE"] = _tmp_path

from backend.database.db import init_database, get_connection  # noqa: E402
from backend.database.migrations import (  # noqa: E402
    get_current_version,
    run_migrations,
    MIGRATIONS,
    _ensure_version_table,
)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """Crea un database fresco per ogni test."""
    db_file = str(tmp_path / "test_migrations.db")
    monkeypatch.setattr("backend.database.db.DB_PATH", db_file)
    monkeypatch.setattr("backend.database.db.DB_DIR", str(tmp_path))
    init_database()
    yield db_file


class TestMigrations:
    def test_migrations_list_is_sequential(self):
        """Le migrazioni devono avere version crescente."""
        versions = [m[0] for m in MIGRATIONS]
        assert versions == sorted(versions), "Migrazioni non in ordine sequenziale"
        assert len(versions) == len(set(versions)), "Versioni duplicate"

    def test_get_current_version_starts_at_zero(self):
        with get_connection() as conn:
            v = get_current_version(conn)
            assert v == 0

    def test_run_migrations_applies_all(self):
        applied = run_migrations()
        assert applied == len(MIGRATIONS)
        with get_connection() as conn:
            v = get_current_version(conn)
            assert v == MIGRATIONS[-1][0]

    def test_run_migrations_idempotent(self):
        run_migrations()
        applied_second = run_migrations()
        assert applied_second == 0, "Seconda esecuzione non deve applicare nulla"

    def test_version_table_tracks_all(self):
        run_migrations()
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT version, description FROM schema_version ORDER BY version"
            ).fetchall()
            assert len(rows) == len(MIGRATIONS)
            for row, (version, desc, _) in zip(rows, MIGRATIONS):
                assert row["version"] == version
                assert row["description"] == desc

    def test_cross_check_results_table_created(self):
        """La migrazione v4 crea la tabella cross_check_results."""
        run_migrations()
        with get_connection() as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
            assert "cross_check_results" in tables

    def test_workflows_table_created(self):
        """La migrazione v5 crea la tabella workflows."""
        run_migrations()
        with get_connection() as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
            assert "workflows" in tables

    def test_rag_sources_table_created(self):
        """La migrazione v6 crea la tabella rag_sources."""
        run_migrations()
        with get_connection() as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
            assert "rag_sources" in tables

    def test_provr_metrics_has_cost_column(self):
        """La migrazione v2 aggiunge cost_usd a provr_metrics."""
        run_migrations()
        with get_connection() as conn:
            info = conn.execute("PRAGMA table_info(provr_metrics)").fetchall()
            columns = [r["name"] for r in info]
            assert "cost_usd" in columns

    def test_provr_metrics_has_category_column(self):
        """La migrazione v3 aggiunge category a provr_metrics."""
        run_migrations()
        with get_connection() as conn:
            info = conn.execute("PRAGMA table_info(provr_metrics)").fetchall()
            columns = [r["name"] for r in info]
            assert "category" in columns
