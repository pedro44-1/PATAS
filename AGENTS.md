# PATAS — Vet Clinic Management SaaS

> Codename. Angola market. Luanda/Benguela focus.

---

## Product

PATAS is a multi-tenant veterinary clinic management SaaS for the Angolan market.
Replaces paper, Excel, and WhatsApp chaos with one clean web dashboard per clinic.

**Phase 1:** Clinic-side only (owner app, SMS, AGT invoicing — Phase 2+)
**Phase 2:** Owner mobile app, SMS reminders, Multicaixa payments
**Phase 3:** AGT-compliant invoicing API, multi-vet, analytics

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic |
| Database | PostgreSQL (prod) / SQLite (tests) |
| Frontend | React 18, TypeScript, Vite, Tailwind, shadcn/ui |
| Auth | JWT (access + refresh tokens), role-based (vet, receptionist) |
| Deployment | Docker, Docker Compose, nginx, SSL |

---

## Architecture

```
frontend/          React web dashboard (clinic staff)
backend/          FastAPI REST API
  app/
    core/         Config, security, database
    models/       SQLAlchemy models
    schemas/      Pydantic schemas
    api/v1/       Routers
    services/     Business logic
```

---

## Multi-Tenant Design

Each clinic is an isolated tenant.

- Tenant identified by `clinic_id` on every authenticated request
- JWT token carries `clinic_id` + `user_id` + `role`
- All database queries scoped by `clinic_id`
- Database: single Postgres instance, schema-per-tenant OR shared schema with `clinic_id` FKs
  - **Decision: shared schema with `clinic_id` FKs** (simpler for MVP, migrate to schema-per-tenant at 20+ tenants)

---

## MVP Features — Phase 1 (v1.0)

### Clinic Dashboard

| Feature | Description |
|---|---|
| Auth | JWT login, vet + receptionist roles |
| Dashboard home | Today's appointments at a glance |
| Owners | Create, view, edit pet owners |
| Pets | Register pets (species, breed, age, notes) |
| Appointments | Calendar view, create, edit, mark complete |
| Treatments | Log consultation notes, diagnosis, prescriptions |
| Invoices | Basic invoice (non-AGT for now) |

### Out of Scope (Phase 2+)

- Owner mobile app
- SMS reminders
- Push notifications
- AGT-compliant invoicing
- Multicaixa payment integration
- Analytics / reporting
- Multi-vet scheduling

---

## Data Model

### Core Entities

```
Clinic
  id, name, address, phone, email, created_at

User
  id, clinic_id FK, name, email, password_hash, role (vet|receptionist), created_at

Owner
  id, clinic_id FK, name, phone, email, address, notes, created_at

Pet
  id, clinic_id FK, owner_id FK, name, species, breed, age, weight, notes, created_at

Appointment
  id, clinic_id FK, pet_id FK, vet_id FK, scheduled_at, duration_min, status (scheduled|completed|cancelled), notes

Treatment
  id, clinic_id FK, appointment_id FK, diagnosis, notes, prescription, created_at

Invoice
  id, clinic_id FK, owner_id FK, appointment_id FK, amount, status (draft|paid|cancelled), created_at
```

---

## Conventions

- **No comments in code** unless logic is non-obvious
- **Edit existing files** — do not create new files unless told
- **Follow existing patterns** — imports, naming, style
- **Run full test suite** before marking any task done: `python -m pytest`
- **API-first** — all features accessible via REST API before UI

---

## Testing

- All tests in `backend/tests/`
- SQLite for tests, PostgreSQL for production
- `conftest.py` has fixture setup — update when adding models

---

## Security

- `SECRET_KEY` and `ENCRYPTION_KEY` env vars required
- Passwords hashed with bcrypt
- Role-based access: receptionist can CRUD owners/pets/appointments; vet can also write treatments
- Never log tokens, passwords, or decrypted data
- Never commit `.env` or `*.db`

---

## Deployment

**Prerequisites:** Domain registered, VPS (Yandex Cloud or equivalent), Docker + Docker Compose

See `docs/deployment.md` for full deployment checklist.

---

## Version

Current: 0.1.0-draft
