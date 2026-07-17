"""Health, readiness, dependency, and version endpoints for backend."""

from __future__ import annotations

import time
from typing import Literal

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

router = APIRouter(tags=["health"])

_start_time = time.time()


class DependencyStatus(BaseModel):
    name: str
    status: Literal["ok", "degraded", "down"]
    latency_ms: float | None = None
    detail: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"]


class VersionResponse(BaseModel):
    version: str
    environment: str
    uptime_seconds: float


def _check_identity_db() -> DependencyStatus:
    """Check identity database connectivity."""
    from lockdin_backend.persistence.database import get_session_factory

    t0 = time.perf_counter()
    try:
        factory = get_session_factory()
        with factory() as db:
            db.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - t0) * 1000
        return DependencyStatus(
            name="identity_database", status="ok", latency_ms=round(latency_ms, 2)
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - t0) * 1000
        return DependencyStatus(
            name="identity_database",
            status="down",
            latency_ms=round(latency_ms, 2),
            detail=str(exc),
        )


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health() -> HealthResponse:
    """Liveness probe: returns 200 if process is alive."""
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    responses={503: {"description": "Service not ready"}},
)
def readiness() -> JSONResponse:
    """Readiness probe: returns 200 if all critical dependencies are healthy."""
    db_status = _check_identity_db()
    all_deps = [db_status]
    is_ready = all(dep.status == "ok" for dep in all_deps)
    http_status = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=http_status,
        content={
            "status": "ready" if is_ready else "not_ready",
            "dependencies": [dep.model_dump(exclude_none=True) for dep in all_deps],
        },
    )


@router.get("/dependencies", status_code=status.HTTP_200_OK)
def dependency_status() -> JSONResponse:
    """Dependency probe: status and latency for all external dependencies."""
    db_status = _check_identity_db()
    all_deps = [db_status]

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "dependencies": [dep.model_dump(exclude_none=True) for dep in all_deps],
        },
    )


@router.get("/version", response_model=VersionResponse, status_code=status.HTTP_200_OK)
def version() -> VersionResponse:
    """Version endpoint: application version, environment, and uptime."""
    import importlib.metadata
    import os

    uptime = round(time.time() - _start_time, 2)

    try:
        app_version = importlib.metadata.version("lockdin-backend")
    except importlib.metadata.PackageNotFoundError:
        app_version = "0.1.0"

    return VersionResponse(
        version=app_version,
        environment=os.getenv("APP_ENV", "dev"),
        uptime_seconds=uptime,
    )
