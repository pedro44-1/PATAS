# PATAS API Usage Examples

## Base URL

- Dev: `http://localhost:8000/api/v1`
- Docker: `http://localhost:80/api/v1`

All endpoints require `Authorization: Bearer <access_token>` header except:
- `POST /auth/register`
- `POST /auth/login`
- `GET /health`

## Authentication

### Register (creates new clinic + admin user)

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Clínica Central",
    "email": "vet@clinic.ao",
    "password": "Password1"
  }'
```

Response:
```json
{
  "id": 1,
  "clinic_id": 1,
  "name": "Clínica Central",
  "email": "vet@clinic.ao",
  "role": "admin"
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
  "token_type": "bearer"
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

### Logout (blacklists current access token)

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access_token>"
```

---

## Dashboard

```bash
curl -X GET http://localhost:8000/api/v1/dashboard/ \
  -H "Authorization: Bearer <access_token>"
```

Response:
```json
{
  "today_appointments_total": 3,
  "today_appointments_by_status": {
    "scheduled": 2,
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

### Delete

```bash
curl -X DELETE http://localhost:8000/api/v1/owners/1 \
  -H "Authorization: Bearer <token>"
```

---

## Pets

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

### Delete

```bash
curl -X DELETE http://localhost:8000/api/v1/pets/1 \
  -H "Authorization: Bearer <token>"
```

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

Status values: `scheduled`, `completed`, `cancelled`, `no-show`

### Delete

```bash
curl -X DELETE http://localhost:8000/api/v1/appointments/1 \
  -H "Authorization: Bearer <token>"
```

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

### Delete (vet/admin only)

```bash
curl -X DELETE http://localhost:8000/api/v1/treatments/1 \
  -H "Authorization: Bearer <token>"
```

---

## Invoices

### List (filter by owner, status)

```bash
curl -X GET "http://localhost:8000/api/v1/invoices/?owner_id=1&status=draft" \
  -H "Authorization: Bearer <token>"
```

### Create (vet/admin only)

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

Status values: `draft`, `paid`, `cancelled`

**Note:** When setting `status: "cancelled"`, you must provide a `reason`.

```bash
curl -X PATCH http://localhost:8000/api/v1/invoices/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"status": "cancelled", "reason": "Cliente desistiu"}'
```

### Delete (admin only)

```bash
curl -X DELETE http://localhost:8000/api/v1/invoices/1 \
  -H "Authorization: Bearer <token>"
```

---

## Users (admin only)

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
    "redis": "error: Connection refused"
  }
}
```

---

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
- `/auth/login`: 5 requests/60 seconds per IP
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

All queries automatically scoped to `clinic_id` from JWT.
Accessing another clinic's resources returns 404 (not 403).