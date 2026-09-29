# PATAS API Usage Examples

## Base URL

- Dev: `http://localhost:8000/api/v1`
- Docker/LAN: `http://localhost/api/v1`

All endpoints require `Authorization: Bearer <access_token>` header except:
- `POST /auth/register`
- `POST /auth/login`
- `GET /integrations/whatsapp/webhook` (Meta verification token)
- `POST /integrations/whatsapp/webhook` (Meta HMAC signature)
- `GET /health`

## Authentication

### Register (creates new clinic + admin user)

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "clinic_name": "Clínica Central",
    "name": "Ana Manuel",
    "email": "vet@clinic.ao",
    "password": "Password1"
  }'
```

Response:
```json
{
  "id": 1,
  "clinic_id": 1,
  "clinic_name": "Clínica Central",
  "name": "Ana Manuel",
  "email": "vet@clinic.ao",
  "role": "admin",
  "must_change_password": false
}
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vet@clinic.ao",
    "password": "Password1"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "must_change_password": false
}
```

### Refresh token (rotation)

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIs..."}'
```

Returns new `access_token` and `refresh_token`. Old refresh token is blacklisted.

### Get current user

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### Logout (revoga ambos os tokens)

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

### Troca obrigatória de palavra-passe

Contas criadas pelo administrador devolvem `must_change_password: true`. Enquanto esse valor estiver ativo, apenas `/auth/me`, `/auth/change-password` e `/auth/logout` são permitidos; os restantes endpoints devolvem `403` com `PASSWORD_CHANGE_REQUIRED`.

```bash
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "Temporary1",
    "new_password": "Permanent2",
    "refresh_token": "<refresh_token>"
  }'
```

A resposta é um novo par de tokens; o par anterior é revogado.

---

## Dashboard

```bash
curl -X GET http://localhost:8000/api/v1/dashboard/ \
  -H "Authorization: Bearer <access_token>"
```

Dashboard status counts include `scheduled`, `in_progress`, `completed`, `cancelled` and `no_show`.

Response:
```json
{
  "today_appointments_total": 3,
  "today_appointments_by_status": {
    "scheduled": 2,
    "in_progress": 0,
    "completed": 1,
    "cancelled": 0,
    "no_show": 0
  },
  "upcoming_appointments": [...],
  "total_owners": 42,
  "total_pets": 67
}
```

---

## Owners

### List (paginated, searchable)

```bash
curl -X GET "http://localhost:8000/api/v1/owners/?skip=0&limit=10&q=João" \
  -H "Authorization: Bearer <token>"
```

Headers: `X-Total-Count: 42`

### Create

```bash
curl -X POST http://localhost:8000/api/v1/owners/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Mendes",
    "phone": "+244 923 456 789",
    "email": "joao@email.ao",
    "address": "Rua das Flores 123, Luanda",
    "notes": "Prefere consultas pela manhã"
  }'
```

### Get by ID

```bash
curl -X GET http://localhost:8000/api/v1/owners/1 \
  -H "Authorization: Bearer <token>"
```

### Update

```bash
curl -X PATCH http://localhost:8000/api/v1/owners/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+244 999 888 777"}'
```

### Arquivar

```bash
curl -X DELETE http://localhost:8000/api/v1/owners/1 \
  -H "Authorization: Bearer <token>"
```

O arquivo define `archived_at`/`archived_by_user_id` e arquiva os animais ativos do dono na mesma transação. Use `?include_archived=true` nas listas para os incluir; o acesso direto e o histórico permanecem disponíveis.

---

## Pets

### Clinical history

```bash
curl -X GET http://localhost:8000/api/v1/pets/1/history \
  -H "Authorization: Bearer <token>"
```

Returns the pet's appointments and their associated diagnosis, prescription, notes and recorded weight in reverse chronological order.

The response also includes `vaccinations` and `medications`. These collections remain scoped to the pet's clinic and retain voided records for audit/history display.

### Vaccinations

Requires `clinical:read` for listing and `clinical:write` for mutations.

