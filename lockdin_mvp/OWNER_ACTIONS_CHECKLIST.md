# Lockd'In MVP Owner Actions Checklist

This is your single execution checklist to run through after implementation work is done.

Use this file as your source of truth for:
- Previous slice setup actions
- Just-finished slice run actions
- Next-slice preparation actions
- MVP completion readiness checks

## 1) Security First (Do Immediately)

1. Rotate any API keys that were exposed in local files or shared logs.
2. Ensure `lockdin_mvp/.env` is in `.gitignore` and never committed.
3. Replace all placeholder secrets with real values.
4. Keep credentials scoped to least privilege.

## 2) Environment Setup (From Previous Slice)

1. Install Python 3.11 on Windows:
   winget install Python.Python.3.11

2. Create and use a Python 3.11 virtual environment in lockdin_mvp:
   py -3.11 -m venv .venv311
   .venv311\Scripts\python.exe -m pip install -r requirements.txt

3. Install and run PostgreSQL locally.

4. Install and run Redis locally (non-Docker path is valid, e.g., Memurai service on Windows).

5. Confirm your `.env` has valid values for:
   APP_ENV
   APP_HOST
   APP_PORT
   DATABASE_URL
   REDIS_URL
   APP_ENCRYPTION_KEY
   GOOGLE_CLIENT_ID
   GOOGLE_CLIENT_SECRET
   GOOGLE_OAUTH_TOKEN_URL
   STEPFUN_API_KEY (optional)
   NEMOTRON_API_KEY (optional)

## 3) Database + Migrations (Current Required Step)

1. Ensure PostgreSQL database exists and credentials match DATABASE_URL.
2. Run migrations:
   .venv311\Scripts\python.exe -m alembic upgrade head
3. Verify tables exist:
   events
   task_suggestions
   integration_tokens
   consent_records

## 4) Run the Services (Just-Finished Implementation)

1. Run API:
   .venv311\Scripts\python.exe -m uvicorn app.main:app --reload

2. Run Celery worker:
   .venv311\Scripts\python.exe -m celery -A app.workers.celery_app.celery_app worker -l info

3. Run tests:
   .venv311\Scripts\python.exe -m pytest -q

## 5) OAuth and Consent Setup (From Current Slice)

1. In Google Cloud Console, configure OAuth app credentials.
2. Add callback URLs for local and staging.
3. Make sure redirect_uri sent to /api/integrations/google/connect exactly matches configured callback.
4. Validate OAuth lifecycle endpoints manually:
   POST /api/integrations/google/connect
   POST /api/integrations/{provider}/refresh
   POST /api/integrations/{provider}/revoke
   GET /api/integrations

5. Validate consent endpoints manually:
   POST /api/consent
   GET /api/consent
   DELETE /api/consent/{consent_id}

## 6) New Slice Actions (Authorize/Callback + Sync)

1. Validate OAuth authorize URL endpoint:
   GET /api/integrations/google/authorize-url

2. Verify callback flow with matching state and redirect URI:
   GET /api/integrations/google/callback

3. Seed consent records for sync (required before ingestion):
   - integration=google, data_category=calendar, purpose=sync, granted=true
   - integration=google, data_category=gmail, purpose=sync, granted=true

4. Trigger sync endpoint:
   POST /api/integrations/google/sync

5. For local debug without worker, run sync inline with request body:
   {"run_inline": true}

6. Verify ingested events are available in events table and reminders can be generated.

## 7) Next Slice Prep (What You Need to Do Before We Implement Further)

1. Confirm frontend callback route to capture Google auth code and send it to backend.
2. Decide canonical user identity source for MVP (replace local-user stub in APIs).
3. Define initial consent policy matrix:
   - integration
   - data_category
   - purpose
   - granted default

4. Prepare sample Google Calendar and Gmail test accounts/data.
5. Decide staging environment values for:
   DATABASE_URL
   REDIS_URL
   APP_HOST and APP_PORT
   OAuth callback URL

## 7) MVP Completion Owner Checklist

1. Infrastructure
   - PostgreSQL and Redis stable
   - Migration history consistent
   - API and worker both healthy

2. Trust/Safety
   - Consent records required before integration ingestion
   - Integration revocation path tested
   - Secret rotation process documented

3. Functionality
   - Reminder flow works end-to-end
   - OAuth connect/refresh/revoke works end-to-end
   - Consent create/list/delete works end-to-end

4. Quality
   - Tests pass consistently in Python 3.11 env
   - Error logs reviewed for noisy failures

5. Launch Readiness
   - .env never committed
   - Keys rotated and scoped
   - Basic runbook documented for local + staging

## 8) Daily Command Block (Quick Copy Reference)

From lockdin_mvp folder:

1. Activate venv:
   .venv311\Scripts\activate

2. Install deps (if changed):
   .venv311\Scripts\python.exe -m pip install -r requirements.txt

3. Run migrations:
   .venv311\Scripts\python.exe -m alembic upgrade head

4. Start API:
   .venv311\Scripts\python.exe -m uvicorn app.main:app --reload

5. Start worker (new terminal):
   .venv311\Scripts\python.exe -m celery -A app.workers.celery_app.celery_app worker -l info

6. Run tests:
   .venv311\Scripts\python.exe -m pytest -q
