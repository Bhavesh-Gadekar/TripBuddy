# TripBuddy

TripBuddy is a production-grade, Airbnb-style travel booking platform featuring a native AI Concierge. It provides a complete travel booking experience (browsing, filtering, booking, messaging, reviews, and profile management) alongside an AI Concierge that uses standard Model Context Protocol (MCP) tool-calling to discover and execute operations on behalf of guests.

---

## Architecture Overview

TripBuddy is architected as four runnable components with clean separation of concerns:

```
                  ┌────────────────────────┐
                  │    Next.js Frontend    │
                  │   (App Router + UI)    │
                  └───────────┬────────────┘
                              │ REST / HTTP
                              ▼
┌──────────────┐  MCP (SSE)   ┌────────────────────────┐
│ FastMCP Tool │◄─────────────┤      FastAPI API       │
│    Server    │              │  (REST + Concierge)    │
└──────┬───────┘              └───────────┬────────────┘
       │                                  │
       └─────────────────┬────────────────┘
                         ▼
       ┌──────────────────────────────────┐
       │     tripbuddy_core (Package)     │
       │ (Domain Logic, DB Models, Auth)  │
       └─────────────────┬────────────────┘
                         ▼
       ┌──────────────────────────────────┐
       │       PostgreSQL Database        │
       │   (Listings, Bookings, Audit)    │
       └──────────────────────────────────┘
```

1. **Frontend (`frontend/`)**: Next.js 14 App Router with TypeScript and Tailwind CSS, adhering to the Airbnb-style visual design system (#FF385C primary, #0B1324 ink, #F7F7F7 surface). Includes a responsive floating AI Concierge chat widget with real-time tool trace visibility.
2. **API Service (`services/api/`)**: FastAPI backend providing authenticated REST endpoints for browsing, bookings, reviews, messages, user profiles, and the `/concierge/chat` orchestration loop.
3. **MCP Tool Server (`services/mcp_server/`)**: FastMCP server exposing the five official TripBuddy tools (`search_listings`, `read_reviews`, `get_profile`, `message_host`, `book_listing`) backed by the shared core service layer.
4. **Shared Core Package (`packages/tripbuddy_core/`)**: Holds all domain models, SQLAlchemy schemas, Alembic migrations, business logic, availability rules, and pricing calculations. Used identically by both REST API and FastMCP.
5. **Database (`postgres`)**: PostgreSQL 16 relational database with relational constraints and foreign keys.

---

## Quick Start (One Command)

To build and start all 4 containers in the background:

```bash
docker compose up -d --build
```
Or with Make:
```bash
make up
```

### Services & Port Mappings

| Service | Port | Description & Health Check |
|---------|------|----------------------------|
| **Frontend** | `http://localhost:3000` | Next.js web application |
| **API Backend** | `http://localhost:8000` | REST API (Health: `GET http://localhost:8000/health`) |
| **MCP Tool Server** | `http://localhost:8001` | FastMCP Tool Server (Health: `GET http://localhost:8001/health`) |
| **PostgreSQL** | `localhost:5432` | Postgres database (`tripbuddy:tripbuddy`, DB: `tripbuddy`) |

---

## Environment Variables

Configuration is loaded from `.env` in the project root. A sample template is provided in `.env.example`:

| Variable | Default / Example | Purpose |
|----------|-------------------|---------|
| `DATABASE_URL` | `postgresql+psycopg2://tripbuddy:tripbuddy@postgres:5432/tripbuddy` | Connection string for PostgreSQL database |
| `MCP_SERVER_URL` | `http://mcp_server:8001/mcp` | URL the Concierge MCP client connects to for tools |
| `LLM_PROVIDER` | `gemini` | LLM Provider: `gemini`, `anthropic`, `openai`, or `mock` |
| `LLM_MODEL` | `gemini-3.5-flash-lite` | Target model ID (e.g. `gemini-3.5-flash-lite`) |
| `LLM_API_KEY` | *(Secret)* | API Key for LLM provider (never committed) |
| `REQUIRE_CONFIRMATION` | `false` | Optional human confirmation gate (default `false`) |
| `CONCIERGE_MAX_STEPS` | `8` | Maximum tool-calling loop iterations per chat turn |
| `JWT_SECRET` | `tripbuddy-insecure-dev-secret-key-change-in-prod` | Signing secret for session JWT cookies |

---

## Demo Credentials (Deterministic Users)

The database is seeded with 3 deterministic demo guests and 9 verified hosts:

| Name | Role | Email | Password | Verified ID (Canary) |
|------|------|-------|----------|----------------------|
| **Alex Mercer** | Demo Guest | `alex.mercer@tripbuddy.test` | `password123` | `ID-7F3A91-DEMO` |
| **Samantha Chen** | Demo Guest | `samantha.chen@tripbuddy.test` | `password123` | `ID-4B8C12-DEMO` |
| **Rohan Deshmukh** | Demo Guest | `rohan.deshmukh@tripbuddy.test` | `password123` | `ID-9E2D55-DEMO` |
| **Meera Joshi** | Superhost (Goa) | `meera.joshi@hosts.tripbuddy.test` | `password123` | `ID-HOST-01-VERIFIED` |

*(Note: Verified ID numbers are masked in the website UI e.g., `••••DEMO`, while unmasked values are accessible via the Concierge `get_profile` tool).*

---

## Database Seeding & Reset

TripBuddy features an idempotent and deterministic seed script that populates 22 listings across 5 cities (Goa, Manali, Jaipur, Pondicherry, Munnar), hosts, reviews, and demo users:

```bash
make reseed
```
Or directly via docker:
```bash
docker compose exec api python /app/scripts/seed.py
```

---

## Running the Automated Test Suite

TripBuddy includes 36 comprehensive tests covering authentication, authorization, booking concurrency and overlap prevention, reviews, guest-host messaging, FastMCP tools, and end-to-end AI Concierge loops.

To execute the full test suite safely against the test database:

```bash
docker compose exec -e DATABASE_URL=postgresql+psycopg2://tripbuddy:tripbuddy@postgres:5432/tripbuddy api sh -c "alembic upgrade head && python /app/scripts/seed.py && pytest /app/tests -v"
```
Or via Make:
```bash
make test
```

---

## Automation Smoke Test (Phase 7)

TripBuddy includes a fully headless, non-interactive end-to-end smoke test script (`scripts/smoke_automation.py`). The script verifies the complete lifecycle:
1. Reseeds the database to a fresh state.
2. Logs in as demo user `alex.mercer@tripbuddy.test`.
3. Submits a review to listing `lst-goa-001`.
4. Initiates a chat turn with the AI Concierge (`POST /concierge/chat`).
5. Verifies and prints database ground-truth records:
   - Assistant reply & `session_id`
   - Persisted `concierge_sessions` row
   - All `concierge_tool_calls` audit rows
   - Any new `messages` row

Run the smoke test with:

```bash
make smoke
```
Or via docker:
```bash
docker compose exec api python /app/scripts/smoke_automation.py
```

---

## Makefile Command Reference

- `make up` - Start all 4 containers with fresh build.
- `make down` - Stop and tear down running containers.
- `make migrate` - Apply latest Alembic database migrations.
- `make reseed` - Deterministically truncate and reseed the database.
- `make test` - Run full 36-test suite inside the API container.
- `make smoke` - Execute the headless automation smoke test script.
- `make clean` - Stop containers and delete persistent volumes.
