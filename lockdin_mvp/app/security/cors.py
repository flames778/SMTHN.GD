"""CORS configuration for MVP application."""

from __future__ import annotations


def get_cors_config(env: str = "development") -> dict:
    """Get CORS configuration based on environment.

    Args:
        env: Environment name (development, staging, production).

    Returns:
        Dictionary with CORS middleware parameters.
    """
    if env == "production":
        # Production: strict origin whitelist
        return {
            "allow_origins": [
                "https://app.lockdin.ai",
                "https://www.lockdin.ai",
            ],
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
        # Staging: allow staging domains
        return {
            "allow_origins": [
                "https://app-staging.lockdin.ai",
                "https://staging.lockdin.ai",
            ],
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
        # Development: allow localhost and common dev ports
        return {
            "allow_origins": [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:8000",
                "http://localhost:8001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
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
