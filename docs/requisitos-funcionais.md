# PATAS — Requisitos Funcionais do MVP Clínico

## Objetivo

O PATAS apoia a operação diária de uma clínica veterinária: a receção regista donos e animais, agenda consultas e acompanha o estado da agenda; o veterinário realiza o atendimento e regista o histórico clínico. A faturação desta versão é apenas um registo local com adaptador mock para integração futura.

## Atores e permissões

| Ator | Capacidades |
|---|---|
| Rececionista | Gerir donos e animais; criar, alterar, cancelar e consultar consultas; consultar histórico clínico e faturas. |
| Veterinário | Tudo o que o rececionista faz; iniciar/concluir atendimentos; registar e atualizar tratamentos e exame físico. |
| Administrador | Todas as capacidades; gerir utilizadores, tipos de serviço e catálogo de exame físico. |

Todos os dados são isolados pela clínica do utilizador autenticado.

## Requisitos

### RF-01 — Autenticação e clínica

1. O registo público cria sempre uma clínica e o primeiro administrador; não aceita perfil escolhido pelo cliente.
2. O utilizador deve iniciar sessão com email e palavra-passe e a sessão deve disponibilizar utilizador, perfil, clínica e estado de palavra-passe temporária.
3. O frontend deve renovar a sessão usando refresh token rotativo antes de exigir novo login; refresh tokens não autenticam endpoints protegidos.
4. O logout revoga o access token apresentado e o refresh token da sessão.
5. Uma conta criada pelo administrador começa com palavra-passe temporária e só pode consultar a própria identidade, trocar palavra-passe ou terminar sessão até concluir a troca.
6. Um utilizador nunca pode consultar ou alterar dados de outra clínica.

### RF-02 — Donos

1. Rececionistas, veterinários e administradores podem criar, consultar, editar, pesquisar e arquivar donos.
2. O dono pode conter nome, telefone, email, morada e notas.
3. O arquivo é auditável, oculta o dono das listas normais, preserva o histórico e arquiva os seus animais ativos na mesma transação.

### RF-03 — Animais

1. Um animal pertence a exatamente um dono e uma clínica.
2. A ficha inclui nome, espécie, raça, data de nascimento, peso atual e notas.
3. O sistema deve permitir abrir a ficha clínica do animal.
4. Um animal arquivado permanece no histórico, fica oculto das listas normais e não pode originar novas consultas ou faturas.

### RF-04 — Agendamento

1. Uma consulta deve indicar animal, veterinário, data/hora, duração, motivo e notas.
2. O veterinário indicado deve pertencer à mesma clínica e ter perfil clínico (`vet` ou administrador responsável).
3. O sistema deve rejeitar sobreposição de intervalos ativos do mesmo veterinário.
4. Consultas canceladas ou marcadas como falta não bloqueiam novos horários.
5. A receção deve conseguir consultar a agenda por data.

### RF-05 — Ciclo de atendimento

1. O ciclo normal é `scheduled` → `in-progress` → `completed`.
2. Uma consulta também pode terminar como `cancelled` ou `no-show`.
3. O cancelamento exige motivo.
4. Consultas iniciadas ou concluídas não podem ser apagadas nem reabertas através do fluxo normal.
5. A remoção solicitada pela interface deve resultar em cancelamento auditável, nunca em perda do registo clínico.
6. As únicas transições válidas são `scheduled` → `in-progress|cancelled|no-show` e `in-progress` → `completed`; estados terminais não reabrem.
7. Animal, veterinário, horário, duração e serviço só podem ser alterados enquanto a consulta está `scheduled`; cancelamento e falta exigem motivo.

### RF-06 — Tratamento e histórico clínico

1. Um veterinário ou administrador pode registar diagnóstico, prescrição e notas numa consulta.
2. O histórico do animal deve apresentar consultas e tratamentos em ordem cronológica inversa.
3. Cada entrada deve mostrar data, veterinário, motivo, estado, peso, notas, diagnóstico e prescrição quando existirem.
4. A receção pode consultar o histórico, mas não pode editar tratamentos.
5. A linha clínica deve combinar consultas, diagnósticos, tratamentos, vacinas, medicamentos, peso e faturas em ordem cronológica inversa.
6. A vacina deve guardar nome, data de administração, dose, lote, validade, próxima dose, veterinário, consulta opcional, notas e estado `administered` ou `voided`.
7. O medicamento deve guardar nome, dosagem, frequência, via, datas de início/fim, instruções, notas, veterinário, consulta opcional e estado `active`, `completed`, `cancelled` ou `voided`.
8. A receção tem permissão `clinical:read`; apenas veterinários e administradores têm `clinical:write`.
9. Vacinas e medicamentos não podem ser apagados fisicamente. A anulação exige motivo, mantém o registo no histórico e exclui-o dos contadores ativos.
10. Tratamentos não podem ser apagados fisicamente; correções permanecem associadas e auditadas.

### RF-07 — Dashboard

1. O dashboard deve apresentar totais reais da clínica.
2. Deve mostrar consultas do dia por estado, incluindo atendimentos em curso.
3. Deve mostrar as próximas consultas ativas.
4. Os contadores da navegação não podem ser valores fixos no frontend.

### RF-08 — Faturação mock

