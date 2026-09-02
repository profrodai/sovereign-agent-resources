# ==============================================================================
# Sovereign Agent Resources — root orchestration
# ==============================================================================
# Single source of truth for the pins: ./SOVEREIGN_AGENT_VERSION and
# ./ZEOCORE_VERSION. Never hand-edit them — `make migrate` is the only writer.
# Per-project day-to-day targets live in each resource's own directory.
# ==============================================================================

PYTHON  ?= python3
ROOT    := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
SCRIPTS := $(ROOT)/scripts

# make migrate PACKAGE=sovereign-agent VERSION=1.1.1
PACKAGE ?= sovereign-agent
VERSION ?=
# KEEP_GOING=1 continues after a project failure and reports them all.
KEEP_GOING ?= 0
# STRICT=1 promotes lint warnings to failures (CI uses this).
STRICT ?= 0

LIST    := $(PYTHON) $(SCRIPTS)/list_projects.py
MIGRATE := $(PYTHON) $(SCRIPTS)/migrate_catalog.py
CHECK   := $(PYTHON) $(SCRIPTS)/check_project.py
LINT    := $(PYTHON) $(SCRIPTS)/lint_repo.py
STRICT_ARGS := $(if $(filter 1,$(STRICT)),--strict,)

PROJECTS := $(shell $(LIST) --paths-only 2>/dev/null)

.DEFAULT_GOAL := help
.PHONY: help list status outdated latest migrate migrate-dry update \
        validate verify-fast verify lint test-scripts new-resource \
        lock-all install-all check-all ci

help: ## Show this help
	@echo ''
	@echo 'Sovereign Agent Resources — runnable examples, tutorials, and patterns'
	@echo ''
	@echo "  Pinned to:  sovereign-agent==$$(cat $(ROOT)/SOVEREIGN_AGENT_VERSION)   zeocore==$$(cat $(ROOT)/ZEOCORE_VERSION)"
	@echo "  Projects:   $(words $(PROJECTS)) maintained"
	@echo ''
	@echo '  Keeping the catalog current (in order):'
	@echo '    1. make outdated     Ask PyPI what is new. Read-only.'
	@echo '    2. make update       Bump both pins to newest, rewrite everything, re-lock.'
	@echo '    3. make ci           Install every project for real and validate it.'
	@echo ''
	@echo '  Version & migration:'
	@echo '    make list            Every project and its pins vs the root pins'
	@echo '    make status          Exit non-zero if any project drifted'
	@echo '    make outdated        Current vs newest on PyPI, per package'
	@echo '    make latest          Bump PACKAGE to newest on PyPI'
	@echo '    make migrate PACKAGE=p VERSION=x    Bump to x (refused if x is not on PyPI)'
	@echo '    make migrate-dry PACKAGE=p VERSION=x  Preview; writes nothing'
	@echo ''
	@echo '  Validate (cheapest first):'
	@echo '    make validate        Offline gate: tooling tests + lint + drift (~seconds)'
	@echo '    make ci              validate + install & check every project (needs uv)'
	@echo ''
	@echo '  Switches: KEEP_GOING=1 (report all failures)  STRICT=1 (warnings fail)'
	@echo ''
	@echo '  Never hand-edit SOVEREIGN_AGENT_VERSION or ZEOCORE_VERSION.'

list: ## Show every project and its pins
	@$(LIST)

status: ## Exit non-zero if any maintained project drifted from the root pins
	@$(LIST) --status

outdated: ## Report current vs newest on PyPI for every governed package
	@$(MIGRATE) --package sovereign-agent --outdated
	@$(MIGRATE) --package zeocore --outdated

latest: ## Bump PACKAGE to the newest release on PyPI
	@$(MIGRATE) --package $(PACKAGE) --latest
	@$(MAKE) --no-print-directory lock-all

migrate: ## Bump PACKAGE to VERSION (refuses a version that is not on PyPI)
	@test -n "$(VERSION)" || { echo "usage: make migrate PACKAGE=sovereign-agent VERSION=1.1.1"; exit 2; }
	@$(MIGRATE) --package $(PACKAGE) --version $(VERSION)
	@$(MAKE) --no-print-directory lock-all

migrate-dry: ## Preview a bump; writes nothing
	@test -n "$(VERSION)" || { echo "usage: make migrate-dry PACKAGE=sovereign-agent VERSION=1.1.1"; exit 2; }
	@$(MIGRATE) --package $(PACKAGE) --version $(VERSION) --dry

update: ## The routine bump: newest of both packages, then validate
	@$(MIGRATE) --package sovereign-agent --latest
	@$(MIGRATE) --package zeocore --latest
	@$(MAKE) --no-print-directory lock-all
	@$(MAKE) --no-print-directory validate

new-resource: ## Scaffold a resource: make new-resource CATEGORY=patterns NAME=my-resource
	@test -n "$(CATEGORY)" -a -n "$(NAME)" || { echo "usage: make new-resource CATEGORY=patterns NAME=my-resource"; exit 2; }
	@$(PYTHON) $(SCRIPTS)/new_resource.py --category $(CATEGORY) --name $(NAME)

lint: ## Static checks only (--json via scripts/lint_repo.py)
	@$(LINT) $(STRICT_ARGS)

test-scripts: ## Unit-test the tooling
	@$(PYTHON) $(SCRIPTS)/test_tooling.py

validate: ## Offline gate: tooling tests + lint + drift. No network, no uv.
	@$(MAKE) --no-print-directory test-scripts
	@$(MAKE) --no-print-directory lint
	@$(MAKE) --no-print-directory status
	@echo "validate: catalog sound"

verify-fast: validate ## Fast-lane alias for the fleet gate

verify: validate ## Full gate: validate + install & check every project
	@$(MAKE) --no-print-directory check-all

lock-all: ## uv lock in every maintained project
	@set -e; for p in $(PROJECTS); do \
		echo "== uv lock: $$p"; \
		(cd $(ROOT)/$$p && uv lock) || { [ "$(KEEP_GOING)" = "1" ] || exit 1; }; \
	done

install-all: ## uv sync in every maintained project
	@set -e; for p in $(PROJECTS); do \
		echo "== uv sync: $$p"; \
		(cd $(ROOT)/$$p && uv sync) || { [ "$(KEEP_GOING)" = "1" ] || exit 1; }; \
	done

check-all: ## Install each project and assert the pins actually resolved
	@set -e; fails=0; for p in $(PROJECTS); do \
		echo "== check: $$p"; \
		$(CHECK) $$p || { fails=1; [ "$(KEEP_GOING)" = "1" ] || exit 1; }; \
	done; exit $$fails

ci: validate check-all ## What the scheduled CI runs
	@echo "ci: all projects installed and checked"
