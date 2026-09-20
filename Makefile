# ============================================================================
# Sotooh — Makefile
# Every target runs through docker compose so only Docker is required.
# ============================================================================

.DEFAULT_GOAL := help
COMPOSE = docker compose
COMPOSE_PROD = docker compose -f docker-compose.prod.yml

# ------------------------------------------------------------- Environment
.PHONY: setup
setup: ## Create .env from example and start all dev services
	$(COMPOSE) --env-file .env up -d --build

.PHONY: dev
dev: ## Start local dev environment (docker compose up)
	$(COMPOSE) up -d
	@echo "backend:  http://localhost:8000"
	@echo "frontend: http://localhost:5173"
	@echo "minio:    http://localhost:9001"

.PHONY: down
down: ## Stop the dev environment
	$(COMPOSE) down

.PHONY: down-v
down-v: ## Stop dev environment and remove volumes (DESTRUCTIVE)
	$(COMPOSE) down -v

.PHONY: logs
logs: ## Tail all logs
	$(COMPOSE) logs -f --tail=100

.PHONY: ps
ps: ## Show running services
	$(COMPOSE) ps

# ----------------------------------------------------------------- Django
.PHONY: migrate
migrate: ## Apply database migrations
	$(COMPOSE) exec backend uv run python manage.py migrate

.PHONY: makemigrations
makemigrations: ## Generate migrations for all apps
	$(COMPOSE) exec backend uv run python manage.py makemigrations

.PHONY: shell
shell: ## Open a Django shell inside the backend container
	$(COMPOSE) exec backend uv run python manage.py shell

.PHONY: createsuperuser
createsuperuser: ## Create a Django superuser
	$(COMPOSE) exec backend uv run python manage.py createsuperuser

.PHONY: seed
seed: ## Load demo data (local dev only)
	$(COMPOSE) exec backend uv run python manage.py seed_demo

.PHONY: pdf-fonts
pdf-fonts: ## Download Noto Sans Arabic / Inter fonts into backend/assets/fonts
	$(COMPOSE) run --rm --no-deps backend uv run python manage.py download_fonts

# ------------------------------------------------------------------- Tests
.PHONY: test
test: ## Run backend tests
	$(COMPOSE) exec -T backend uv run python -m pytest -v

.PHONY: lint
lint: ## Run backend lint (ruff) + frontend lint
	$(COMPOSE) exec -T backend uv run ruff check .
	$(COMPOSE) exec -T backend uv run ruff format --check .
	cd frontend && npm run lint && npm run typecheck

.PHONY: format
format: ## Auto-format backend + frontend
	$(COMPOSE) exec -T backend uv run ruff format .
	$(COMPOSE) exec -T backend uv run ruff check --fix .
	cd frontend && npm run format

.PHONY: typecheck
typecheck: ## Run frontend TypeScript check
	cd frontend && npm run typecheck

# -------------------------------------------------------------------- E2E
.PHONY: e2e
e2e: ## Run Playwright E2E tests (requires dev environment running)
	cd frontend && npm run test:e2e

# --------------------------------------------------------------- Analytics
.PHONY: analytics
analytics: ## Query ClickHouse product metrics summary (via backend)
	$(COMPOSE) exec -T backend uv run python manage.py analytics_summary

# ------------------------------------------------------------ Production
.PHONY: build
build: ## Build production images
	$(COMPOSE_PROD) --env-file .env build

.PHONY: deploy
deploy: ## Production deploy: build, migrate, collectstatic, restart, health
	bash scripts/deploy.sh

.PHONY: backup
backup: ## Dump production PostgreSQL to backups/
	bash scripts/backup.sh

.PHONY: restore
restore FILE=backups/backup.sql.gz ## Restore production PostgreSQL from a dump
	bash scripts/restore.sh $(FILE)

# ------------------------------------------------------------------- Help
.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'
