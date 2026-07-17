# Environment Variable Inventory

## Ownership categories

- Platform owner: defaults and non-secret toggles.
- Secret owner: OAuth keys, API keys, signing materials.
- Developer local: machine-specific overrides.

## Variables

| Variable                  | Secret  | Owner           | Purpose                    | Example                                                |
| ------------------------- | ------- | --------------- | -------------------------- | ------------------------------------------------------ |
| APP_NAME                  | No      | Platform owner  | Product identifier         | lockdin                                                |
| APP_ENV                   | No      | Platform owner  | Runtime environment        | local                                                  |
| APP_LOG_LEVEL             | No      | Platform owner  | Logging verbosity          | INFO                                                   |
| LOCKDIN_API_HOST          | No      | Developer local | API bind host              | 127.0.0.1                                              |
| LOCKDIN_API_PORT          | No      | Developer local | API bind port              | 8000                                                   |
| LOCKDIN_WEB_ORIGIN        | No      | Developer local | Frontend origin            | http://localhost:3000                                  |
| APP_BOOTSTRAP_TOKEN       | Yes     | Secret owner    | One-time owner setup secret | (set locally, at least 32 characters)                  |
| DATABASE_URL              | Usually | Secret owner    | Postgres connection string | postgresql+psycopg://...                               |
| REDIS_URL                 | Usually | Secret owner    | Redis connection string    | redis://localhost:6379/0                               |
| GOOGLE_CLIENT_ID          | Yes     | Secret owner    | Google OAuth client id     | (set locally)                                          |
| GOOGLE_CLIENT_SECRET      | Yes     | Secret owner    | Google OAuth client secret | (set locally)                                          |
| GOOGLE_REDIRECT_URI       | No      | Platform owner  | OAuth callback route       | http://localhost:8000/api/integrations/google/callback |
| MODEL_ROUTER_DEFAULT      | No      | Platform owner  | Routing mode               | balanced                                               |
| MODEL_ROUTER_PRIVACY_TIER | No      | Platform owner  | Privacy preference         | local_first                                            |

## Rules

- Never commit secret values.
- Keep `.env.example` non-sensitive and up to date.
- Any new variable must be added here with owner and purpose.
