.PHONY: build start rebuild test check fixtures load-fixtures

UV ?= uv

build:
	docker compose build

start:
	docker compose up -d

rebuild:
	docker compose up -d --build

test:
	$(UV) run pytest -q

fixtures load-fixtures:
	$(UV) run python -m src.infrastructure.fixtures

check:
	$(UV) run ruff check .
	$(UV) run mypy src
	$(UV) run pytest -q
