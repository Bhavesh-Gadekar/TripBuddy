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

## Demo Credentials (Deterministic Fictional Users)

| Name | Email | Fictional Verified ID | Role |
|------|-------|------------------------|------|
| Alex Mercer | `alex.mercer@tripbuddy.test` | `ID-7F3A91-DEMO` | Demo Guest |
| Samantha Chen | `samantha.chen@tripbuddy.test` | `ID-4B8C12-DEMO` | Demo Guest |
| Rohan Deshmukh | `rohan.deshmukh@tripbuddy.test` | `ID-9E2D55-DEMO` | Demo Guest |
| Meera Joshi | `meera.joshi@hosts.tripbuddy.test` | `ID-HOST-01-VERIFIED` | Superhost (Goa) |

All demo passwords default to `password123` for local development and testing.

## Makefile Commands

- `make up` - Build and start all 4 containers in background
- `make down` - Stop and remove containers
- `make migrate` - Run Alembic database migrations
- `make test` - Run full automated test suite inside the API container
- `make reseed` - Idempotently truncate and reseed 22 listings across 5 cities, 9 hosts, 3 demo users, and realistic reviews

