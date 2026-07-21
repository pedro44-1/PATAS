"""Seed script — run once to populate the database with realistic test data."""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import random

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.models.clinic import Clinic
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserRole
from app.models.invoice import Invoice, InvoiceStatus as InvStatus
from app.models.treatment import Treatment


def seed(db: Session) -> None:
    # ── 1. Clinic ──────────────────────────────────────────────
    clinic = db.query(Clinic).first()
    if not clinic:
        clinic = Clinic(name="Clínica Veterinária Luanda Sul")
        db.add(clinic)
        db.commit()
        db.refresh(clinic)

    print(f"Clinic: {clinic.name} (id={clinic.id})")

    # ── 2. Users ────────────────────────────────────────────────
    users_data = [
        ("Dr. Ana Sousa",    "ana@patas.ao",    "vet"),
        ("Dr. João Mendes",  "joao@patas.ao",   "vet"),
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
        print(f"  User: {u.name} ({u.email}) — {u.role.value}")

    vets = [u for u in users if u.role == UserRole.VET]
    vet = vets[0]

    # ── 3. Owners ───────────────────────────────────────────────
    owners_data = [
        ("Maria do Carmo",     "maria.carmo@gmail.com",     "+244 923 456 789", "Rua Major Kanhangulo, Luanda"),
        ("António João",      "antonio.joao@ymail.com",    "+244 934 567 890", "Rua Comandante Gika, Benfica"),
        ("Fernanda Pacavira",  "fernanda.p@gmail.com",      "+244 945 678 901", "Rua Timor, Talatona"),
        ("Carlos Eduardo",     "carlos.edu@outlook.com",    "+244 956 789 012", "Rua Comandante Valódia, Maianga"),
        ("Jesuína Francisco",  "jesuina.francisco@gmail.com","+244 921 234 567", "Rua Comandante Ncondo, Kilamba"),
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

    # ── 4. Pets ────────────────────────────────────────────────
    pet_names = ["Bubi", "Nala", "Rex", "Luna", "Bobby", "白雪", "Thor", "Pipa", "Duke", "Zara"]
    species_map = ["Cão", "Cão", "Cão", "Gato", "Gato", "Gato", "Cão", "Ave", "Cão", "Gato"]
    breeds = {
        "Cão":  ["SRD", "Pastor Alemão", "Labrador", "Bulldog", "Rottweiler", "Golden Retriever"],
        "Gato":  ["SRD", "Persa", "Siamês", "British Shorthair"],
        "Ave":   ["Papagaio", "Canário", "Periquito"],
    }
    ages = [3, 7, 2, 5, 1, 4, 8, 2, 6, 3]
    weights = [12.5, 4.2, 28.0, 3.8, 5.1, 3.2, 22.0, 0.3, 30.0, 4.5]

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
                    age=ages[idx],
                    weight=Decimal(str(weights[idx])),
                    notes="",
                )
                db.add(p)
                db.commit()
                db.refresh(p)
            else:
                p = existing
            pets.append(p)

    print(f"  {len(pets)} pets seeded")

    # ── 5. Appointments ────────────────────────────────────────
    statuses = list(AppointmentStatus)
    now = datetime.now(timezone.utc)

    appt_data = [
        (pets[0], "Consulta geral",      now + timedelta(days=1,  hours=9)),
        (pets[1], "Vacinação",           now + timedelta(days=1,  hours=11)),
        (pets[2], "Exame de sangue",     now + timedelta(days=2,  hours=10)),
        (pets[3], "Cirurgia simples",     now + timedelta(days=3,  hours=8)),
        (pets[4], "Consulta urgência",    now + timedelta(hours=2)),
        (pets[5], "Revacinação",         now - timedelta(days=1,  hours=9)),
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
            )
            db.add(a)
    db.commit()
    appts = db.query(Appointment).filter(Appointment.clinic_id == clinic.id).all()
    print(f"  {len(appts)} appointments seeded")

    # ── 6. Treatments (for completed appointments) ─────────────
    treatment_map = {
        "Consulta geral":       "Exame físico geral — sem anomalias",
        "Vacinação":            "Vacina V8 administrada",
        "Exame de sangue":     "Hemograma completo — normal",
        "Cirurgia simples":     "Cirurgia realizada com sucesso",
        "Consulta urgência":    "Atendimento de urgência — medicado",
        "Revacinação":          "Vacina reforçada",
        "Banho e tosquia":     "Banho medicado + tosquia",
        "Raio-X":               "Raio-X torácico — normal",
        "Tratamento pele":     "Tratamento dermatológico prescrito",
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
                    prescription="Medicação conforme protocolo padrão",
                )
                db.add(t)

    # ── 7. Invoices ────────────────────────────────────────────
    invoice_data = [
        (pets[5], 2500.0,  InvStatus.PAID,       "Consulta + Vacinação"),
        (pets[6], 4500.0,  InvStatus.PAID,       "Banho + Tosquia"),
        (pets[7], 3500.0,  InvStatus.DRAFT,       "Consulta geral"),
        (pets[8], 8000.0,  InvStatus.DRAFT,       "Raio-X"),
        (pets[9], 5200.0,  InvStatus.CANCELLED,  "Tratamento dermatológico"),
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
    print("\n✅ Seed complete!")
    print(f"   Login: ana@patas.ao / patas2026 (vet)")


def main():
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