```bash
curl -X GET "http://localhost:8000/api/v1/vaccinations/?pet_id=1" \
  -H "Authorization: Bearer <token>"

curl -X POST http://localhost:8000/api/v1/vaccinations/ \
  -H "Authorization: Bearer <vet_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "pet_id": 1,
    "vet_id": 2,
    "name": "V10",
    "administered_at": "2026-07-23T09:00:00Z",
    "dose": "1 ml",
    "lot_number": "LOT-001",
    "next_due_at": "2027-07-23"
  }'

curl -X PATCH http://localhost:8000/api/v1/vaccinations/1 \
  -H "Authorization: Bearer <vet_token>" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Sem reação"}'

curl -X POST http://localhost:8000/api/v1/vaccinations/1/void \
  -H "Authorization: Bearer <vet_token>" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Registo duplicado"}'
```

### Medications

Requires `clinical:read` for listing and `clinical:write` for mutations. A medication uses structured dosage, frequency, route and dates; it can be completed/cancelled through `PATCH` or voided with a mandatory reason.

```bash
curl -X GET "http://localhost:8000/api/v1/medications/?pet_id=1" \
  -H "Authorization: Bearer <token>"

curl -X POST http://localhost:8000/api/v1/medications/ \
  -H "Authorization: Bearer <vet_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "pet_id": 1,
    "vet_id": 2,
    "name": "Amoxicilina",
    "dosage": "250 mg",
    "frequency": "12/12h",
    "route": "oral",
    "start_date": "2026-07-23",
    "instructions": "Após a refeição"
  }'

curl -X PATCH http://localhost:8000/api/v1/medications/1 \
  -H "Authorization: Bearer <vet_token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'

curl -X POST http://localhost:8000/api/v1/medications/1/void \
  -H "Authorization: Bearer <vet_token>" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Prescrição substituída"}'
```

### List (paginated, searchable)

```bash
curl -X GET "http://localhost:8000/api/v1/pets/?skip=0&limit=10&q=Rex&owner_id=1" \
  -H "Authorization: Bearer <token>"
```

### Create

```bash
curl -X POST http://localhost:8000/api/v1/pets/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": 1,
    "name": "Rex",
    "species": "cão",
    "breed": "Pastor Alemão",
    "age": "3 anos",
    "weight": 32.5,
    "notes": "Vacinado"
  }'
```

### Get by ID

```bash
curl -X GET http://localhost:8000/api/v1/pets/1 \
  -H "Authorization: Bearer <token>"
```

### Update

```bash
curl -X PATCH http://localhost:8000/api/v1/pets/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"weight": 33.0}'
```

### Arquivar

```bash
curl -X DELETE http://localhost:8000/api/v1/pets/1 \
  -H "Authorization: Bearer <token>"
```

Animais arquivados não podem originar novas consultas ou faturas. Use `?include_archived=true` para os incluir na lista.

---

## Appointments

### List (filter by date)

```bash
curl -X GET "http://localhost:8000/api/v1/appointments/?date=2026-07-21" \
  -H "Authorization: Bearer <token>"
```

### Create

```bash
curl -X POST http://localhost:8000/api/v1/appointments/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "pet_id": 1,
    "vet_id": 1,
    "scheduled_at": "2026-07-21T10:30:00Z",
    "duration_min": 30,
    "reason": "Vacinação anual",
    "notes": "Chegar 10 min antes"
  }'
```

Note: `owner_id` is auto-derived from pet.

### Get by ID

```bash
curl -X GET http://localhost:8000/api/v1/appointments/1 \
  -H "Authorization: Bearer <token>"
```

### Update (status, time, etc.)

```bash
curl -X PATCH http://localhost:8000/api/v1/appointments/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

Status values: `scheduled`, `in-progress`, `completed`, `cancelled`, `no-show`.

Transições: `scheduled → in-progress|cancelled|no-show` e `in-progress → completed`. Envie `status_reason` para `cancelled` e `no-show`. Apenas veterinários e administradores iniciam/concluem; a receção pode cancelar ou marcar falta. Campos de agenda só mudam em `scheduled`.

### Remover uma consulta agendada

```bash
curl -X DELETE http://localhost:8000/api/v1/appointments/1 \
  -H "Authorization: Bearer <token>"
