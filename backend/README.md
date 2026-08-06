
# RadiusFlow Management Backend

FastAPI service for managing FreeRADIUS internet users through the existing PostgreSQL radius database, with a Flask management interface mounted at `/admin`.

## Full Stack Docker

To run both the API and the frontend in containers from the repo root:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up -d --build
```

The frontend will be available on `http://localhost:8080` and the backend on `http://localhost:8000`.

## Architecture

```text
Frontend / Admin UI -> RadiusFlow API container -> FreeRADIUS PostgreSQL DB
                                      |
                                      -> radclient CoA disconnects to NAS/MikroTik
```

## Quick Start: Docker

```bash
cd backend
cp .env.example .env
# Edit .env with your real FreeRADIUS PostgreSQL and admin credentials
docker-compose up -d --build
```

The Compose port is bound to `127.0.0.1:8000`; expose it through an HTTPS reverse proxy instead of publishing Uvicorn directly.

Swagger is available at:

```text
http://YOUR_SERVER_IP:8000/docs
```

The management login is available at:

```text
http://YOUR_SERVER_IP:8000/admin/login
```

See `DEPLOYMENT.md` for the approval-gated VPS deployment, database objects,
least-privilege grants, and migration commands.

## Required Integration Values

```env
DATABASE_URL=postgresql://radius:your_password@host.docker.internal:5432/radius
JWT_SECRET=replace-with-a-long-random-secret
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
ENVIRONMENT=production
FLASK_SECRET_KEY=replace-with-a-different-long-random-secret
AUTH_SESSION_HOURS=12
SESSION_COOKIE_SECURE=true
```

`JWT_SECRET` and `FLASK_SECRET_KEY` must be different random values. Production startup fails when the Flask secret or secure-cookie setting is unsafe.

## Management Authentication Setup

Apply the application-table migration only after confirming `DATABASE_URL` targets the intended FreeRADIUS PostgreSQL database:

```bash
cd backend
python -m alembic upgrade head
```

Create the first management user without placing its password in shell history:

```bash
python -m flask --app 'app.web:create_web_app' create-admin admin --role admin
```

The command prompts for the password and confirmation. Management passwords are stored as scrypt hashes. Browser sessions and API bearer tokens use revocable, SHA-256-token-hashed records in `app_sessions`; raw session tokens are never stored in the database.

If PostgreSQL runs directly on the same VPS host as Docker, use `host.docker.internal`; it is mapped in `docker-compose.yml`.
If you are using the SSH tunnel command `ssh -N -L 55432:127.0.0.1:5432 valentin@5.189.153.17`, point `DATABASE_URL` at `localhost:55432` when running the backend locally, or `host.docker.internal:55432` inside Docker.
If PostgreSQL runs in another container or remote server, set `DATABASE_URL` to that hostname or IP.

## Local Development

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing

Smoke tests do not touch your live FreeRADIUS database:

```bash
python -m unittest discover -s tests
```

## Endpoint Groups

All documented API routes are versioned under `/api/v1`.

| Tag | Purpose |
| --- | --- |
| Auth | Admin JWT login |
| Users | Create, update, block, renew, disconnect, and inspect users |
| Packages | FreeRADIUS group/package CRUD and user assignment |
| NAS | NAS/MikroTik CRUD and active session counts |
| Sessions | Active sessions, stale sessions, and cleanup |
| Monitoring | Dashboard, traffic, online users, and summary stats |
| Logs | Authentication logs and failed attempts |
| Notifications | Africa's Talking SMS |
| System | Health checks |

Management routes require `Authorization: Bearer <token>`. Get a token from `/api/v1/auth/token`.

## Security Checklist

- Change `JWT_SECRET`.
- Change `ADMIN_PASSWORD`.
- Set `CORS_ORIGINS` to your frontend URL.
- Put the API behind HTTPS before public use.
- Keep PostgreSQL private; do not expose port `5432` publicly.
- Store correct NAS secrets in the FreeRADIUS `nas` table for CoA disconnects.
