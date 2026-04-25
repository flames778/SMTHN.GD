from fastapi import FastAPI

from app.core.config import get_settings

app = FastAPI(title="Lockd'In MVP API", version="0.1.0")


@app.on_event("startup")
def validate_configuration() -> None:
    settings = get_settings()
    settings.validate_startup_config()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
