# TripBuddy

TripBuddy is an Airbnb-style travel booking platform with a native AI Concierge.

## Quick Start (One Command)

To build and run all 4 services (PostgreSQL, FastAPI Backend, FastMCP Tool Server, Next.js Frontend):

```bash
docker compose up -d --build
```
Or using make:
```bash
make up
```

## Services & Ports

- **Frontend (Next.js App Router)**: [http://localhost:3000](http://localhost:3000)
- **API Backend (FastAPI)**: [http://localhost:8000](http://localhost:8000) (Health: `GET /health`)
- **MCP Tool Server (FastMCP)**: [http://localhost:8001](http://localhost:8001) (Health: `GET /health`, Info: `GET /mcp`)
- **PostgreSQL Database**: `localhost:5432` (`tripbuddy:tripbuddy`, db: `tripbuddy`)

## Architecture & Layout

- `packages/tripbuddy_core`: Shared domain logic, configurations, db sessions, and error models.
- `services/api`: FastAPI REST API for frontend and concierge chat endpoint.
- `services/mcp_server`: FastMCP server exposing the 5 tools for the AI Concierge.
- `frontend`: Next.js 14 App Router with Tailwind CSS Airbnb-styled design system.

## Makefile Commands

- `make up` - Build and start all 4 containers in background
- `make down` - Stop and remove containers
- `make migrate` - Run Alembic database migrations
- `make test` - Run test suite
- `make reseed` - Reseed database deterministically (Phase 1)

