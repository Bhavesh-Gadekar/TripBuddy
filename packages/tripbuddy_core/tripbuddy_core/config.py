import os
from pydantic import BaseModel


class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://tripbuddy:tripbuddy@postgres:5432/tripbuddy")
    MCP_SERVER_URL: str = os.getenv("MCP_SERVER_URL", "http://mcp_server:8001/mcp")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-3.5-flash")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    REQUIRE_CONFIRMATION: bool = os.getenv("REQUIRE_CONFIRMATION", "false").lower() in ("true", "1", "yes")
    CONCIERGE_MAX_STEPS: int = int(os.getenv("CONCIERGE_MAX_STEPS", "8"))
    JWT_SECRET: str = os.getenv("JWT_SECRET", "fictional-demo-jwt-secret-not-for-production")


settings = Settings()

