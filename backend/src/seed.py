"""Seed script — run once to populate the database with realistic test data."""

import random
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from src.core.database import SessionLocal
from src.core.security import hash_password
from src.models.appointment import Appointment, AppointmentStatus
from src.models.clinic import Clinic
from src.models.invoice import Invoice
from src.models.invoice import InvoiceStatus as InvStatus
from src.models.medication import Medication, MedicationStatus
from src.models.owner import Owner
from src.models.pet import Pet
from src.models.treatment import Treatment
from src.models.user import User, UserRole
from src.models.vaccination import Vaccination, VaccinationStatus
from src.services.clinical_catalog import ensure_clinic_defaults


def seed(db: Session) -> None:
    # ── 1. Clinic ──────────────────────────────────────────────
    clinic = db.query(Clinic).first()
    if not clinic:
        clinic = Clinic(name="Clínica Veterinária Luanda Sul")
        db.add(clinic)
        db.commit()
        db.refresh(clinic)

    print(f"Clinic: {clinic.name} (id={clinic.id})")
    ensure_clinic_defaults(db, clinic.id)

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
    pet_names = ["Bubi", "Nala", "Rex", "Luna", "Bobby", "з™Ѕй›Є", "Thor", "Pipa", "Duke", "Zara"]
    species_map = ["Cão", "Cão", "Cão", "Gato", "Gato", "Gato", "Cão", "Ave", "Cão", "Gato"]
    breeds = {
        "Cão":  ["SRD", "Pastor Alemão", "Labrador", "Bulldog", "Rottweiler", "Golden Retriever"],
        "Gato":  ["SRD", "Persa", "Siamês", "British Shorthair"],
        "Ave":   ["Papagaio", "Canário", "Periquito"],
    }
    ages = [3, 7, 2, 5, 1, 4, 8, 2, 6, 3]
    weights = [12.5, 4.2, 28.0, 3.8, 5.1, 3.2, 22.0, 0.3, 30.0, 4.5]
    now_seed = datetime.now(UTC)

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
            birth_date = date(birth_year, random.randint(1, 12), random.randint(1, 28))
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

    # ── 5. Appointments ────────────────────────────────────────
    statuses = list(AppointmentStatus)
    now = datetime.now(UTC)

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
                weight=pet.weight if random.random() > 0.2 else None,
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

    # ── 7. Structured clinical history ─────────────────────────
    # Keep this block repeatable so it can enrich an already populated local DB.
    all_pets = db.query(Pet).filter(Pet.clinic_id == clinic.id).order_by(Pet.id).all()
    vaccine_profiles = {
        "cão": ["Vacina V10", "Antirrábica", "Tosse dos Canis"],
        "cao": ["Vacina V10", "Antirrábica", "Tosse dos Canis"],
        "gato": ["Vacina V3", "Antirrábica", "Leucemia felina (FeLV)"],
        "ave": ["Poliomavírus", "Bouba aviária"],
    }
    medication_profiles = {
        "cão": ("Suplemento articular", "1 comprimido", "1x/dia", "oral"),
        "cao": ("Suplemento articular", "1 comprimido", "1x/dia", "oral"),
        "gato": ("Pasta de malte", "2 cm", "1x/dia", "oral"),
        "ave": ("Suplemento vitamínico", "3 gotas", "1x/dia", "oral"),
    }

    for pet in all_pets:
        species_key = (pet.species or "").strip().lower()
        vaccine_names = vaccine_profiles.get(species_key, ["Vacina polivalente", "Antirrábica"])
        existing_vaccines = {
            record.name
            for record in db.query(Vaccination).filter(
                Vaccination.clinic_id == clinic.id,
                Vaccination.pet_id == pet.id,
            ).all()
        }
        for vaccine_index, vaccine_name in enumerate(vaccine_names):
            if vaccine_name in existing_vaccines:
                continue
            administered_at = now - timedelta(days=730 - vaccine_index * 335 + pet.id)
            db.add(Vaccination(
                clinic_id=clinic.id,
                pet_id=pet.id,
                vet_id=vet.id,
                name=vaccine_name,
                administered_at=administered_at,
                dose="0,5 ml" if species_key == "ave" else "1 ml",
                lot_number=f"PATAS-{pet.id:02d}-{vaccine_index + 1:02d}",
                expires_at=(administered_at + timedelta(days=365)).date(),
                next_due_at=(administered_at + timedelta(days=365)).date(),
                notes="Registo demonstrativo de vacinação no histórico do animal.",
                status=VaccinationStatus.ADMINISTERED,
            ))
            existing_vaccines.add(vaccine_name)

        medication_profile = medication_profiles.get(
            species_key,
            ("Suplemento multivitamínico", "1 dose", "1x/dia", "oral"),
        )
        medication_name = medication_profile[0]
        existing_medication = db.query(Medication).filter(
            Medication.clinic_id == clinic.id,
            Medication.pet_id == pet.id,
            Medication.name == medication_name,
        ).first()
        if not existing_medication:
            start_date = (now - timedelta(days=90 + pet.id)).date()
            end_date = (now + timedelta(days=14)).date() if pet.id % 4 == 0 else (now - timedelta(days=45)).date()
            db.add(Medication(
                clinic_id=clinic.id,
                pet_id=pet.id,
                vet_id=vet.id,
                name=medication_name,
                dosage=medication_profile[1],
                frequency=medication_profile[2],
                route=medication_profile[3],
                start_date=start_date,
                end_date=end_date,
                instructions="Administrar conforme indicação clínica.",
                notes="Registo demonstrativo de medicação no histórico do animal.",
                status=MedicationStatus.ACTIVE if pet.id % 4 == 0 else MedicationStatus.COMPLETED,
            ))

    completed_appointments = db.query(Appointment).filter(
        Appointment.clinic_id == clinic.id,
        Appointment.status == AppointmentStatus.COMPLETED,
    ).all()
    for completed_appointment in completed_appointments:
        existing_treatment = db.query(Treatment).filter(
            Treatment.clinic_id == clinic.id,
            Treatment.appointment_id == completed_appointment.id,
        ).first()
        if not existing_treatment:
            db.add(Treatment(
                clinic_id=clinic.id,
                appointment_id=completed_appointment.id,
                diagnosis="Avaliação clínica concluída sem intercorrências.",
                prescription="Manter vacinação e desparasitação conforme calendário.",
                notes="Registo demonstrativo associado ao histórico clínico.",
            ))

    # ── 8. Invoices ────────────────────────────────────────────
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
    print("   Login: ana@patas.ao / patas2026 (vet)")


def main():
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
