# RadiusFlow Deployment Plan

This plan is approval-gated. Do not run production database commands until the
VPS configuration and FreeRADIUS schema have been reviewed.

## Database Changes

Migration `20260724_0001` creates only these application-owned objects:

### `app_users`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | integer | primary key, generated sequence |
| `username` | varchar(64) | not null, unique index |
| `password_hash` | varchar(255) | not null |
| `role` | varchar(32) | not null; admin, operator, or viewer |
| `is_active` | boolean | not null |
| `last_login_at` | timestamptz | nullable |
| `created_at` | timestamptz | not null, current timestamp |
| `updated_at` | timestamptz | not null, current timestamp |

### `app_sessions`

| Column | Type | Constraints |
| --- | --- | --- |
| `id` | integer | primary key, generated sequence |
| `user_id` | integer | foreign key to `app_users.id`, cascade delete |
| `token_hash` | varchar(64) | not null, unique index |
| `ip_address` | varchar(45) | nullable |
| `user_agent` | varchar(255) | nullable |
| `created_at` | timestamptz | not null, current timestamp |
| `last_seen_at` | timestamptz | not null, current timestamp |
| `expires_at` | timestamptz | not null, indexed |
| `revoked_at` | timestamptz | nullable |

Alembic also creates `alembic_version`. The migration does not alter, delete,
truncate, reference, or add foreign keys to any FreeRADIUS table. Its only
foreign key is `app_sessions.user_id -> app_users.id`.

Other generated objects are:

```text
app_users_id_seq
app_sessions_id_seq
ix_app_users_username               UNIQUE
ix_app_sessions_token_hash          UNIQUE
ix_app_sessions_user_id
ix_app_sessions_expires_at
alembic_version_pkc
```

Migration source:
`alembic/versions/20260724_0001_add_management_auth.py`

Review the exact PostgreSQL DDL without connecting to a database:

```bash
python -m alembic upgrade head --sql
```

## Required Environment

Create `/opt/radiusflow/backend/.env` on the VPS with mode `0600`:

```env
DATABASE_URL=postgresql+psycopg2://radiusflow_app:URL_ENCODED_PASSWORD@host.docker.internal:5432/radius
JWT_SECRET=GENERATE_A_LONG_RANDOM_VALUE
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=12
CORS_ORIGINS=https://radius.example.com
SMS_API_KEY=
SMS_USERNAME=
SMS_SENDER_ID=RADIUS
HOST=0.0.0.0
PORT=8000
API_V1_PREFIX=/api/v1
ENVIRONMENT=production
FLASK_SECRET_KEY=GENERATE_A_DIFFERENT_LONG_RANDOM_VALUE
AUTH_SESSION_HOURS=12
SESSION_COOKIE_SECURE=true
```

`JWT_SECRET` and `FLASK_SECRET_KEY` must be different. Do not commit `.env`.
Passwords embedded in `DATABASE_URL` must be URL-encoded.

Generate secrets on the VPS:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Run that command twice and use a different result for each secret.

## PostgreSQL Permissions

Use one dedicated, unprivileged application role. The database owner creates it
and temporarily grants schema creation only for the reviewed migration:

```sql
CREATE ROLE radiusflow_app
    LOGIN
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;

-- Set its password interactively with \password radiusflow_app.
GRANT CONNECT ON DATABASE radius TO radiusflow_app;
GRANT USAGE, CREATE ON SCHEMA public TO radiusflow_app;
```

Run the reviewed migration as `radiusflow_app`, making it the owner of the new
application objects. Immediately afterward:

```sql
REVOKE CREATE ON SCHEMA public FROM radiusflow_app;
GRANT SELECT, INSERT, UPDATE, DELETE
    ON TABLE public.app_users, public.app_sessions
    TO radiusflow_app;
GRANT USAGE, SELECT
    ON SEQUENCE public.app_users_id_seq, public.app_sessions_id_seq
    TO radiusflow_app;
```

Do not grant ownership of the database or schema, superuser, database creation,
role creation, replication, or bypass-RLS.

Permissions for `radcheck`, `radreply`, `radacct`, `radusergroup`,
`radgroupcheck`, `radgroupreply`, `radpostauth`, and `nas` will be specified
after their live schemas and each management module have been reviewed.

## Approval-Gated Deployment

After source review, schema review, and explicit approval:

```bash
sudo install -d -o "$USER" -g "$USER" /opt/radiusflow
cd /opt/radiusflow/backend
chmod 600 .env

docker compose config --quiet
docker compose build

# Render and review SQL again before applying it.
docker compose run --rm radiusflow-api python -m alembic upgrade head --sql

# Apply only after a database backup and explicit approval.
docker compose run --rm radiusflow-api python -m alembic upgrade head

# Password is entered interactively and is not stored in shell history.
docker compose run --rm radiusflow-api \
  python -m flask --app app.web:create_web_app \
  create-admin admin --role admin

docker compose up -d
docker compose ps
curl --fail http://127.0.0.1:8000/api/v1/health
```

The Compose service binds to `127.0.0.1:8000`. Configure an HTTPS reverse
proxy before allowing remote browser access.

## Production Preconditions

Before the commands above:

1. Back up the `radius` database and verify the backup file.
2. Inspect the live FreeRADIUS table definitions and PostgreSQL version.
3. Confirm PostgreSQL listens on an interface reachable only from the
   application container/host.
4. Add the narrow `pg_hba.conf` rule required by the dedicated runtime role.
5. Confirm the application container can resolve `host.docker.internal`.
6. Review the generated Alembic SQL and verify it contains only the objects
   listed in this document.
7. Configure Nginx or another reverse proxy with TLS.
8. Keep FreeRADIUS and PostgreSQL ports closed to the public internet.

Stopping or rolling back the application does not require changing existing
FreeRADIUS tables. Preserve the application tables during an application
rollback so management identities and session audit data are not lost.
