from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tripbuddy_core import __version__ as core_version
from tripbuddy_core.config import settings
from app.routes.listings import router as listings_router
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.bookings import router as bookings_router
from app.routes.messages import router as messages_router

app = FastAPI(title="TripBuddy API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(listings_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(bookings_router)
app.include_router(messages_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "api",
        "core_version": core_version,
        "database_configured": bool(settings.DATABASE_URL),
        "mcp_server_url": settings.MCP_SERVER_URL,
    }

