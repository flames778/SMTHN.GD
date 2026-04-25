from fastapi import FastAPI

from app.api.consent import router as consent_router
from app.api.integrations import router as integrations_router
from app.core.config import get_settings

app = FastAPI(title="Lockd'In MVP API", version="0.1.0")
app.include_router(integrations_router)
app.include_router(consent_router)


@app.on_event("startup")
def validate_configuration() -> None:
    settings = get_settings()
    settings.validate_startup_config()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
