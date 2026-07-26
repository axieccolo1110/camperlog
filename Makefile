.PHONY: help install dev-install test lint format run serve serve-prod clean check

help:
	@echo "CamperLog — Verfügbare Kommandos:"
	@echo "  make install       — Installiere Dependencies"
	@echo "  make dev-install   — Installiere Dev-Dependencies"
	@echo "  make test          — Führe Tests aus"
	@echo "  make lint          — Code-Qualitätsprüfung"
	@echo "  make format        — Auto-Format mit Black"
	@echo "  make run           — Starte camperlog --help"
	@echo "  make serve         — Starte Web-Server lokal (SQLite, --reload)
  make serve-prod    — Starte Web-Server mit Railway PostgreSQL (DATABASE_URL nötig)"
	@echo "  make clean         — Cleanup (__pycache__, .pytest_cache, etc.)"
	@echo "  make check         — Alle Checks (lint + test)"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

test:
	pytest -v

lint:
	black --check src/ tests/
	flake8 src/ tests/ --max-line-length=88
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/

run:
	python -m camperlog.cli --help

serve:
	camperlog serve --reload

serve-prod:
	@test -n "$$DATABASE_URL" || (echo "Fehler: DATABASE_URL ist nicht gesetzt." && exit 1)
	DATABASE_URL="$$DATABASE_URL" camperlog serve

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf .mypy_cache

check: lint test