1. Um utilizador autorizado pode criar um registo de cobrança associado ao dono e opcionalmente à consulta.
2. A consulta associada deve pertencer ao mesmo dono e clínica.
3. O registo usa moeda AOA e estados `draft`, `sent`, `paid` e `cancelled`.
4. O cancelamento exige motivo.
5. O adaptador mock deve criar uma referência externa local e marcar a sincronização como `synced`.
6. O endpoint de estado deve permitir substituir futuramente o adaptador sem alterar o fluxo clínico.
7. Não são processados pagamentos reais nesta versão.
8. Rececionistas, veterinários e administradores podem criar e consultar faturas; não existe eliminação física e `paid`/`cancelled` são terminais.

### RF-09 — Gestão de utilizadores

1. Apenas administradores podem listar utilizadores da clínica.
2. Apenas administradores podem alterar o perfil de outro utilizador.
3. Um administrador não pode alterar o próprio perfil através deste fluxo.
4. Apenas administradores podem criar contas na sua clínica, indicando perfil e palavra-passe temporária; essa palavra-passe não é devolvida nem armazenada no frontend após o pedido.

### RF-10 — Sala de espera e serviços

1. A receção deve conseguir consultar a sala de espera por data, serviço, estado e pesquisa por animal/dono.
2. Uma entrada pode nascer de uma consulta agendada ou de um atendimento sem marcação.
3. Um atendimento sem marcação cria consulta e entrada de fila de forma transacional.
4. Uma consulta não pode ser adicionada duas vezes à mesma sala de espera.
5. A fila deve suportar os estados `waiting`, `called`, `in-progress`, `completed`, `cancelled` e `no-show`.
6. As transições de fila devem atualizar o estado da consulta correspondente e gerar auditoria.
7. Os tipos de serviço são próprios da clínica, podem ser ordenados/renomeados/arquivados pelo administrador e não podem ser apagados quando têm histórico.
8. As transições válidas são `waiting` → `called|cancelled|no-show`, `called` → `in-progress|cancelled|no-show` e `in-progress` → `completed`; fila e consulta permanecem sincronizadas nos dois sentidos.

### RF-11 — Atendimento clínico estruturado

1. O veterinário deve conseguir abrir um atendimento a partir da fila ou da ficha do animal.
2. O atendimento deve guardar anamnese, tipo de consulta, diagnóstico, notas, veterinário referenciador e prescrição livre.
3. A prescrição deve permitir linhas estruturadas com medicamento, dosagem, frequência, via, datas e instruções.
4. O exame físico deve apresentar sistemas e achados configuráveis por clínica, com estados normal, anormal ou não avaliado e observação opcional.
5. O catálogo de sistemas e achados só pode ser alterado pelo administrador; valores arquivados devem continuar visíveis em históricos antigos.
6. A receção pode consultar o atendimento, mas não pode alterar o seu conteúdo clínico.
7. O histórico do animal deve devolver o tipo de serviço e os achados físicos associados à consulta.

## Tempo funcional

Agenda, dashboard e sala de espera usam `Africa/Luanda`. Instantes são armazenados em UTC e convertidos apenas nas fronteiras da API e da interface.

## Interfaces principais

- `GET /api/v1/appointments/vets` — veterinários disponíveis na clínica.
- `PATCH /api/v1/appointments/{id}` — atualização validada de horário, estado e dados do atendimento.
- `GET /api/v1/pets/{id}/history` — histórico clínico agregado.
- `GET/POST/PATCH /api/v1/vaccinations/` e `POST /api/v1/vaccinations/{id}/void` — vacinas estruturadas.
- `GET/POST/PATCH /api/v1/medications/` e `POST /api/v1/medications/{id}/void` — medicamentos estruturados.
- `POST /api/v1/invoices/{id}/sync` — sincronização com o adaptador mock.
- `GET /api/v1/invoices/{id}/sync-status` — estado local e externo da sincronização.
- `GET/POST/PATCH /api/v1/service-types/` — tipos de serviço da clínica.
- `GET /api/v1/waiting-room/` e `POST/PATCH /api/v1/waiting-room/entries` — sala de espera e entradas.
- `POST /api/v1/waiting-room/entries/{id}/transition` — transição auditada da fila.
- `GET /api/v1/exam-catalog/` — catálogo de exame físico.
- `POST/PATCH /api/v1/exam-catalog/systems` e `POST/PATCH /api/v1/exam-catalog/findings` — configuração do catálogo por administradores.
- `GET/PUT /api/v1/appointments/{id}/clinical-record` — atendimento clínico agregado.

## Critérios de aceitação do fluxo vertical

1. A receção cria um dono, animal e consulta para um veterinário da própria clínica.
2. Uma segunda consulta sobreposta para o mesmo veterinário é rejeitada.
3. O veterinário inicia e conclui o atendimento, registando peso e tratamento.
4. A ficha do animal apresenta a consulta e o tratamento no histórico.
5. Um veterinário regista uma vacina e um medicamento estruturados na ficha do animal; ambos aparecem na linha clínica.
6. A anulação de qualquer registo exige motivo e mantém a entrada visível com estado anulado.
7. A receção consegue consultar o histórico, mas recebe `403` ao tentar alterar um registo clínico.
8. Um registo de cobrança é criado, enviado ao adaptador mock e recebe referência externa.
9. Um utilizador de outra clínica não consegue ver nenhum dos registos.
10. A receção regista a chegada de uma consulta e o veterinário abre o atendimento a partir da sala de espera.
11. Um walk-in cria consulta, entrada na fila e histórico clínico sem dados de outra clínica.
12. O veterinário guarda anamnese, achado físico anormal e medicamento estruturado; esses dados aparecem no histórico do animal.
13. O administrador cria um novo serviço, sistema e achado; estes ficam disponíveis na fila e no atendimento.
