import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"


from datetime import UTC

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.database import Base, get_db
from src.core.security import hash_password
from src.models import *
from src.services.cache import cache as cache_service


@pytest.fixture(scope="session", autouse=True)
def mock_redis():
    """Mock Redis for all tests using fakeredis"""
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    # Patch the cache service
    cache_service._redis = redis
    cache_service._redis_url = "redis://fake"
    
    # Also mock init and close to be no-ops
    async def mock_init():
        pass
    async def mock_close():
        pass
    cache_service.init = mock_init
    cache_service.close = mock_close
    
    # In-memory blacklist tracking for tests
    _blacklist = set()

    async def mock_is_blacklisted(jti):
        return jti in _blacklist
    cache_service.is_token_blacklisted = mock_is_blacklisted
    
    async def mock_blacklist_token(jti, ttl):
        _blacklist.add(jti)
        return True
    cache_service.blacklist_token = mock_blacklist_token
    
    # Mock check_rate_limit to always succeed (avoid cross-test rate limit accumulation)
    async def mock_check_rate_limit(key, max_attempts, window):
        return True, 0
    cache_service.check_rate_limit = mock_check_rate_limit
    
    yield redis
    # Cleanup
    cache_service._redis = None


TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session", autouse=True)
def seed_permission_data(setup_database):
    from scripts.seed_permissions import seed_permissions
    session = TestingSessionLocal()
    seed_permissions(session)
    session.close()


@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    from src.main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def clinic(db_session):
    from src.models.clinic import Clinic
    clinic = Clinic(name="Test Clinic", address="Test Address", phone="123456789", email="test@clinic.com")
    db_session.add(clinic)
    db_session.commit()
    db_session.refresh(clinic)
    return clinic


@pytest.fixture(scope="function")
def vet_user(db_session, clinic):
    from src.models.user import User, UserRole
    user = User(
        clinic_id=clinic.id,
        name="Dr. Vet",
        email="vet@test.com",
        password_hash=hash_password("Password1"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def receptionist_user(db_session, clinic):
    from src.models.user import User, UserRole
    user = User(
        clinic_id=clinic.id,
        name="Receptionist",
        email="receptionist@test.com",
        password_hash=hash_password("Password1"),
        role=UserRole.RECEPTIONIST,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def vet_token(client, vet_user):
    response = client.post("/api/v1/auth/login", json={"email": "vet@test.com", "password": "Password1"})
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def receptionist_token(client, receptionist_user):
    response = client.post("/api/v1/auth/login", json={"email": "receptionist@test.com", "password": "Password1"})
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def vet_headers(vet_token):
    return {"Authorization": f"Bearer {vet_token}"}


@pytest.fixture(scope="function")
def receptionist_headers(receptionist_token):
    return {"Authorization": f"Bearer {receptionist_token}"}


@pytest.fixture(scope="function")
def owner(db_session, clinic):
    from src.models.owner import Owner
    owner = Owner(
        clinic_id=clinic.id,
        name="Test Owner",
        phone="+244 900 000 000",
        email="owner@test.com",
        address="Test Address",
        notes="Test notes",
    )
    db_session.add(owner)
    db_session.commit()
    db_session.refresh(owner)
    return owner


@pytest.fixture(scope="function")
def pet(db_session, clinic, owner):
    from decimal import Decimal

    from src.models.pet import Pet
    pet = Pet(
        clinic_id=clinic.id,
        owner_id=owner.id,
        name="Test Pet",
        species="Cão",
        breed="SRD",
        weight=Decimal("10.5"),
        notes="Test pet",
    )
    db_session.add(pet)
    db_session.commit()
    db_session.refresh(pet)
    return pet


@pytest.fixture(scope="function")
def appointment(db_session, clinic, pet, vet_user):
    from datetime import datetime, timedelta

    from src.models.appointment import Appointment, AppointmentStatus
    appointment = Appointment(
        clinic_id=clinic.id,
        pet_id=pet.id,
        vet_id=vet_user.id,
        owner_id=pet.owner_id,
        scheduled_at=datetime.now(UTC) + timedelta(days=1),
        duration_min=30,
        status=AppointmentStatus.SCHEDULED,
        reason="Test appointment",
        notes="Test notes",
    )
    db_session.add(appointment)
    db_session.commit()
    db_session.refresh(appointment)
    return appointment


@pytest.fixture(scope="function")
def treatment(db_session, clinic, appointment):
    from src.models.treatment import Treatment
    treatment = Treatment(
        clinic_id=clinic.id,
        appointment_id=appointment.id,
        diagnosis="Test diagnosis",
        notes="Test notes",
        prescription="Test prescription",
    )
    db_session.add(treatment)
    db_session.commit()
    db_session.refresh(treatment)
    return treatment


@pytest.fixture(scope="function")
def invoice(db_session, clinic, owner, appointment):
    from src.models.invoice import Invoice, InvoiceStatus
    invoice = Invoice(
        clinic_id=clinic.id,
        owner_id=owner.id,
        appointment_id=appointment.id,
        amount=100.0,
        status=InvoiceStatus.DRAFT,
        description="Test invoice",
    )
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)
    return invoice