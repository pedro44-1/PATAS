# PATAS

SaaS de gestão clínica veterinária para Angola, com interface portuguesa e operação funcional em `Africa/Luanda`.

## MVP

O percurso coberto inclui:

- registo de clínica, administrador e equipa com palavra-passe temporária;
- isolamento por clínica e perfis `admin`, `vet` e `receptionist`;
- donos e animais com arquivo lógico e histórico preservado;
- agenda sem sobreposição, sala de espera e ciclo clínico transacional;
- exame estruturado, tratamentos, vacinas e medicação;
- faturação local com adaptador mock, sem pagamentos reais;
- dashboard com dados da clínica e frontend português-first.

Os requisitos e respetivos testes estão em [requisitos funcionais](docs/requisitos-funcionais.md) e na [matriz de rastreabilidade](docs/matriz-rastreabilidade.md).

## Desenvolvimento

Backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL='sqlite:///./patas_dev.db'
alembic upgrade head
uvicorn src.main:app --reload
```

Frontend, noutro terminal:

```powershell
npm install
npm run dev --workspace=frontend
```

O Vite abre em `http://localhost:3000` e encaminha `/api` para o backend em `http://localhost:8000`.

## Piloto LAN

```powershell
Copy-Item infra/.env.example infra/.env
# Defina segredos fortes em infra/.env.
docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --build
Invoke-WebRequest http://localhost/health -UseBasicParsing
```

O perfil do piloto publica apenas HTTP/80. A migração Alembic é um serviço one-shot e o backend só arranca após o seu sucesso. Consulte o [runbook do piloto](docs/operacao-piloto.md) antes de usar dados reais; backup PostgreSQL e ensaio de restauro são obrigatórios.

## Verificação

```powershell
cd backend
$env:PYTHONPATH='.'
pytest tests/ -q
ruff check src/

cd ..
npm run test --workspace=frontend
npm run build
scripts/run_integration_tests.ps1
```

O runner de integração usa PostgreSQL e Redis reais, valida migrações de base vazia e anterior, o percurso vertical e a concorrência de agenda. A CI acrescenta o smoke test do Compose LAN.

## Arquitetura

- Backend: Python 3.11, FastAPI, SQLAlchemy 2, Pydantic 2, Alembic, PostgreSQL e Redis.
- Frontend: React 18, TypeScript, Vite, Tailwind e tipos de `@patas/shared-types`.
- Infraestrutura: Docker Compose e nginx; `/api/v1` e a SPA partilham o mesmo host.

Mais detalhes: [setup](docs/setup.md), [API](docs/api.md) e [operação](docs/operacao-piloto.md).
