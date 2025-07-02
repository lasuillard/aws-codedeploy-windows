#!/usr/bin/env --split-string make --makefile

MAKEFLAGS += --warn-undefined-variable --no-builtin-rules --silent
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:
.SUFFIXES:

SHELL := bash
.ONESHELL:
.SHELLFLAGS := -o errexit -o nounset -o pipefail -c


help: Makefile  ## Show this help message
	@grep -E '(^[a-zA-Z_-]+:.*?##.*$$)|(^##)' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[32m%-30s\033[0m %s\n", $$1, $$2}' | sed -e 's/\[32m##/[33m/'


# =============================================================================
# Common
# =============================================================================
init:  ## Initialize the project workspace
	pre-commit install --install-hooks
	cp --no-clobber .env.example .env
	cp --no-clobber .devcontainer/.env.example .devcontainer/.env
.PHONY: init

install:  ## Install deps
	uv python install
	uv sync --frozen
.PHONY: install

update:  ## Update deps and tools
	pre-commit autoupdate
	uv sync --upgrade
.PHONY: update

run:  ## Run application
	dotenvx run uv run python ./main.py
.PHONY: run


# =============================================================================
# CI
# =============================================================================
ci: lint test  ## Run CI tasks
.PHONY: ci

format:  ## Run autoformatters
	uv run ruff check --fix .
	uv run ruff format .
.PHONY: format

lint:  ## Run code linters
	uv run ruff check .
	uv run ty check .
.PHONY: lint

test:  ## Run tests
	uv run pytest
.PHONY: test


# =============================================================================
# Utility
# =============================================================================
clean:  ## Clean up the project workspace, removing caches and temporary files
	rm -rf .mypy_cache/ .pytest_cache/ .ruff_cache/ htmlcov/ .coverage coverage.xml report.xml
	find . -path '*/__pycache__*' -or -path '*.log*' -delete
.PHONY: clean
