.PHONY: up down migrate test reseed clean

up:
	docker compose up -d --build

down:
	docker compose down

migrate:
	docker compose exec api alembic upgrade head

test:
	docker compose exec api pytest /app/tests

reseed:
	@echo "Reseed target stub for Phase 0 (will truncate and seed in Phase 1)"

clean:
	docker compose down -v

