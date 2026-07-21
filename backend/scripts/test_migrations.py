"""Test that Alembic migrations generate valid SQL for PostgreSQL (offline mode)."""
import os
import sys
from alembic.config import Config
from alembic import command
from app.core.config import settings


def test_migrations():
    """Run migrations in offline mode to verify SQL syntax."""
    # Use PostgreSQL URL for offline mode testing
    pg_url = os.getenv("DATABASE_URL", "postgresql://patas:patas_dev_password@db:5432/patas")
    
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", pg_url)
    
    # Test upgrade to head in offline mode (generates SQL without executing)
    # We'll just run upgrade with sql=True to see the generated SQL
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory
    from sqlalchemy import create_engine
    
    engine = create_engine(pg_url, strategy="mock", executor=lambda *args, **kwargs: None)
    
    context = MigrationContext.configure(engine)
    script = ScriptDirectory.from_config(cfg)
    
    print("Testing migration SQL generation for PostgreSQL...")
    
    def process_revision_directives(context, revision, directives):
        for directive in directives:
            print(f"\n--- Migration: {directive.revision} ({directive.doc}) ---")
            for op in directive.ops:
                print(op)
    
    context.configure(
        url=pg_url,
        target_metadata=None,
        process_revision_directives=process_revision_directives,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    
    with context.begin_transaction():
        context.run_migrations()
    
    print("\n✓ All migration SQL generated successfully for PostgreSQL")


if __name__ == "__main__":
    test_migrations()