```

Este endpoint cancela a consulta com motivo auditável. Consultas iniciadas ou terminais devolvem `409`.

---

## Treatments

### List (filter by appointment)

```bash
curl -X GET "http://localhost:8000/api/v1/treatments/?appointment_id=1" \
  -H "Authorization: Bearer <token>"
```

### Create (vet/admin only)

```bash
curl -X POST http://localhost:8000/api/v1/treatments/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "appointment_id": 1,
    "diagnosis": "Animal saudável",
    "prescription": "Vacina V10 aplicada. Reforço em 12 meses.",
    "notes": "Sem reações adversas"
  }'
```

### Get by ID

```bash
curl -X GET http://localhost:8000/api/v1/treatments/1 \
  -H "Authorization: Bearer <token>"
```

### Update

```bash
curl -X PATCH http://localhost:8000/api/v1/treatments/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Dose de reforço agendada"}'
```

### Eliminação

```bash
curl -X DELETE http://localhost:8000/api/v1/treatments/1 \
  -H "Authorization: Bearer <token>"
```

Devolve `405`: tratamentos clínicos nunca são eliminados fisicamente.

---

## Invoices

### List (filter by owner, status)

```bash
curl -X GET "http://localhost:8000/api/v1/invoices/?owner_id=1&status=draft" \
  -H "Authorization: Bearer <token>"
```

### Create (receção, vet ou admin)

```bash
curl -X POST http://localhost:8000/api/v1/invoices/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": 1,
    "appointment_id": 1,
    "amount": 8500.0,
    "description": "Vacinação V10 + consulta",
    "reason": null
  }'
```

### Get by ID

```bash
curl -X GET http://localhost:8000/api/v1/invoices/1 \
  -H "Authorization: Bearer <token>"
```

### Update

```bash
curl -X PATCH http://localhost:8000/api/v1/invoices/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "paid"}'
```

Status values: `draft`, `sent`, `paid`, `cancelled`.

**Note:** When setting `status: "cancelled"`, you must provide a `reason`.

Invoice statuses are `draft`, `sent`, `paid` and `cancelled`. The mock payment adapter can be called with:

```bash
curl -X POST http://localhost:8000/api/v1/invoices/1/sync \
  -H "Authorization: Bearer <token>"
```

The response contains `external_reference` and `sync_status`. No real payment is processed by PATAS.

```bash
curl -X PATCH http://localhost:8000/api/v1/invoices/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "cancelled", "reason": "Cliente desistiu"}'
```

### Eliminação

```bash
curl -X DELETE http://localhost:8000/api/v1/invoices/1 \
  -H "Authorization: Bearer <token>"
```

Devolve `405`: use `PATCH` para cancelar com motivo. `paid` e `cancelled` são terminais.

---

## Users (admin only)

### Criar utilizador com palavra-passe temporária

```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Maria José",
    "email": "maria@clinic.ao",
    "role": "receptionist",
    "password": "Temporary1"
  }'
```

A resposta não inclui a palavra-passe e devolve `must_change_password: true`.

### List users in clinic

```bash
curl -X GET http://localhost:8000/api/v1/users/ \
  -H "Authorization: Bearer <admin_token>"
