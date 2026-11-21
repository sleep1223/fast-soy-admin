# ============================================================
# FastSoyAdmin justfile
# ============================================================

host_family := os_family()

# Show all available commands.
default:
    @just --list

# Show all available commands.
help:
    @just --list

# ---- Dependencies ------------------------------------------

# Install dependencies. Target can be all, backend, or frontend.
install target='all':
    just _install-{{target}}

_install-all:
    just _install-backend
    just _install-frontend

_install-backend:
    uv sync

_install-frontend:
    cd web && pnpm install

# ---- Development -------------------------------------------

# Start dev server(s). Target can be all, backend, or frontend.
run target='all':
    just _run-{{target}}

# Stop dev server(s) started by `just run`. Target can be all, backend, or frontend.
stop target='all':
    just _stop-{{target}}

_run-all:
    just _run-{{host_family}} all

_run-backend:
    just _run-{{host_family}} backend

_run-frontend:
    just _run-{{host_family}} frontend

_run-windows target:
    powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "{{justfile_directory()}}\scripts\run-dev-windows.ps1" -Root "{{justfile_directory()}}" -Target "{{target}}"

_run-unix target:
    uv run python scripts/dev.py "{{target}}"

_stop-all:
    just _stop-{{host_family}} all

_stop-backend:
    just _stop-{{host_family}} backend

_stop-frontend:
    just _stop-{{host_family}} frontend

_stop-windows target:
    powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "{{justfile_directory()}}\scripts\stop-dev-windows.ps1" -Root "{{justfile_directory()}}" -Target "{{target}}"

_stop-unix target:
    @echo "just stop is currently implemented for Windows dev runs. On Unix, press Ctrl+C in the terminal running just run."

# Backward-compatible alias for starting both dev servers.
dev:
    just run

# ---- Quality -----------------------------------------------

# Lint code without modifying files. Target can be all, backend, or frontend.
lint target='all':
    just _lint-{{target}}

_lint-all:
    just _lint-backend
    just _lint-frontend

_lint-backend:
    uv run ruff check app/
    uv run ruff format --check app/

_lint-frontend:
    cd web && pnpm exec oxlint
    cd web && pnpm exec eslint .

# Format code and apply safe lint fixes. Target can be all, backend, or frontend.
fmt target='all':
    just _fmt-{{target}}

_fmt-all:
    just _fmt-backend
    just _fmt-frontend

_fmt-backend:
    uv run ruff check --fix app/
    uv run ruff format app/

_fmt-frontend:
    cd web && pnpm lint
    cd web && pnpm fmt

# Type check code. Target can be all, backend, or frontend.
typecheck target='all':
    just _typecheck-{{target}}

_typecheck-all:
    just _typecheck-backend
    just _typecheck-frontend

_typecheck-backend:
    uv run basedpyright app

_typecheck-frontend:
    cd web && pnpm typecheck

# Run tests. Target can be all, backend, or frontend.
test target='all':
    just _test-{{target}}

_test-all:
    just _test-backend
    just _test-frontend

_test-backend:
    uv run pytest tests/ -v

_test-frontend:
    cd web && pnpm test

# Run all quality gates. Target can be all, backend, or frontend.
check target='all':
    just _check-{{target}}

_check-all:
    just _check-backend
    just _check-frontend

_check-backend:
    just _fmt-backend
    just _typecheck-backend
    just _test-backend

_check-frontend:
    just _fmt-frontend
    just _typecheck-frontend
    just _test-frontend

# ---- Build --------------------------------------------------

# Build production artifacts. Target can be frontend or all.
build target='frontend':
    just _build-{{target}}

_build-all:
    just _build-frontend

_build-frontend:
    cd web && pnpm build

# ---- Database ----------------------------------------------

# First-time database init.
db-init:
    uv run python -m app.cli initdb

# Reset current dev database and migration baseline, then initialize again.
db-reset:
    uv run python -m app.cli initdb --force

# Generate migration files from model changes.
makemigrations:
    uv run tortoise makemigrations

# Preview SQL for a migration.
sqlmigrate app migration:
    uv run tortoise sqlmigrate {{app}} {{migration}}

# Apply pending migrations.
migrate:
    uv run tortoise migrate

# Generate + apply migrations.
mm: makemigrations migrate

# Show migration history.
dbhistory:
    uv run tortoise history

# ---- CLI ----------------------------------------------------

# Create a new business module skeleton.
cli-init mod:
    uv run python -m app.cli init "{{mod}}"

# Generate backend code from models.py.
cli-gen mod args='':
    uv run python -m app.cli gen "{{mod}}" {{args}}

# Generate frontend code from models.py.
cli-gen-web mod cn='' args='':
    uv run python -m app.cli gen-web "{{mod}}"{{ if cn == "" { "" } else { " --cn-name \"" + cn + "\"" } }} {{args}}

# Generate both backend and frontend code.
cli-gen-all mod cn='' args='':
    uv run python -m app.cli gen-all "{{mod}}"{{ if cn == "" { "" } else { " --cn-name \"" + cn + "\"" } }} {{args}}

# Generate full CRUD code (alias of cli-gen-all).
cli-crud mod cn='' args='':
    uv run python -m app.cli crud "{{mod}}"{{ if cn == "" { "" } else { " --cn-name \"" + cn + "\"" } }} {{args}}

# Undo generated frontend/backend code after backing it up.
cli-undo args='':
    uv run python -m app.cli undo {{args}}

# Dry-run business init declarations and route-key drift.
init-plan args='':
    uv run python -m app.cli init-plan {{args}}

# List discovered business modules.
module-list:
    uv run python -m app.cli module-list

# Check business import boundaries.
check-boundaries args='':
    uv run python -m app.cli check-boundaries {{args}}

# ---- E2E ----------------------------------------------------

# Reset E2E sqlite and create schema from current models.
e2e-initdb:
    uv run python scripts/e2e_init_db.py

# Run Playwright E2E tests.
e2e: e2e-initdb
    cd web && pnpm e2e

# Run Playwright in UI mode for local debugging.
e2e-ui: e2e-initdb
    cd web && pnpm e2e:ui

# Install Playwright browsers (chromium).
e2e-install:
    cd web && pnpm e2e:install

# ---- Compatibility Aliases ---------------------------------

# Install all dependencies.
install-all:
    just install

# Run all backend + frontend quality gates.
check-all:
    just check

# Install frontend dependencies.
web-install:
    just install frontend

# Start frontend dev server (:9527).
web-dev:
    just run frontend

# Production build frontend.
web-build:
    just build frontend

# Lint frontend without modifying files.
web-lint:
    just lint frontend

# Vue-tsc type check frontend.
web-typecheck:
    just typecheck frontend

# Run all frontend quality gates.
web-check:
    just check frontend

# ---- Docker -------------------------------------------------

# First-time Docker database init.
docker-db-init:
    docker compose up -d postgres redis
    docker compose run --rm app uv run python -m app.cli initdb

# Docker compose up.
up:
    docker compose up -d

# Docker compose rebuild images and recreate containers.
rebuild:
    docker compose up -d --build

# Docker compose down.
down:
    docker compose down

# Docker compose logs; usage: `just logs [svc] [tail]`.
logs svc='' tail='100':
    docker compose logs -f --tail={{tail}} {{svc}}
