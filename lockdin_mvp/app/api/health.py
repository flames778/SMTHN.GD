"""Health, readiness, dependency, and version endpoints."""

from __future__ import annotations

import importlib.metadata
import time
from typing import Literal

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

router = APIRouter(tags=["health"])

# Track application start time for uptime reporting
_start_time = time.time()


class DependencyStatus(BaseModel):
    name: str
    status: Literal["ok", "degraded", "down"]
    latency_ms: float | None = None
    detail: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    dependencies: list[DependencyStatus]


class DependenciesResponse(BaseModel):
    dependencies: list[DependencyStatus]


class VersionResponse(BaseModel):
    version: str
    environment: str
    uptime_seconds: float


def _check_database() -> DependencyStatus:
    """Check database connectivity and latency (lazy import to avoid startup errors)."""
    from app.db.session import SessionLocal  # noqa: PLC0415

    t0 = time.perf_counter()
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - t0) * 1000
        return DependencyStatus(name="database", status="ok", latency_ms=round(latency_ms, 2))
    except Exception as exc:
        latency_ms = (time.perf_counter() - t0) * 1000
        return DependencyStatus(
            name="database",
            status="down",
            latency_ms=round(latency_ms, 2),
            detail=str(exc),
        )


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health() -> HealthResponse:
    """Liveness probe: returns 200 if process is alive.

    Use for load balancer or container liveness checks.
    This endpoint does NOT check dependencies - it only confirms the process is running.
    """
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    responses={503: {"description": "Service not ready"}},
)
def readiness() -> JSONResponse:
    """Readiness probe: returns 200 if all dependencies are healthy.

    Use for Kubernetes readiness gate or deployment health checks.
    Returns 503 if any critical dependency is unavailable.
    """
    db_status = _check_database()
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
    """Dependency probe: returns status and latency for all external dependencies.

    Use for monitoring dashboards and alerting.
    Always returns 200 regardless of dependency health - check individual statuses.
    """
    db_status = _check_database()
    all_deps = [db_status]

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "dependencies": [dep.model_dump(exclude_none=True) for dep in all_deps],
        },
    )


@router.get("/version", response_model=VersionResponse, status_code=status.HTTP_200_OK)
def version() -> VersionResponse:
    """Version endpoint: returns application version, environment, and uptime.

    Use for deployment verification and monitoring.
    """
    from app.core.config import get_settings  # noqa: PLC0415

    settings = get_settings()
    uptime = round(time.time() - _start_time, 2)

    try:
        app_version = importlib.metadata.version("lockdin-mvp")
    except importlib.metadata.PackageNotFoundError:
        app_version = "0.1.0"

    return VersionResponse(
        version=app_version,
        environment=settings.app_env,
        uptime_seconds=uptime,
    )
