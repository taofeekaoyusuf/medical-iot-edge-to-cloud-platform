"""Process health only: domain handlers are intentionally absent at Stage 3."""

import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

SERVICE_NAMES = frozenset({"gateway", "registry", "processor", "health", "notifications", "api"})


def create_app(service_name: str | None = None) -> FastAPI:
    """Select a named scaffold without claiming its domain service is ready."""
    name = service_name if service_name is not None else os.getenv("MEDICAL_IOT_SERVICE", "api")
    if name not in SERVICE_NAMES:
        raise ValueError(f"Unknown service: {name!r}")
    app = FastAPI(title=f"Medical IoT {name}", docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"service": name, "status": "alive"}

    @app.get("/health/ready")
    async def ready() -> JSONResponse:
        # A live scaffold must not receive production traffic before its dependencies exist.
        return JSONResponse(
            status_code=503,
            content={
                "service": name,
                "status": "not_ready",
                "reason": "domain_service_not_implemented",
            },
        )

    return app
