"""CORS configuration for backend application."""

from __future__ import annotations


def get_cors_config(env: str = "development") -> dict:
    """Get CORS configuration based on environment.

    Args:
        env: Environment name (development, staging, production).

    Returns:
        Dictionary with CORS middleware parameters.
    """
    if env == "production":
        # Production: only app origin
        return {
            "allow_origins": ["https://app.lockdin.ai"],
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "X-Correlation-ID",
                "X-Lockdin-Session-Token",
            ],
            "max_age": 86400,  # 24 hours
        }
    elif env == "staging":
        # Staging: allow staging domain
        return {
            "allow_origins": ["https://app-staging.lockdin.ai"],
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "X-Correlation-ID",
                "X-Lockdin-Session-Token",
            ],
            "max_age": 86400,
        }
    else:
        # Development: allow local development servers
        return {
            "allow_origins": [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:8000",
                "http://localhost:8001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:8000",
                "http://127.0.0.1:8001",
            ],
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "X-Correlation-ID",
                "X-Lockdin-Session-Token",
            ],
            "max_age": 3600,  # 1 hour for dev
        }
