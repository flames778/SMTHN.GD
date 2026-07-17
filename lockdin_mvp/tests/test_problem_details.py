"""Tests for RFC 9457 Problem Details responses."""

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from app.api.problem_details_handlers import (
    ProblemDetailsException,
    register_problem_details_handlers,
)
from app.schemas.problem_details import ProblemDetails, problem_details


class TestProblemDetailsModel:
    """Test ProblemDetails model."""

    def test_problem_details_with_all_fields(self):
        """Test ProblemDetails with all fields."""
        pd = ProblemDetails(
            type="https://api.lockdin.ai/errors/oauth-state-invalid",
            status=400,
            title="Invalid OAuth State",
            detail="OAuth state token expired",
            instance="/api/integrations/google/callback",
            error_code="OAUTH_STATE_INVALID",
            correlation_id="req-123",
        )
        assert pd.status == 400
        assert pd.error_code == "OAUTH_STATE_INVALID"

    def test_problem_details_to_dict_excludes_none(self):
        """Test to_dict excludes None values."""
        pd = ProblemDetails(
            status=404,
            title="Not Found",
            detail=None,
            instance=None,
        )
        d = pd.to_dict()
        assert "detail" not in d
        assert "instance" not in d
        assert d["status"] == 404

    def test_problem_details_factory_function(self):
        """Test problem_details factory function."""
        pd = problem_details(
            "OAUTH_STATE_INVALID",
            detail="Token expired",
        )
        assert pd.error_code == "OAUTH_STATE_INVALID"
        assert pd.status == 400
        assert "oauth-state-invalid" in pd.type.lower()

    def test_problem_details_factory_unknown_error_code(self):
        """Test factory with unknown error code."""
        pd = problem_details("UNKNOWN_CODE", status=500)
        assert pd.error_code == "UNKNOWN_CODE"
        assert pd.status == 500
        assert pd.title == "Unknown Error"


class TestProblemDetailsExceptionHandler:
    """Test exception handlers."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app."""
        app = FastAPI()
        register_problem_details_handlers(app)

        @app.get("/oauth-invalid")
        def oauth_invalid():
            raise HTTPException(
                status_code=400,
                detail=problem_details(
                    error_code="OAUTH_STATE_INVALID",
                    detail="State expired",
                ).to_dict(),
            )

        @app.get("/not-found")
        def not_found():
            raise HTTPException(
                status_code=404,
                detail="Resource not found",
            )

        @app.get("/problem-details-exc")
        def problem_exc():
            raise ProblemDetailsException(
                problem_details(
                    "INTERNAL_SERVER_ERROR",
                    status=500,
                    detail="Something went wrong",
                )
            )

        return app

    def test_http_exception_with_problem_details_dict(self, app):
        """Test HTTPException with pre-formatted problem_details dict."""
        client = TestClient(app)
        response = client.get("/oauth-invalid")
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "OAUTH_STATE_INVALID"
        assert data["detail"] == "State expired"
        assert "oauth-state-invalid" in data["type"]

    def test_http_exception_plain_detail(self, app):
        """Test HTTPException with plain string detail."""
        client = TestClient(app)
        response = client.get("/not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == 404
        assert data["title"] == "Not Found"
        assert data["detail"] == "Resource not found"
        assert "not-found" in data["type"]

    def test_problem_details_exception(self, app):
        """Test ProblemDetailsException handler."""
        client = TestClient(app)
        response = client.get("/problem-details-exc")
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INTERNAL_SERVER_ERROR"
        assert data["detail"] == "Something went wrong"


class TestErrorCodes:
    """Test standard error codes."""

    def test_all_error_codes_have_mappings(self):
        """Test that all defined error codes map to title and status."""
        from app.schemas.problem_details import ERROR_CODES

        expected_codes = [
            "OAUTH_STATE_INVALID",
            "OAUTH_CODE_EXCHANGE_FAILED",
            "OAUTH_TOKEN_REFRESH_FAILED",
            "INTEGRATION_NOT_FOUND",
            "INTEGRATION_NOT_CONNECTED",
            "UNAUTHORIZED",
            "INVALID_SESSION_TOKEN",
        ]

        for code in expected_codes:
            assert code in ERROR_CODES
            title, status = ERROR_CODES[code]
            assert isinstance(title, str)
            assert isinstance(status, int)
            assert 400 <= status < 600

    def test_error_code_statuses_correct(self):
        """Test error codes have correct HTTP statuses."""
        from app.schemas.problem_details import ERROR_CODES

        assert ERROR_CODES["UNAUTHORIZED"][1] == 401
        assert ERROR_CODES["INVALID_SETUP_SECRET"][1] == 403
        assert ERROR_CODES["OAUTH_STATE_INVALID"][1] == 400
        assert ERROR_CODES["INTEGRATION_NOT_FOUND"][1] == 404
        assert ERROR_CODES["OWNER_ALREADY_INITIALIZED"][1] == 409
        assert ERROR_CODES["INTERNAL_SERVER_ERROR"][1] == 500
        assert ERROR_CODES["SERVICE_UNAVAILABLE"][1] == 503
