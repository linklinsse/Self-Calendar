.PHONY: help dev test lint docker-build lint-fix init

# Couleurs
GREEN  := \033[0;32m
YELLOW := \033[1;33m
BLUE   := \033[0;34m
RED    := \033[0;31m
NC     := \033[0m

# Variables
DOCKER_IMAGE := fastapi-app

# ============================================================================
# AIDE
# ============================================================================

help:
	@echo "$(BLUE)╔═══════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║          Makefile - Projet Self Calendar                  ║$(NC)"
	@echo "$(BLUE)╚═══════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Installation:$(NC)"
	@echo "  make init             - Initialiser le projet complet"
	@echo ""
	@echo "$(GREEN)Développement:$(NC)"
	@echo "  make dev              - Lancer l'app en mode développement"
	@echo ""
	@echo "$(GREEN)Tests:$(NC)"
	@echo "  make test             - Lancer tous les tests"
	@echo ""
	@echo "$(GREEN)Quality:$(NC)"
	@echo "  make lint             - Vérifier avec Ruff"
	@echo "  make lint-fix         - Vérifier avec Ruff + Fix"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-build     - Compiler l'image Docker"
	@echo ""

# ============================================================================
# SETUP
# ============================================================================

init:
	@echo "$(GREEN)→ Initialisation du projet en Dev...$(NC)"
	@echo ""
	uv venv $(VENV)
	uv sync --dev
	@echo ""
	@echo "$(GREEN)✅ Projet initialisé!$(NC)"

# ============================================================================
# DÉVELOPPEMENT
# ============================================================================

dev:
	@echo "$(GREEN)→ Lancement en mode développement...$(NC)"
	uv run fastapi dev app/app.py

# ============================================================================
# TESTS
# ============================================================================

test:
	@echo "$(GREEN)→ Lancement des tests...$(NC)"
	uv run pytest

# ============================================================================
# QUALITY
# ============================================================================

lint:
	@echo "$(GREEN)→ Vérification avec Ruff...$(NC)"
	uv run ruff check ; uv run ruff format

lint-fix:
	@echo "$(GREEN)→ Correction automatique...$(NC)"
	uv run ruff check --fix ; uv run ruff format

# ============================================================================
# DOCKER
# ============================================================================

docker-build:
	@echo "$(GREEN)→ Construction Docker...$(NC)"
	docker build -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)✓ Image: $(DOCKER_IMAGE)$(NC)"
