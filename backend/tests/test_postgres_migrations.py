import os
import uuid
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def _admin_url() -> str:
    value = os.environ.get("POSTGRES_ADMIN_URL")
    if not value:
        pytest.skip("POSTGRES_ADMIN_URL is required for PostgreSQL migration tests")
    return value


def _database_url(database_name: str) -> str:
    from sqlalchemy.engine import make_url

    return make_url(_admin_url()).set(database=database_name).render_as_string(
        hide_password=False
    )


def _create_database(database_name: str) -> None:
    import psycopg2
    from psycopg2 import sql

    connection = psycopg2.connect(_admin_url())
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name)))
    finally:
        connection.close()


def _drop_database(database_name: str) -> None:
    import psycopg2
    from psycopg2 import sql

    connection = psycopg2.connect(_admin_url())
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()",
                (database_name,),
            )
            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(database_name)))
    finally:
        connection.close()


def _alembic_config(database_url: str):
    from alembic.config import Config

    from src.core.config import settings

    backend_root = Path(__file__).resolve().parents[1]
    settings.DATABASE_URL = database_url
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def test_migrations_build_empty_postgresql_database():
    from sqlalchemy import create_engine, inspect, text

    from alembic import command

    database_name = f"patas_empty_{uuid.uuid4().hex[:10]}"
    _create_database(database_name)
    database_url = _database_url(database_name)
    try:
        command.upgrade(_alembic_config(database_url), "head")
        engine = create_engine(database_url)
        try:
            inspector = inspect(engine)
            assert "must_change_password" in {
                column["name"] for column in inspector.get_columns("users")
            }
            assert {"archived_at", "archived_by_user_id"}.issubset(
                {column["name"] for column in inspector.get_columns("owners")}
            )
            with engine.connect() as connection:
                assert connection.execute(text(
                    "SELECT count(*) FROM pg_constraint "
                    "WHERE conname = 'ex_appointments_active_vet_overlap'"
                )).scalar_one() == 1
        finally:
            engine.dispose()
    finally:
        _drop_database(database_name)


def test_previous_database_upgrades_without_losing_data_and_blocks_overlap():
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import IntegrityError

    from alembic import command

    database_name = f"patas_upgrade_{uuid.uuid4().hex[:10]}"
    _create_database(database_name)
    database_url = _database_url(database_name)
    config = _alembic_config(database_url)
    try:
        command.upgrade(config, "20260909_clinical_waiting_room")
        engine = create_engine(database_url)
        try:
            with engine.begin() as connection:
                clinic_id = connection.execute(text(
                    "INSERT INTO clinics (name) VALUES ('Clínica preservada') RETURNING id"
                )).scalar_one()
                user_id = connection.execute(text(
                    "INSERT INTO users (clinic_id, name, email, password_hash, role) "
                    "VALUES (:clinic, 'Admin', 'migration@test.ao', 'hash', 'admin') RETURNING id"
                ), {"clinic": clinic_id}).scalar_one()
                owner_id = connection.execute(text(
                    "INSERT INTO owners (clinic_id, name) "
                    "VALUES (:clinic, 'Dono preservado') RETURNING id"
                ), {"clinic": clinic_id}).scalar_one()
                pet_id = connection.execute(text(
                    "INSERT INTO pets (clinic_id, owner_id, name, species) "
                    "VALUES (:clinic, :owner, 'Kalu', 'Cão') RETURNING id"
                ), {"clinic": clinic_id, "owner": owner_id}).scalar_one()
                appointment_id = connection.execute(text(
                    "INSERT INTO appointments "
                    "(clinic_id, pet_id, vet_id, owner_id, scheduled_at, duration_min, status) "
                    "VALUES (:clinic, :pet, :vet, :owner, '2026-10-01 09:00:00', NULL, 'scheduled') "
                    "RETURNING id"
                ), {
                    "clinic": clinic_id,
                    "pet": pet_id,
                    "vet": user_id,
                    "owner": owner_id,
                }).scalar_one()
        finally:
            engine.dispose()

        command.upgrade(config, "head")
        engine = create_engine(database_url)
        try:
            with engine.connect() as connection:
                row = connection.execute(text(
                    "SELECT duration_min, status FROM appointments WHERE id = :id"
                ), {"id": appointment_id}).one()
                assert row.duration_min == 30
                assert row.status == "scheduled"
                assert connection.execute(text(
                    "SELECT must_change_password FROM users WHERE id = :id"
                ), {"id": user_id}).scalar_one() is False
                assert connection.execute(text(
                    "SELECT archived_at FROM owners WHERE id = :id"
                ), {"id": owner_id}).scalar_one() is None

            with pytest.raises(IntegrityError), engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO appointments "
                    "(clinic_id, pet_id, vet_id, owner_id, scheduled_at, duration_min, status) "
                    "VALUES (:clinic, :pet, :vet, :owner, '2026-10-01 09:15:00', 30, 'scheduled')"
                ), {
                    "clinic": clinic_id,
                    "pet": pet_id,
                    "vet": user_id,
                    "owner": owner_id,
                })
        finally:
            engine.dispose()
    finally:
        _drop_database(database_name)
