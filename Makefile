# ════════════════════════════════════════════════════════════════════════════
# PATAS — Developer Makefile
# Run `make help` to see all available targets.
# ════════════════════════════════════════════════════════════════════════════

# ── Colours ─────────────────────────────────────────────────────────────────
BLUE  := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED  := \033[31m
RESET := \033[0m

define info
	@echo "$(BLUE)ℹ  $(RESET)$1"
endef

define success
	@echo "$(GREEN)✓  $(RESET)$1"
endef

define warn
	@echo "$(YELLOW)⚠  $(RESET)$1"
endef

define error
	@echo "$(RED)✗  $(RESET)$1"
endef

# ── Help ─────────────────────────────────────────────────────────────────────
.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}'

# ── Development ──────────────────────────────────────────────────────────────
.PHONY: dev
dev: ## Start full development environment (with hot-reload)
	docker compose -f docker-compose.yml -f infra/docker-compose.dev.yml up -d
	@echo ""
	$(info Backend:   http://localhost:8000)
	$(info Frontend:  http://localhost:3000)
	$(info API docs:  http://localhost:8000/docs)

.PHONY: dev-backend
dev-backend: ## Start backend only (with hot-reload)
	docker compose -f docker-compose.yml -f infra/docker-compose.dev.yml up -d db redis backend
	$(info Backend running at http://localhost:8000)

.PHONY: dev-frontend
dev-frontend: ## Start frontend only (hot-reload via Vite)
	docker compose -f docker-compose.yml -f infra/docker-compose.dev.yml up -d frontend

# ── Production ───────────────────────────────────────────────────────────────
.PHONY: prod
prod: ## Start production environment (requires .env with real secrets)
	docker compose -f infra/docker-compose.yml up -d
	$(info Running in production mode)

# ── Database ─────────────────────────────────────────────────────────────────
.PHONY: seed
seed: ## Run database seed script
	docker exec patas_backend python -c "import sys; sys.path.insert(0,'/app'); from src.seed import main; main()"
	$(success Seed complete)

.PHONY: migrate
migrate: ## Run Alembic migrations
	docker exec patas_backend alembic upgrade head
	$(success Migrations applied)

.PHONY: db-logs
db-logs: ## View database logs
	docker logs patas_db --tail 50 -f

# ── Backend ───────────────────────────────────────────────────────────────────
.PHONY: test
test: ## Run all backend tests
	docker exec patas_backend bash -c "rm -rf /app/tests/__pycache__ /app/src/__pycache__ && PYTHONPATH=/app pytest tests/ -q --tb=short"
	$(success All tests passed)

.PHONY: test-api
test-api: ## Test a single API endpoint ( Usage: make test-api URL=/health )
	docker exec patas_backend python -c "import urllib.request; r=urllib.request.urlopen('http://localhost:8000$(URL)'); print(r.read().decode())"

.PHONY: lint
lint: ## Run ruff linter
	docker exec patas_backend bash -c "cd /app && pip install -q ruff && ruff check src/"
	$(success Lint clean)

# ── Frontend ───────────────────────────────────────────────────────────────────
.PHONY: build-ui
build-ui: ## Build frontend for production
	cd frontend && npm install && npm run build
	docker cp frontend/dist/. patas_frontend:/usr/share/nginx/html/
	docker exec patas_frontend nginx -s reload
	$(success Frontend built and deployed to container)

.PHONY: preview-ui
preview-ui: ## Preview frontend locally (port 5173)
	cd frontend && npm run dev

# ── Docker ────────────────────────────────────────────────────────────────────
.PHONY: stop
stop: ## Stop all containers
	docker compose -f docker-compose.yml stop

.PHONY: down
down: ## Stop and remove all containers and volumes
	docker compose -f docker-compose.yml down -v

.PHONY: logs
logs: ## View backend logs ( Usage: make logs SERVICE=backend )
	docker logs patas_$(SERVICE) --tail 100 -f

.PHONY: ps
ps: ## Show running containers
	docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

.PHONY: rebuild
rebuild: ## Rebuild all images (no cache)
	docker compose -f docker-compose.yml build --no-cache
	docker compose -f docker-compose.yml up -d
	$(success All images rebuilt and containers restarted)

.PHONY: restart
restart: ## Restart a specific service ( Usage: make restart SERVICE=backend )
	docker compose -f docker-compose.yml restart $(SERVICE)
	$(success Service $(SERVICE) restarted)

# ── CI ─�───────────────────────────────────────────────────────────────────────
.PHONY: ci
ci: lint test ## Run lint + tests (what CI does locally)
	$(success CI checks passed)

# ── Cleanup ────────────────────────────────────────────────────────────────────
.PHONY: clean
clean: ## Remove node_modules, __pycache__, .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null; true
	rm -rf frontend/node_modules/frontend/.vite 2>/dev/null; true
	$(success Cleaned)
