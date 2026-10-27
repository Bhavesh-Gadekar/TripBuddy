from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tripbuddy_core import __version__ as core_version
from tripbuddy_core.config import settings

app = FastAPI(title="TripBuddy API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "api",
        "core_version": core_version,
        "database_configured": bool(settings.DATABASE_URL),
        "mcp_server_url": settings.MCP_SERVER_URL,
    }

