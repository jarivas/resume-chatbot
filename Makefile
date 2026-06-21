.PHONY: help install lint test run clean

# Define la ruta al binario usando 'poetry run which'
DATAMODEL_GEN := $(shell poetry run which datamodel-code-generator)

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Instala dependencias y configura el entorno
	poetry install

lint: ## Ejecuta Ruff y Mypy para validar la calidad del código
	poetry run ruff check app/ tests/
	poetry run mypy app/

test: ## Ejecuta la suite de pruebas
	poetry run pytest tests/ --cov=app

run: ## Ejecuta la API en modo desarrollo
	poetry run uvicorn app.main:app --reload

quality: lint test ## Ejecuta todo el pipeline de calidad (lint + test)
	@echo "Pipeline de calidad completado exitosamente."

# Puedes añadir esto al workflow de calidad para que siempre esté al día
quality: update-models lint test