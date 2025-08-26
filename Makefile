# -------- Settings --------
GH_USER      = vickot
REGISTRY     = ghcr.io/$(GH_USER)
PROJECT      = familydash
PLATFORM     = linux/arm64

DASH_CTX     = .
SCHED_CTX    = .

# Pi deploy (ssh alias eller user@host) UPPDATERA!
PI_HOST      = dashpi
PI_DIR       = ~/Projects/$(PROJECT)               # var compose-filen ligger på Pi
COMPOSE_FILE = docker-compose.yml         # prodfilen
ENV_FILE     = .env                       # finns på Pi (inte i git)

# -------- Convenience tags --------
DASH_IMG     = $(REGISTRY)/$(PROJECT)-dash:latest
SCHED_IMG    = $(REGISTRY)/$(PROJECT)-scheduler:latest

# -------- Targets --------
# .PHONY markerar att dessa targets inte är filer utan "alias"/kommandon.
# Utan .PHONY kan make tro att target redan är färdigt om en fil med samma namn råkar finnas.
.PHONY: push-dash push-scheduler push-all logs deploy-pi pull-pi up-pi restart-pi

## Bygg & pusha Dash (från lokal kod) till GHCR
push-dash:
	docker buildx build --platform $(PLATFORM) -t $(DASH_IMG) $(DASH_CTX) --push

## Bygg & pusha Scheduler (från lokal kod) till GHCR
push-scheduler:
	docker buildx build --platform $(PLATFORM) -t $(SCHED_IMG) $(SCHED_CTX) --push

## Pusha båda
push-all: push-dash push-scheduler

## Visa loggar (lokalt)
logs:
	docker compose logs -f --tail=200

## Dra ner senaste images & starta på Pi (prod; använder endast docker-compose.yml)
deploy-pi: pull-pi up-pi

pull-pi:
	ssh $(PI_HOST) "cd $(PI_DIR) && docker compose -f $(COMPOSE_FILE) pull"

up-pi:
	ssh $(PI_HOST) "cd $(PI_DIR) && docker compose -f $(COMPOSE_FILE) up -d"

## Snabb omstart på Pi (utan pull)
restart-pi:
	ssh $(PI_HOST) "cd $(PI_DIR) && docker compose -f $(COMPOSE_FILE) up -d"
