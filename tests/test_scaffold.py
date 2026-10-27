import sys
import os

# Ensure package paths are discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "tripbuddy_core")))
sys.path.insert(0, "/packages/tripbuddy_core")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "services", "api")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "services", "mcp_server")))
sys.path.insert(0, "/app")


def test_shared_core_package_import():
    """Verify that tripbuddy_core can be imported and supplies config, errors, and db base."""
    import tripbuddy_core
    from tripbuddy_core.config import settings
    from tripbuddy_core.errors import TripBuddyError, DatesUnavailableError
    from tripbuddy_core.db import Base

    assert tripbuddy_core.__version__ == "0.1.0"
    assert settings.CONCIERGE_MAX_STEPS == 8
    assert settings.REQUIRE_CONFIRMATION is False
    assert issubclass(DatesUnavailableError, TripBuddyError)
    assert Base is not None


def test_api_imports_core_package():
    """Verify that the API service imports and uses the shared tripbuddy_core package."""
    try:
        from services.api.app.main import app, health_check
    except ModuleNotFoundError:
        from app.main import app, health_check
    res = health_check()
    assert res["status"] == "healthy"
    assert res["service"] == "api"
    assert res["core_version"] == "0.1.0"


def test_mcp_server_imports_core_package():
    """Verify that the MCP server imports and uses the shared tripbuddy_core package."""
    # When running on host or mcp container
    try:
        from services.mcp_server.app.server import app, health_check
        res = health_check()
        assert res["status"] == "healthy"
        assert res["service"] == "mcp_server"
        assert res["core_version"] == "0.1.0"
    except ModuleNotFoundError:
        # In the API container, query the MCP server endpoint over the network
        import httpx
        from tripbuddy_core.config import settings

        # health endpoint on mcp service
        base_url = settings.MCP_SERVER_URL.rsplit("/mcp", 1)[0]
        response = httpx.get(f"{base_url}/health")
        assert response.status_code == 200
        res = response.json()
        assert res["status"] == "healthy"
        assert res["service"] == "mcp_server"
        assert res["core_version"] == "0.1.0"


