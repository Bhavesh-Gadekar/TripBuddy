from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP
from tripbuddy_core import __version__ as core_version
from tripbuddy_core.config import settings

mcp = FastMCP("TripBuddy MCP Server")


@mcp.tool()
def health_check_tool() -> str:
    """Check health of TripBuddy MCP Tool Server."""
    return f"TripBuddy MCP Tool Server is healthy. Core version: {core_version}"


# We also expose HTTP endpoints for health monitoring and MCP SSE/HTTP transport
app = FastAPI(title="TripBuddy MCP Service", version="0.1.0")

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
        "service": "mcp_server",
        "core_version": core_version,
        "database_configured": bool(settings.DATABASE_URL),
    }


@app.get("/mcp")
def mcp_root():
    return {
        "status": "ok",
        "protocol": "mcp",
        "tools": ["search_listings", "read_reviews", "get_profile", "message_host", "book_listing", "health_check_tool"],
    }

