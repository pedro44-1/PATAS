"""Seed script вЂ” run once to populate the database with realistic test data."""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import random

from sqlalchemy.orm import Session

from src.core.database import SessionLocal, engine
from src.core.security import hash_password
from src.models.clinic import Clinic
from src.models.owner import Owner
from src.models.pet import Pet
from src.models.appointment import Appointment, AppointmentStatus
from src.models.user import User, UserRole
from src.models.invoice import Invoice, InvoiceStatus as InvStatus
from src.models.treatment import Treatment


def seed(db: Session) -> None:
    # в”Ђв”Ђ 1. Clinic в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    clinic = db.query(Clinic).first()
    if not clinic:
        clinic = Clinic(name="ClГ­nica VeterinГЎria Luanda Sul")
        db.add(clinic)
        db.commit()
        db.refresh(clinic)

    print(f"Clinic: {clinic.name} (id={clinic.id})")

    # в”Ђв”Ђ 2. Users в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    users_data = [
        ("Dr. Ana Sousa",    "ana@patas.ao",    "vet"),
        ("Dr. JoГЈo Mendes",  "joao@patas.ao",   "vet"),
        ("Carla Reception",   "carla@patas.ao",  "receptionist"),
    ]
    users = []
    for name, email, role in users_data:
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            u = User(
                clinic_id=clinic.id,
                name=name,
                email=email,
                password_hash=hash_password("patas2026"),
                role=UserRole(role),
            )
            db.add(u)
        else:
            u = existing
        users.append(u)
    db.commit()
    for u in users:
        print(f"  User: {u.name} ({u.email}) вЂ” {u.role.value}")

    vets = [u for u in users if u.role == UserRole.VET]
    vet = vets[0]

    # в”Ђв”Ђ 3. Owners в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    owners_data = [
        ("Maria do Carmo",     "maria.carmo@gmail.com",     "+244 923 456 789", "Rua Major Kanhangulo, Luanda"),
        ("AntГіnio JoГЈo",      "antonio.joao@ymail.com",    "+244 934 567 890", "Rua Comandante Gika, Benfica"),
        ("Fernanda Pacavira",  "fernanda.p@gmail.com",      "+244 945 678 901", "Rua Timor, Talatona"),
        ("Carlos Eduardo",     "carlos.edu@outlook.com",    "+244 956 789 012", "Rua Comandante ValГіdia, Maianga"),
        ("JesuГ­na Francisco",  "jesuina.francisco@gmail.com","+244 921 234 567", "Rua Comandante Ncondo, Kilamba"),
    ]

    owners = []
    for name, email, phone, address in owners_data:
        existing = db.query(Owner).filter(Owner.email == email).first()
        if not existing:
            o = Owner(
                clinic_id=clinic.id,
                name=name,
                email=email,
                phone=phone,
                address=address,
            )
            db.add(o)
            db.commit()
            db.refresh(o)
        else:
            o = existing
        owners.append(o)

    print(f"  {len(owners)} owners seeded")

    # в”Ђв”Ђ 4. Pets в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    pet_names = ["Bubi", "Nala", "Rex", "Luna", "Bobby", "з™Ѕй›Є", "Thor", "Pipa", "Duke", "Zara"]
    species_map = ["CГЈo", "CГЈo", "CГЈo", "Gato", "Gato", "Gato", "CГЈo", "Ave", "CГЈo", "Gato"]
    breeds = {
        "CГЈo":  ["SRD", "Pastor AlemГЈo", "Labrador", "Bulldog", "Rottweiler", "Golden Retriever"],
        "Gato":  ["SRD", "Persa", "SiamГЄs", "British Shorthair"],
        "Ave":   ["Papagaio", "CanГЎrio", "Periquito"],
    }
    ages = [3, 7, 2, 5, 1, 4, 8, 2, 6, 3]
    weights = [12.5, 4.2, 28.0, 3.8, 5.1, 3.2, 22.0, 0.3, 30.0, 4.5]
    now_seed = datetime.now(timezone.utc)

    pets = []
    for i, owner in enumerate(owners):
        # 2 pets per owner
        for j in range(2):
            idx = i * 2 + j
            if idx >= len(pet_names):
                break
            name = pet_names[idx]
            species = species_map[idx]
            breed = random.choice(breeds[species])
            birth_year = now_seed.year - ages[idx]
            birth_date = datetime(birth_year, random.randint(1, 12), random.randint(1, 28)).date()
            existing = db.query(Pet).filter(
                Pet.clinic_id == clinic.id,
                Pet.owner_id == owner.id,
                Pet.name == name,
            ).first()
            if not existing:
                p = Pet(
                    clinic_id=clinic.id,
                    owner_id=owner.id,
                    name=name,
                    species=species,
                    breed=breed,
                    birth_date=birth_date,
                    weight=float(weights[idx]),
                    notes="",
                )
                db.add(p)
                db.commit()
                db.refresh(p)
            else:
                p = existing
            pets.append(p)

    print(f"  {len(pets)} pets seeded")

    # в”Ђв”Ђ 5. Appointments в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    statuses = list(AppointmentStatus)
    now = datetime.now(timezone.utc)

    appt_data = [
        (pets[0], "Consulta geral",      now + timedelta(days=1,  hours=9)),
        (pets[1], "VacinaГ§ГЈo",           now + timedelta(days=1,  hours=11)),
        (pets[2], "Exame de sangue",     now + timedelta(days=2,  hours=10)),
        (pets[3], "Cirurgia simples",     now + timedelta(days=3,  hours=8)),
        (pets[4], "Consulta urgГЄncia",    now + timedelta(hours=2)),
        (pets[5], "RevacinaГ§ГЈo",         now - timedelta(days=1,  hours=9)),
        (pets[6], "Banho e tosquia",     now - timedelta(days=2,  hours=14)),
        (pets[7], "Consulta geral",       now - timedelta(days=3,  hours=10)),
        (pets[8], "Raio-X",              now - timedelta(days=5,  hours=8)),
        (pets[9], "Tratamento pele",     now - timedelta(days=7,  hours=11)),
    ]

    for i, (pet, reason, scheduled) in enumerate(appt_data):
        status = statuses[i % len(statuses)]
        existing = db.query(Appointment).filter(
            Appointment.clinic_id == clinic.id,
            Appointment.pet_id == pet.id,
            Appointment.reason == reason,
        ).first()
        if not existing:
            a = Appointment(
                clinic_id=clinic.id,
                pet_id=pet.id,
                vet_id=vet.id,
                owner_id=pet.owner_id,
                scheduled_at=scheduled,
                reason=reason,
                notes="",
                status=status,
                weight=pet.weight if random.random() > 0.2 else None,
            )
            db.add(a)
    db.commit()
    appts = db.query(Appointment).filter(Appointment.clinic_id == clinic.id).all()
    print(f"  {len(appts)} appointments seeded")

    # в”Ђв”Ђ 6. Treatments (for completed appointments) в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    treatment_map = {
        "Consulta geral":       "Exame fГ­sico geral вЂ” sem anomalias",
        "VacinaГ§ГЈo":            "Vacina V8 administrada",
        "Exame de sangue":     "Hemograma completo вЂ” normal",
        "Cirurgia simples":     "Cirurgia realizada com sucesso",
        "Consulta urgГЄncia":    "Atendimento de urgГЄncia вЂ” medicado",
        "RevacinaГ§ГЈo":          "Vacina reforГ§ada",
        "Banho e tosquia":     "Banho medicado + tosquia",
        "Raio-X":               "Raio-X torГЎcico вЂ” normal",
        "Tratamento pele":     "Tratamento dermatolГіgico prescrito",
    }

    completed = [a for a in appts if a.status == AppointmentStatus.COMPLETED]
    for appt in completed[:5]:
        reason = appt.reason
        if reason in treatment_map:
            existing = db.query(Treatment).filter(
                Treatment.clinic_id == clinic.id,
                Treatment.appointment_id == appt.id,
            ).first()
            if not existing:
                t = Treatment(
                    clinic_id=clinic.id,
                    appointment_id=appt.id,
                    diagnosis=treatment_map[reason],
                    prescription="MedicaГ§ГЈo conforme protocolo padrГЈo",
                )
                db.add(t)

    # в”Ђв”Ђ 7. Invoices в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
    invoice_data = [
        (pets[5], 2500.0,  InvStatus.PAID,       "Consulta + VacinaГ§ГЈo"),
        (pets[6], 4500.0,  InvStatus.PAID,       "Banho + Tosquia"),
        (pets[7], 3500.0,  InvStatus.DRAFT,       "Consulta geral"),
        (pets[8], 8000.0,  InvStatus.DRAFT,       "Raio-X"),
        (pets[9], 5200.0,  InvStatus.CANCELLED,  "Tratamento dermatolГіgico"),
    ]

    for pet, amount, status, desc in invoice_data:
        existing = db.query(Invoice).filter(
            Invoice.clinic_id == clinic.id,
            Invoice.owner_id == pet.owner_id,
        ).first()
        if not existing:
            inv = Invoice(
                clinic_id=clinic.id,
                owner_id=pet.owner_id,
                amount=float(amount),
                status=status,
                description=desc,
            )
            db.add(inv)

    db.commit()
    invoices = db.query(Invoice).filter(Invoice.clinic_id == clinic.id).all()
    print(f"  {len(invoices)} invoices seeded")
    print("\nвњ… Seed complete!")
    print(f"   Login: ana@patas.ao / patas2026 (vet)")


def main():
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
