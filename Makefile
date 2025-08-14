COMPOSE_PROJECT_NAME_DEV=devmentor_dev
COMPOSE_PROJECT_NAME_PROD=devmentor_prod

COMPOSE_FILE_DEV = docker/docker-compose.yaml
COMPOSE_FILE_PROD = docker/docker-compose.prod.yaml
ENV_FILE = .env

DC_DEV=docker compose -f $(COMPOSE_FILE_DEV) -p $(COMPOSE_PROJECT_NAME_DEV) --env-file $(ENV_FILE)
DC_PROD=docker compose -f $(COMPOSE_FILE_PROD) -p $(COMPOSE_PROJECT_NAME_PROD) --env-file $(ENV_FILE)

.PHONY: help \
build-dev up-dev down-dev stop-dev restart-dev logs-dev shell-dev \
makemigrations-dev migrate-dev superuser-dev static-dev ollama_pull-dev \
build-prod up-prod down-prod stop-prod restart-prod logs-prod shell-prod \
migrate-prod superuser-prod ollama_pull-prod \
ollama_pull

# ====================================================================================

build-dev:
	$(DC_DEV) build

up-dev:
	$(DC_DEV) up -d

down-dev:
	$(DC_DEV) down -v

stop-dev:
	$(DC_DEV) stop

restart-dev:
	$(DC_DEV) restart $(s)

logs-dev:
	$(DC_DEV) logs -f $(s)

shell-dev:
	$(DC_DEV) exec $(s) sh

makemigrations-dev:
	$(DC_DEV) exec backend python backend/manage.py makemigrations

migrate-dev:
	$(DC_DEV) exec backend python backend/manage.py migrate

superuser-dev:
	$(DC_DEV) exec backend python backend/manage.py createsuperuser

static-dev:
	$(DC_DEV) exec backend python backend/manage.py collectstatic --noinput

ollama_pull-dev:
	$(DC_DEV) exec ollama ollama pull $(m)

# ====================================================================================

build-prod:
	$(DC_PROD) build

up-prod:
	$(DC_PROD) up -d

down-prod:
	$(DC_PROD) down -v

stop-prod:
	$(DC_PROD) stop

restart-prod:
	$(DC_PROD) restart $(s)

logs-prod:
	$(DC_PROD) logs -f $(s)

shell-prod:
	$(DC_PROD) exec $(s) sh

migrate-prod:
	$(DC_PROD) exec backend python backend/manage.py migrate

superuser-prod:
	$(DC_PROD) exec backend python backend/manage.py createsuperuser

ollama_pull-prod:
	$(DC_PROD) exec ollama ollama pull $(m)
