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
	docker compose exec api python /app/scripts/seed.py

clean:
	docker compose down -v

