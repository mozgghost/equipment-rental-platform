SHELL := /bin/sh

.PHONY: up down logs migrate test lint frontend-install frontend-build seed
up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

migrate:
	docker compose exec backend python manage.py migrate

test:
	cd backend && python -m pytest tests -q

lint:
	python -m ruff check backend

frontend-install:
	cd frontend && npm install

frontend-build:
	cd frontend && npm run build

seed:
	docker compose exec backend python manage.py seed_demo_data --seed 20261026 --allow-sandbox
