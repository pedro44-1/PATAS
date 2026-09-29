"""Test that Alembic migrations generate valid SQL for PostgreSQL (offline mode)."""
import os

from alembic.config import Config

from alembic import command
from src.core.config import settings


def test_migrations():
    """Run migrations in offline mode to verify SQL syntax."""
    # Use PostgreSQL URL for offline mode testing
    pg_url = os.getenv("DATABASE_URL", "postgresql://patas:patas_dev_password@db:5432/patas")
    
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", pg_url)
    
    print("Testing migration SQL generation for PostgreSQL...")

    # Alembic owns the offline MigrationContext; configuring it a second time
    # is incompatible with newer Alembic releases.
    settings.DATABASE_URL = pg_url
    command.upgrade(cfg, "head", sql=True)
    
    print("\n✓ All migration SQL generated successfully for PostgreSQL")


if __name__ == "__main__":
    test_migrations()
