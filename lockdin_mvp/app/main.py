from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from lockdin_backend.api.session_routes import router as session_router
from starlette.middleware.cors import CORSMiddleware

from app.api.consent import router as consent_router
from app.api.health import router as health_router
from app.api.integrations import router as integrations_router
from app.api.problem_details_handlers import register_problem_details_handlers
from app.core.config import get_settings
from app.core.logging import CorrelationIdMiddleware
from app.security.cors import get_cors_config
from app.security.idempotency import IdempotencyMiddleware
from app.security.request_boundaries import (
    RateLimitMiddleware,
    RequestSizeLimitMiddleware,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.validate_startup_config()
    yield


app = FastAPI(title="Lockd'In MVP API", version="0.1.0", lifespan=lifespan)

# Request boundary protections (must be added first for correct middleware order)
# CORS must be added first to handle preflight requests
cors_config = get_cors_config(get_settings().app_env)
app.add_middleware(CORSMiddleware, **cors_config)

# Security middleware
app.add_middleware(RequestSizeLimitMiddleware, max_size_bytes=10 * 1024 * 1024)
app.add_middleware(RateLimitMiddleware, max_requests=1000, window_seconds=60)
# Note: TrustedHostMiddleware disabled by default (pass trusted_hosts=[] to enable with custom list)

# Idempotency: replay duplicate mutation responses within 24h
app.add_middleware(IdempotencyMiddleware)

# Correlation ID middleware for request tracing
app.add_middleware(CorrelationIdMiddleware)

# Register RFC 9457 Problem Details exception handlers
register_problem_details_handlers(app)

app.include_router(health_router)
app.include_router(integrations_router)
app.include_router(consent_router)
app.include_router(session_router)
