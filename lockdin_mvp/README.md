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

## Quick start

1. Copy `.env.example` to `.env` and fill values.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run API:

```bash
uvicorn app.main:app --reload
```

4. Run worker:

```bash
celery -A app.workers.celery_app.celery_app worker -l info
```

5. Run tests:

```bash
pytest -q
```

## Migrations

Run initial migration:

```bash
alembic upgrade head
```

> Note: `alembic.ini` contains a default local DB URL. Update it or provide `DATABASE_URL` before running.
