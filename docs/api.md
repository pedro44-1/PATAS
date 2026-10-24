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

`nif` accepts 10 digits (company) or 9 digits + 2 letters + 3 digits (individual) and is stored without separators in uppercase; `phone` accepts 9 digits or an international `+` number. Blank optional fields are stored as `null`.


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

### List (filter by date or interval)

```bash
curl -X GET "http://localhost:8000/api/v1/appointments/?date=2026-07-21" \
  -H "Authorization: Bearer <token>"

curl -X GET "http://localhost:8000/api/v1/appointments/?date_from=2026-07-21&date_to=2026-07-27" \
  -H "Authorization: Bearer <token>"
```

`date` preserves the single-day filter. For an inclusive interval, send both `date_from` and `date_to`; incomplete, reversed, or mixed single-date/range filters return `422`. Optional filters: `pet_id`, `owner_id`, `status`, `q` (pet, owner or reason) and `order=asc|desc` (by `scheduled_at`). Responses include `pet_name`, `owner_name`, `vet_name` and `subject_archived`, plus the `X-Total-Count` header.

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

Requires `treatment:read` (receptionists receive `403`). Clinical writes (`PATCH /treatments/{id}` and `PUT /appointments/{id}/clinical-record`) are rejected for cancelled/no-show appointments (`409`); changing an existing record of a completed appointment requires `correction_reason` from a vet/admin (`422`/`403` otherwise), is audited with that reason and marks removed exam findings as `not-evaluated` instead of deleting them. Appointments whose pet or owner is archived cannot be checked in, called, started, documented or invoiced (`409`); they can still be cancelled. An appointment has at most one treatment; a second create returns `409`.

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

### List (filter by owner, pet, appointment, status, search)

```bash
curl -X GET "http://localhost:8000/api/v1/invoices/?owner_id=1&status=draft&q=FT" \
  -H "Authorization: Bearer <token>"
```

`pet_id` matches invoices whose appointment belongs to the pet; `q` searches the document number, customer name and owner name. An appointment accepts one non-cancelled invoice (`409` otherwise), and cancelled or no-show appointments cannot be invoiced.

### Create (receção, vet ou admin)

```bash
curl -X POST http://localhost:8000/api/v1/invoices/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": 1,
    "appointment_id": 1,
    "payment_method": "tpa",
    "items": [
      {"description": "Consulta", "quantity": 1, "unit_price": 6000, "tax_rate": 0},
      {"description": "Vacinação V10", "quantity": 1, "unit_price": 2500, "tax_rate": 0}
    ]
  }'
```

O dono precisa de NIF. O servidor calcula um subtotal comercial provisório; `tax_rate` deve ser zero porque IVA, retenções e total fiscal são calculados pelo Vendas. `amount` e `description` continuam aceites como formato legado e são convertidos numa linha única.

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
  -d '{"status": "cancelled", "reason": "Documento criado por engano"}'
```

Status values: `draft`, `sent`, `paid`, `cancelled`.

**Note:** `cancelled` exige `reason` e só é permitido antes da emissão externa. `sent` e `paid` não podem ser definidos manualmente no PATAS; só a emissão no Vendas os aplica. Alterar `amount`/`description` de um rascunho limpa a prévia fiscal; com uma emissão pendente (`sync_attempts > 0` e `idempotency_key`), o conteúdo fica bloqueado (`409`).

O PATAS prepara linhas e preços líquidos. Antes da emissão, obtenha a prévia fiscal:

```bash
curl -X POST http://localhost:8000/api/v1/invoices/1/preview \
  -H "Authorization: Bearer <token>"
```

A resposta preserva `quote_id`, `quote_expires_at`, `quote_vat_configuration_version`, `quote_calculation_digest` e `quote_payable`. A cotação dura dez minutos. Depois de confirmar o valor, emita com:

```bash
curl -X POST http://localhost:8000/api/v1/invoices/1/sync \
  -H "Authorization: Bearer <token>"
