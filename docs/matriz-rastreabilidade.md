# Matriz de rastreabilidade do MVP

## Gate de release

O MVP só está pronto quando todos os comandos abaixo passam numa revisão limpa:

```text
Backend SQLite:      PYTHONPATH=. pytest tests/ -q
Backend lint:        ruff check src/
PostgreSQL/Redis:    scripts/run_integration_tests.ps1 (ou .sh)
Tipos partilhados:   npm run build --workspace=@patas/shared-types
Frontend:            npm run test --workspace=frontend && npm run build
Compose LAN:         docker compose -f infra/docker-compose.yml --env-file infra/.env.example config --quiet
```

A pipeline `.github/workflows/ci.yml` executa estes gates e um smoke test HTTP do Compose. Não pode existir defeito P0/P1 conhecido no percurso principal.

## RF01–RF11

| Requisito | Evidência automatizada principal |
|---|---|
| RF-01 Autenticação e tenant | `test_auth.py`, `test_integration.py::test_08_cross_tenant_isolation`, `client.test.ts`, `errors.test.ts`, `AuthContext.test.tsx`, `ProtectedRoute.test.tsx` |
| RF-02 Donos | `test_owners.py`, incluindo arquivo em cascata e bloqueio de nova faturação |
| RF-03 Animais | `test_pets.py`, `test_history.py`, `test_appointments.py::test_archived_pet_cannot_be_scheduled` |
| RF-04 Agendamento | `test_appointments.py`; `test_integration.py::test_11_concurrent_appointments_return_conflict`; `test_postgres_migrations.py` |
| RF-05 Ciclo de atendimento | matriz em `test_appointments.py` e sincronização em `test_waiting_room.py` |
| RF-06 Histórico clínico | `test_treatments.py`, `test_history.py`, `test_clinical.py`, `test_encounters.py` |
| RF-07 Dashboard | `test_integration.py::test_07_dashboard` e fluxo vertical real |
| RF-08 Faturação mock | `test_invoices.py`, incluindo tenant, cancelamento terminal e adaptador mock |
| RF-09 Utilizadores | `test_users.py`, `test_auth.py::test_temporary_password_change_and_logout_revoke_both_tokens`, `Users.test.tsx` |
| RF-10 Sala de espera e serviços | `test_waiting_room.py`, `test_encounters.py::test_admin_can_configure_service_and_exam_catalog` |
| RF-11 Atendimento estruturado | `test_encounters.py`, `test_clinical.py`, `test_integration.py::test_10_vertical_mvp_flow` |

## Treze critérios verticais

| # | Critério | Teste/evidência |
|---:|---|---|
| 1 | Receção cria dono, animal e consulta | `test_integration.py::test_10_vertical_mvp_flow` |
| 2 | Sobreposição do veterinário é rejeitada | `test_appointments.py::test_create_appointment_rejects_overlap` e teste concorrente real `test_11_concurrent_appointments_return_conflict` |
| 3 | Veterinário inicia, regista e conclui | `test_10_vertical_mvp_flow`, `test_appointments.py::test_appointment_status_flow_and_cancel_reason` |
| 4 | Consulta e tratamento surgem no histórico | `test_history.py::test_pet_history_returns_appointments_and_treatment` |
| 5 | Vacina e medicamento estruturados surgem na linha clínica | `test_clinical.py::test_vaccination_crud_void_and_history`, `test_encounters.py::test_clinical_record_saves_exam_and_structured_medication` |
| 6 | Anulação exige motivo e preserva registo | `test_clinical.py`, `test_invoices.py::test_cancel_invoice_requires_reason_and_is_terminal` |
| 7 | Receção lê e recebe 403 ao escrever clínica | `test_encounters.py::test_receptionist_can_read_but_not_write_clinical_record` |
| 8 | Cobrança sincroniza e recebe referência | `test_invoices.py::test_sync_invoice_uses_mock_adapter` |
| 9 | Segundo tenant não vê os registos | `test_integration.py::test_08_cross_tenant_isolation` e testes `*_scoped_by_clinic` |
| 10 | Chegada e abertura pela fila | `test_10_vertical_mvp_flow`, `test_waiting_room.py::test_waiting_room_check_in_and_transitions` |
| 11 | Walk-in cria consulta e fila isoladas | `test_waiting_room.py::test_waiting_room_supports_walk_in` |
| 12 | Anamnese, achado anormal e medicamento persistem | `test_encounters.py::test_clinical_record_saves_exam_and_structured_medication` |
| 13 | Administrador cria serviço, sistema e achado | `test_encounters.py::test_admin_can_configure_service_and_exam_catalog` |

## Migração e recuperação

`test_postgres_migrations.py` aplica a cadeia numa base PostgreSQL vazia e numa base da revisão anterior com dados, verifica o backfill e a constraint GiST. O smoke Compose valida que a migração one-shot precede o backend. O ensaio de restauro descrito em `operacao-piloto.md` continua obrigatório antes da entrada de dados reais.
