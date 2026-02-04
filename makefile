.PHONY: up down build clean validate config ps logs

# Detect compose command
DOCKER_COMPOSE := $(shell command -v docker-compose 2> /dev/null || echo "docker compose")

# Default target
all: validate up

validate:
	@echo "Validating docker-compose.yml..."
	@$(DOCKER_COMPOSE) config > /dev/null && echo "✓ docker-compose.yml is valid" || (echo "✗ docker-compose.yml is invalid"; exit 1)

config:
	@$(DOCKER_COMPOSE) config

up: validate
	@echo "Starting services..."
	@$(DOCKER_COMPOSE) up

build: validate
	@echo "Building services..."
	@$(DOCKER_COMPOSE) build --no-cache=false

rebuild: clean validate
	@echo "Rebuilding services..."
	@$(DOCKER_COMPOSE) up --build

down:
	@echo "Stopping services..."
	@$(DOCKER_COMPOSE) down

clean:
	@echo "Cleaning up..."
	@$(DOCKER_COMPOSE) down -v --remove-orphans
 

restart: down up

logs:
	@$(DOCKER_COMPOSE) logs -f

ps:
	@$(DOCKER_COMPOSE) ps

# For debugging
debug:
	@echo "Docker Compose command: $(DOCKER_COMPOSE)"
	@echo "Docker version:"
	@docker --version
	@echo -e "\nDocker Compose version:"
	@$(DOCKER_COMPOSE) version
	@echo -e "\nCurrent directory: $(shell pwd)"
	@echo -e "\nFiles in current directory:"
	@ls -la

# Build specific service
build-%: validate
	@echo "Building $* service..."
	@$(DOCKER_COMPOSE) build $*