```

### Update user role

```bash
curl -X PATCH http://localhost:8000/api/v1/users/2/role \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "vet"}'
```

Roles: `admin`, `vet`, `receptionist`

---

## Health Check

```bash
curl -X GET http://localhost:8000/health
```

Response (healthy):
```json
{
  "status": "ok",
  "app": "PATAS",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

Response (degraded):
```json
{
  "status": "degraded",
  "app": "PATAS",
  "checks": {
    "database": "ok",
    "redis": "error"
  }
}
```

Uma resposta degradada usa HTTP `503`; saudável usa `200`.

---

## WhatsApp integration

The optional WhatsApp Cloud API callback is exposed at
`/api/v1/integrations/whatsapp/webhook` when the integration is configured.

Meta verifies the callback with `GET` query parameters `hub.mode`, `hub.verify_token`, and
`hub.challenge`. Event delivery uses `POST` and must include a valid `X-Hub-Signature-256`
computed with the configured Meta app secret. Accepted event payloads return:

```json
{
  "status": "accepted",
  "messages": 1,
  "statuses": 0
}
```

This endpoint does not yet persist message content or initiate domain actions. Outbound text and
approved-template messages are implemented behind the internal service boundary and should only
be connected to a clinic workflow after consent, tenant ownership, and template policy are defined.

---

## Service types

List types configured for the current clinic:

```bash
curl -X GET http://localhost:8000/api/v1/service-types/ \
  -H "Authorization: Bearer <token>"
```

Administrators can create or update types with `POST /service-types/` and `PATCH /service-types/{id}`. Updating `active` archives a type without removing historical references.

## Waiting room

List checked-in entries for a day:

```bash
curl -X GET "http://localhost:8000/api/v1/waiting-room/?date=2026-09-09&q=Nala" \
  -H "Authorization: Bearer <token>"
```

Add an already scheduled appointment:

```bash
curl -X POST http://localhost:8000/api/v1/waiting-room/entries \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"appointment_id": 12, "room": "Consultório 1"}'
```

A walk-in uses `pet_id`, `vet_id`, and optionally `service_type_id`; the API creates its appointment and queue entry atomically. Queue transitions use `POST /waiting-room/entries/{id}/transition`: `waiting → called|cancelled|no-show`, `called → in-progress|cancelled|no-show`, and `in-progress → completed`. Cancellation and no-show require `reason`; appointment and queue are updated together.

## Structured clinical encounter

The clinical workspace reads and writes the complete encounter as one resource:

```bash
curl -X GET http://localhost:8000/api/v1/appointments/12/clinical-record \
  -H "Authorization: Bearer <token>"
```

Veterinarians and administrators save history, diagnosis, free prescription, exam findings and structured medicines with `PUT /appointments/{id}/clinical-record`. Receptionists may read this resource but receive `403` on writes.

## Physical exam catalogue

`GET /exam-catalog/` returns the systems and findings for the current clinic. Administrators create or archive systems with `/exam-catalog/systems` and findings with `/exam-catalog/systems/{system_id}/findings` or `/exam-catalog/findings/{id}`. Archived catalogue values remain valid in saved encounter history.

## Pagination & Filters

All list endpoints support:
- `skip` (default 0)
- `limit` (default 100, max 1000)
- Returns `X-Total-Count` header

Additional filters:
- **Owners**: `?q=search_term`
- **Pets**: `?q=search_term&owner_id=1`
- **Appointments**: `?date=2026-07-21`
- **Treatments**: `?appointment_id=1`
- **Invoices**: `?owner_id=1&status=draft`

---

## Rate Limits

- Global: 100 requests/minute per IP (`X-RateLimit-*` headers)
- The health check and signed WhatsApp webhook callback bypass the generic IP limit.
- `/auth/login`: 5 requests/60 seconds per combinação IP/email
- Exceeding returns `429 Too Many Requests` with `Retry-After` header

---

## Error Responses

```json
// 400 Bad Request
{"detail": "Email já registado"}

// 401 Unauthorized
{"detail": "Token inválido ou expirado"}

// 403 Forbidden
{"detail": "Permissão negada"}

// 409 Conflict
{"detail": "O veterinário já tem uma consulta nesse horário"}

// 404 Not Found
{"detail": "Dono não encontrado"}

// 422 Validation Error
{"detail": [{"loc": ["body", "email"], "msg": "value is not a valid email address", "type": "value_error"}]}

// 429 Too Many Requests
{"detail": "Muitas tentativas de login. Tente novamente em 60 segundos."}

// 500 Internal Server Error
{"detail": "Erro interno do servidor"}
```

---

## Token Payload

```json
{
  "sub": "1",
  "clinic_id": "1",
  "role": "vet",
  "type": "access",
  "jti": "uuid",
  "exp": 1721563200
}
```

Refresh tokens have `type: "refresh"` and 7-day expiry.

---

## Cross-Tenant Isolation

All queries are scoped to the current database user `clinic_id`; refresh reloads user, clinic and role instead of trusting stale claims.
Accessing another clinic's resources returns 404 (not 403).

Agenda, dashboard and waiting-room date boundaries use `Africa/Luanda`; stored instants remain UTC.
