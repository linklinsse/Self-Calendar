# ╔══════════════════════════════════════════════════════════════╗
# ║  SELF CALENDAR — Makefile                                    ║
# ║                                                              ║
# ║  Targets:                                                    ║
# ║    make init          Install all dependencies               ║
# ║    make dev           Start Vite dev server (hot reload)     ║
# ║    make build         Production web build → dist/          ║
# ║    make preview       Preview the production build locally   ║
# ║    make android       Build + open in Android Studio         ║
# ║    make ios           Build + open in Xcode                  ║
# ║    make sync          Sync web assets to native platforms     ║
# ║    make lint          Run svelte-check type-checking          ║
# ║    make clean         Remove dist/ and node_modules/         ║
# ╚══════════════════════════════════════════════════════════════╝

# ── Configuration ────────────────────────────────────────────
NODE    := node
NPM     := npm
VITE    := npx vite
CAP     := npx cap

DIST    := dist
SRC     := src

# Detect OS for open command
UNAME := $(shell uname -s 2>/dev/null || echo Windows)
ifeq ($(UNAME),Darwin)
  OPEN := open
else ifeq ($(UNAME),Linux)
  OPEN := xdg-open
else
  OPEN := start
endif

.PHONY: all init dev build preview android ios sync lint clean help

# Default target
all: build

# ── help ─────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  Self Calendar — available targets:"
	@echo ""
	@echo "  make init        Install npm dependencies + Capacitor"
	@echo "  make dev         Start Vite dev server with HMR"
	@echo "  make build       Production web build → dist/"
	@echo "  make preview     Preview the production build"
	@echo "  make android     Build web + sync + open Android Studio"
	@echo "  make ios         Build web + sync + open Xcode"
	@echo "  make sync        Sync latest web build to native platforms"
	@echo "  make lint        Run svelte-check (type/style checks)"
	@echo "  make clean       Remove dist/ and node_modules/"
	@echo ""

# ── init ─────────────────────────────────────────────────────
# Install web deps, then install Capacitor CLI + native platforms
init:
	@echo "→ Installing npm dependencies…"
	$(NPM) install
	@echo "→ Installing Capacitor CLI + plugins…"
	$(NPM) install --save-dev \
	  @capacitor/cli \
	  @capacitor/core \
	  @capacitor/android \
	  @capacitor/ios
	@echo "→ Initialising Capacitor (if not already done)…"
	@if [ ! -f capacitor.config.json ]; then \
	  $(CAP) init "Self Calendar" "app.selfcalendar.app" --web-dir dist; \
	fi
	@echo "→ Adding native platforms (if not present)…"
	@if [ ! -d android ]; then $(CAP) add android; fi
	@if [ ! -d ios ];     then $(CAP) add ios;     fi
	@echo "✓ Init complete. Run 'make dev' to start."

# ── dev ──────────────────────────────────────────────────────
dev:
	$(VITE)

# ── build ────────────────────────────────────────────────────
build:
	@echo "→ Building production web assets…"
	$(VITE) build
	@echo "✓ Web build complete → $(DIST)/"

# ── preview ──────────────────────────────────────────────────
preview: build
	$(VITE) preview

# ── sync ─────────────────────────────────────────────────────
# Copy the latest dist/ output into android/assets and ios
sync: build
	@echo "→ Syncing web assets to native platforms…"
	$(CAP) sync
	@echo "✓ Sync complete."

# ── android ──────────────────────────────────────────────────
android: sync
	@echo "→ Opening Android Studio…"
	$(CAP) open android

# ── ios ──────────────────────────────────────────────────────
ios: sync
	@echo "→ Opening Xcode…"
	$(CAP) open ios

# ── lint ─────────────────────────────────────────────────────
lint:
	@echo "→ Running svelte-check…"
	$(NPM) exec svelte-check -- --tsconfig ./jsconfig.json || true

# ── clean ────────────────────────────────────────────────────
clean:
	@echo "→ Removing dist/ and node_modules/…"
	rm -rf $(DIST) node_modules
	@echo "✓ Clean complete."
