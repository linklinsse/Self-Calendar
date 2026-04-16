.PHONY: help init dev build preview sync android ios lint clean docker-build

# Colors
GREEN  := \033[0;32m
YELLOW := \033[1;33m
BLUE   := \033[0;34m
RED    := \033[0;31m
NC     := \033[0m

# Variables
NODE         := node
NPM          := npm
CAP          := npx cap
DIST         := dist
DOCKER_IMAGE := selfcalendar-web

# Detect OS for open command
UNAME := $(shell uname -s 2>/dev/null || echo Windows)
ifeq ($(UNAME),Darwin)
  OPEN := open
else ifeq ($(UNAME),Linux)
  OPEN := xdg-open
else
  OPEN := start
endif

# ============================================================================
# HELP
# ============================================================================

help:
	@echo "$(BLUE)╔═══════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║            Makefile - Self Calendar (Web)                 ║$(NC)"
	@echo "$(BLUE)╚═══════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Installation:$(NC)"
	@echo "  make init             - Install dependencies + Capacitor platforms"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make dev              - Start Vite dev server (hot reload)"
	@echo ""
	@echo "$(GREEN)Build & Preview:$(NC)"
	@echo "  make build            - Production web build → $(DIST)/"
	@echo "  make preview          - Preview the production build locally"
	@echo ""
	@echo "$(GREEN)Native (Capacitor):$(NC)"
	@echo "  make sync             - Sync web assets to native platforms"
	@echo "  make android          - Build + sync + open Android Studio"
	@echo "  make ios              - Build + sync + open Xcode"
	@echo ""
	@echo "$(GREEN)Quality:$(NC)"
	@echo "  make lint             - Run svelte-check (type & style checks)"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-build     - Build the Docker image"
	@echo ""
	@echo "$(GREEN)Maintenance:$(NC)"
	@echo "  make clean            - Remove $(DIST)/ and node_modules/"
	@echo ""

# ============================================================================
# SETUP
# ============================================================================

init:
	@echo "$(GREEN)→ Installing npm dependencies…$(NC)"
	$(NPM) install
	@echo "$(GREEN)→ Installing Capacitor CLI + plugins…$(NC)"
	$(NPM) install --save-dev \
	  @capacitor/cli \
	  @capacitor/core \
	  @capacitor/android \
	  @capacitor/ios
	@echo "$(GREEN)→ Initialising Capacitor (if not already done)…$(NC)"
	@if [ ! -f capacitor.config.json ]; then \
	  $(CAP) init "Self Calendar" "app.selfcalendar.app" --web-dir dist; \
	fi
	@echo "$(GREEN)→ Adding native platforms (if not present)…$(NC)"
	@if [ ! -d android ]; then $(CAP) add android; fi
	@if [ ! -d ios ];     then $(CAP) add ios;     fi
	@echo ""
	@echo "$(GREEN)✅ Init complete. Run 'make dev' to start.$(NC)"

# ============================================================================
# DEVELOPMENT
# ============================================================================

dev:
	@echo "$(GREEN)→ Starting Vite dev server…$(NC)"
	$(NPM) run dev

# ============================================================================
# BUILD & PREVIEW
# ============================================================================

build:
	@echo "$(GREEN)→ Building production web assets…$(NC)"
	$(NPM) run build
	@echo "$(GREEN)✅ Build complete → $(DIST)/$(NC)"

preview: build
	@echo "$(GREEN)→ Starting preview server…$(NC)"
	$(NPM) run preview

# ============================================================================
# NATIVE (CAPACITOR)
# ============================================================================

sync: build
	@echo "$(GREEN)→ Syncing web assets to native platforms…$(NC)"
	$(CAP) sync
	@echo "$(GREEN)✓ Sync complete.$(NC)"

android: sync
	@echo "$(GREEN)→ Opening Android Studio…$(NC)"
	$(CAP) open android

ios: sync
	@echo "$(GREEN)→ Opening Xcode…$(NC)"
	$(CAP) open ios

# ============================================================================
# QUALITY
# ============================================================================

lint:
	@echo "$(GREEN)→ Running svelte-check…$(NC)"
	$(NPM) run check

# ============================================================================
# DOCKER
# ============================================================================

docker-build:
	@echo "$(GREEN)→ Building Docker image…$(NC)"
	docker build -t $(DOCKER_IMAGE):latest .
	@echo "$(GREEN)✓ Image: $(DOCKER_IMAGE)$(NC)"

# ============================================================================
# MAINTENANCE
# ============================================================================

clean:
	@echo "$(RED)→ Removing $(DIST)/ and node_modules/…$(NC)"
	rm -rf $(DIST) node_modules
	@echo "$(GREEN)✓ Clean complete.$(NC)"
