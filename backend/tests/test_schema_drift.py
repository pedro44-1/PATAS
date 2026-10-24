from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Enum, UniqueConstraint, create_engine

from alembic import command


SQLITE_EQUIVALENT_INDEXES = {"ix_invoice_lines_id", "uq_invoices_external_reference"}


def _significant(diff) -> bool:
    entry = diff[0] if isinstance(diff, list) else diff
    kind = entry[0]
    if kind == "modify_type":
        existing, target = entry[5], entry[6]
        if isinstance(target, Enum) and not target.native_enum:
            return False
        return existing.__class__.__name__ != target.__class__.__name__ or (
            getattr(existing, "length", None) != getattr(target, "length", None)
        )
    if kind in {"add_index", "remove_index"}:
        return entry[1].name not in SQLITE_EQUIVALENT_INDEXES
    if kind == "add_constraint" and isinstance(entry[1], UniqueConstraint):
        return [column.name for column in entry[1].columns] != ["external_reference"]
    return kind not in {"remove_fk", "add_fk"}


def test_alembic_head_matches_models(tmp_path):
    from alembic.config import Config

    from src.core.config import settings
    from src.core.database import Base

    backend_root = Path(__file__).resolve().parents[1]
    database_url = f"sqlite:///{(tmp_path / 'drift.db').as_posix()}"
    previous_url = settings.DATABASE_URL
    settings.DATABASE_URL = database_url
    try:
        config = Config(str(backend_root / "alembic.ini"))
        config.set_main_option("script_location", str(backend_root / "alembic"))
        config.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(config, "head")
    finally:
        settings.DATABASE_URL = previous_url

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(
                connection, opts={"compare_type": True}
            )
            diffs = [diff for diff in compare_metadata(context, Base.metadata) if _significant(diff)]
    finally:
        engine.dispose()

    assert diffs == []