```

A resposta contém `external_reference`, `sync_status`, `provider_status`, `provider_mode`, `series`, `document_number` e `document_url` quando o provedor os devolver. O provedor `mock` é usado por omissão; `BILLING_PROVIDER=vendas` ativa o cliente server-to-server. O PATAS não cria a fatura fiscal.

O cliente Vendas chama primeiro `POST /api/integrations/v1/invoices/preview` e depois `POST /api/integrations/v1/invoices`. Cada pedido usa uma `Idempotency-Key` UUID persistida e distinta. FT omite pagamento; FR envia um tender exatamente igual ao `quote_payable`. A chave Vendas precisa dos escopos `invoice.issue`, `invoice.read`, `customer.upsert` e `product.upsert`; numerário acrescenta `cash.operate` e uma sessão aberta.

O payload externo serializa quantidades, preços, descontos e pagamentos como strings decimais exatas. Cada linha recebe código de até 64 caracteres, unidade de até 12 e `vatProfileCode` de até 80; o perfil pode ser indicado por linha ou herdado da configuração predefinida. Na ausência de código, o PATAS gera um identificador determinístico por clínica, tipo e descrição, evitando criar um artigo novo por fatura. Campos opcionais sem valor são omitidos. FR suporta `CASH`, `CARD` e `TRANSFER`; `other` é rejeitado. A referência legível devolvida pelo Vendas é apresentada como número do documento; `seriesId` permanece metadado interno.

`VAT_PROFILE_REQUIRED` pede configuração comercial no Vendas. `QUOTE_NOT_FOUND`, `QUOTE_EXPIRED`, `QUOTE_MISMATCH` e `QUOTE_STALE` invalidam a cotação local e exigem nova prévia. Um timeout, erro de transporte, `5xx`, `408`, `409`, `425` ou `429` na emissão mantém a chave e reutiliza exatamente o mesmo corpo na repetição, para evitar duplicação. Outras rejeições `4xx` são definitivas: limpam a prévia e a chave, guardam `last_sync_error` e permitem uma nova prévia.

Uma FT emitida fica `sent` até o Vendas a reportar como paga. `POST /api/v1/invoices/{id}/reconcile` (permissão `invoice:read`) consulta o estado no Vendas e passa a fatura a `paid` quando o estado está em `VENDAS_PAID_STATES` (por omissão `PAID,SETTLED`); devolve `409` se o documento ainda não foi emitido. `GET /{id}/sync-status` mantém-se por compatibilidade e usa a mesma reconciliação. O serviço `billing-reconciler` (`python -m scripts.reconcile_invoices --loop`) repete a reconciliação das FT pendentes a cada `BILLING_RECONCILE_INTERVAL_SECONDS` quando `BILLING_RECONCILE_ENABLED=true`, com um lock Redis para não correr em paralelo. A prévia volta a ler os dados atuais da clínica e do dono, e a data do documento é o dia corrente em Luanda.

Variáveis do backend: `BILLING_PROVIDER`, `VENDAS_BASE_URL`, `VENDAS_API_KEY`, `VENDAS_OPERATION_TYPE`, `VENDAS_DEFAULT_VAT_PROFILE_CODE`, `VENDAS_CASH_SESSION_ID` e `VENDAS_REQUEST_TIMEOUT_SECONDS`. O modo atual do Vendas é `TRAINING` e não produz documentos com validade fiscal.

### Dados da clínica para faturação

```bash
curl -X PATCH http://localhost:8000/api/v1/clinics/me \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"nif": "5000000000", "billing_store_external_id": "clinica-luanda"}'
```

`GET /api/v1/clinics/me` está disponível para utilizadores autenticados; apenas administradores alteram os dados.

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

Devolve `405`: use `PATCH` para cancelar um rascunho com motivo. Um documento já aceite pelo Vendas exige anulação ou nota de crédito no provedor. `paid` e `cancelled` são terminais.

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

### Ativar/desativar utilizador

```bash
curl -X PATCH http://localhost:8000/api/v1/users/2/status \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

Desativar revoga imediatamente todas as sessões do utilizador e bloqueia o login (`403`). Um administrador não se pode desativar (`400`). As respostas de utilizador incluem `is_active`.

### Sessões

Os tokens transportam a versão de sessão do utilizador (`tv`). Mudar a palavra-passe ou desativar a conta incrementa essa versão e invalida todos os tokens anteriores (`401 Sessão revogada`). Cada refresh token só pode ser usado uma vez, de forma atómica.

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
- `skip` (default 0, `>= 0`)
- `limit` (default 100, `1..200`; outside the range returns `422`)
- Returns `X-Total-Count` header

Additional filters:
- **Owners**: `?q=` (name, phone, email, NIF)
- **Pets**: `?q=` (name, species, breed, owner name) `&owner_id=1`
- **Appointments**: `?date=2026-07-21` or `date_from`/`date_to`, `pet_id`, `owner_id`, `status`, `q`, `order`
- **Treatments**: `?appointment_id=1`
- **Invoices**: `?owner_id=1&pet_id=2&appointment_id=3&status=draft&q=`

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
