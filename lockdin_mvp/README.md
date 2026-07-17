# Lockd'In MVP Backend (Slice 1)

This folder contains implementation slice 1 for Lockd'In MVP infrastructure:

- FastAPI app with `/health`
- Startup config validation
- Canonical schemas (`Event`, `TaskSuggestion`)
- Google Calendar and Gmail connector normalization stubs
- SQLAlchemy models and repository layer
- Celery worker task for reminder generation
- Alembic initial migration
- Basic tests for normalization and reminder creation

This folder now also includes implementation slice 2 backend APIs:

- Integration lifecycle API (MVP): connect, refresh, revoke, list
- Consent API (MVP): upsert, list, delete
- Google OAuth token exchange and refresh via Google token endpoint

## Quick start

1. Copy `.env.example` to `.env` and fill values.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Apply migrations:

```bash
alembic upgrade head
```

4. Run API:

```bash
uvicorn app.main:app --reload
```

5. Bootstrap the first owner session once using the separate `APP_BOOTSTRAP_TOKEN` secret:

```powershell
$headers = @{ "X-Lockdin-Bootstrap-Token" = $env:APP_BOOTSTRAP_TOKEN }
$body = @{ display_name = "Owner"; device_name = $env:COMPUTERNAME; platform = "windows" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/session/bootstrap -Headers $headers -ContentType "application/json" -Body $body
```

The response contains `session_token` once. Send it to protected endpoints as `X-Lockdin-Session-Token`.

6. Run worker:

```bash
celery -A app.workers.celery_app.celery_app worker -l info
```

7. Run tests:

```bash
pytest -q
```

## New API endpoints (Slice 2)

- `POST /api/integrations/google/connect`
- `GET /api/integrations/google/authorize-url`
- `GET /api/integrations/google/callback`
- `POST /api/integrations/{provider}/refresh`
- `POST /api/integrations/{provider}/revoke`
- `GET /api/integrations`
- `POST /api/integrations/google/sync`
- `POST /api/consent`
- `GET /api/consent`
- `DELETE /api/consent/{consent_id}`

For `POST /api/integrations/google/connect`, send `auth_code` from your Google OAuth consent flow and include `redirect_uri` that matches your OAuth app configuration.

Google sync behavior is consent-gated in MVP:

- Calendar sync runs only if consent exists for `integration=google`, `data_category=calendar`, `purpose=sync`.
- Gmail sync runs only if consent exists for `integration=google`, `data_category=gmail`, `purpose=sync`.

## Migrations

Run initial migration:

```bash
alembic upgrade head
```

> Note: `alembic.ini` contains a default local DB URL. Update it or provide `DATABASE_URL` before running.
