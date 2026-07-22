"""Populate the database with demo data for development/testing."""
import random
from datetime import datetime, timezone, timedelta
from src.core.database import SessionLocal
from src.core.security import hash_password
from src.models.clinic import Clinic
from src.models.user import User, UserRole
from src.models.owner import Owner
from src.models.pet import Pet
from src.models.appointment import Appointment, AppointmentStatus
from src.models.treatment import Treatment
from src.models.invoice import Invoice, InvoiceStatus
from scripts.seed_permissions import seed_permissions


def seed_demo():
    db = SessionLocal()

    try:
        seed_permissions(db)

        clinic = Clinic(name="ClГ­nica Animal Central")
        db.add(clinic)
        db.flush()

        vet = User(
            clinic_id=clinic.id,
            name="Dr. AntГіnio Silva",
            email="vet@patas.ao",
            password_hash=hash_password("Password1"),
            role=UserRole.VET,
        )
        receptionist = User(
            clinic_id=clinic.id,
            name="Maria Santos",
            email="receptionist@patas.ao",
            password_hash=hash_password("Password1"),
            role=UserRole.RECEPTIONIST,
        )
        db.add_all([vet, receptionist])
        db.flush()

        owners = [
            Owner(clinic_id=clinic.id, name="JoГЈo Mendes", phone="+244 923 456 789", email="joao@email.ao"),
            Owner(clinic_id=clinic.id, name="Ana Costa", phone="+244 912 345 678", email="ana@email.ao"),
            Owner(clinic_id=clinic.id, name="Pedro Ngola", phone="+244 934 567 890", email="pedro@email.ao"),
        ]
        db.add_all(owners)
        db.flush()

        pets = [
            Pet(clinic_id=clinic.id, owner_id=owners[0].id, name="Rex", species="cГЈo", breed="Pastor AlemГЈo", age="3 anos", weight=32.5),
            Pet(clinic_id=clinic.id, owner_id=owners[0].id, name="Mimi", species="gato", breed="SiamГЄs", age="5 anos", weight=4.2),
            Pet(clinic_id=clinic.id, owner_id=owners[1].id, name="Buddy", species="cГЈo", breed="Labrador", age="1 ano", weight=28.0),
            Pet(clinic_id=clinic.id, owner_id=owners[2].id, name="Luna", species="cГЈo", breed="SRD", age="2 anos", weight=15.0),
            Pet(clinic_id=clinic.id, owner_id=owners[2].id, name="Pipoca", species="gato", breed="SRD", age="8 meses", weight=3.1),
        ]
        db.add_all(pets)
        db.flush()

        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
        appointments = [
            Appointment(clinic_id=clinic.id, pet_id=pets[0].id, vet_id=vet.id, owner_id=pets[0].owner_id, scheduled_at=today_start, reason="VacinaГ§ГЈo anual", status=AppointmentStatus.COMPLETED),
            Appointment(clinic_id=clinic.id, pet_id=pets[1].id, vet_id=vet.id, owner_id=pets[1].owner_id, scheduled_at=today_start + timedelta(hours=1), reason="Check-up", status=AppointmentStatus.SCHEDULED),
            Appointment(clinic_id=clinic.id, pet_id=pets[2].id, vet_id=vet.id, owner_id=pets[2].owner_id, scheduled_at=today_start + timedelta(hours=2), reason="Ferimento na pata", status=AppointmentStatus.SCHEDULED),
            Appointment(clinic_id=clinic.id, pet_id=pets[3].id, vet_id=vet.id, owner_id=pets[3].owner_id, scheduled_at=today_start + timedelta(days=1), reason="Consulta geral", status=AppointmentStatus.SCHEDULED),
            Appointment(clinic_id=clinic.id, pet_id=pets[4].id, vet_id=vet.id, owner_id=pets[4].owner_id, scheduled_at=today_start + timedelta(days=2), reason="VacinaГ§ГЈo", status=AppointmentStatus.SCHEDULED),
        ]
        db.add_all(appointments)
        db.flush()

        treatment = Treatment(
            clinic_id=clinic.id,
            appointment_id=appointments[0].id,
            diagnosis="Animal saudГЎvel. VacinaГ§ГЈo V10 administrada.",
            prescription="ReforГ§o em 12 meses.",
            notes="Sem reacГ§Гµes adversas.",
        )
        db.add(treatment)
        db.flush()

        invoices = [
            Invoice(clinic_id=clinic.id, owner_id=owners[0].id, appointment_id=appointments[0].id, amount=8500.0, status=InvoiceStatus.PAID, description="VacinaГ§ГЈo V10 + consulta"),
            Invoice(clinic_id=clinic.id, owner_id=owners[1].id, appointment_id=appointments[2].id, amount=12500.0, status=InvoiceStatus.DRAFT, description="Penso + consulta"),
        ]
        db.add_all(invoices)
        db.flush()

        db.commit()
        print("Demo data seeded successfully!")
        print(f"  Clinic: {clinic.name.encode('ascii', 'replace').decode()}")
        print(f"  Vet: {vet.email} / Password1")
        print(f"  Receptionist: {receptionist.email} / Password1")
        print(f"  Owners: {len(owners)}")
        print(f"  Pets: {len(pets)}")
        print(f"  Appointments: {len(appointments)}")
        print(f"  Invoices: {len(invoices)}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding demo data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo()
