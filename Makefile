.PHONY: help install dev-install test lint format run clean

help:
	@echo "CamperLog — Verfügbare Kommandos:"
	@echo "  make install       — Installiere Dependencies"
	@echo "  make dev-install   — Installiere Dev-Dependencies"
	@echo "  make test          — Führe Tests aus"
	@echo "  make lint          — Code-Qualitätsprüfung"
	@echo "  make format        — Auto-Format mit Black"
	@echo "  make run           — Starte camperlog --help"
	@echo "  make clean         — Cleanup (__pycache__, .pytest_cache, etc.)"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

test:
	pytest -v

lint:
	black --check src/ tests/
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/

run:
	python -m camperlog.cli --help

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf .mypy_cache
