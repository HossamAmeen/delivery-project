# Flash backend

Django REST Framework API for Flash, built to `DRF_SKILL.md` (ADR-001) with the
server adaptations in ADR-015 (systemd + gunicorn), ADR-017 (SQLite WAL,
FileBasedCache, Celery disabled) and ADR-018 (tests run on the server).

## Layout

```
backend/
├── config/            settings (base / development / production / test), urls, wsgi, celery
├── common/            shared infrastructure: BaseModel, managers, errors, envelope, pagination, throttling, OpenAPI
├── apps/              domain apps (users, health, …)
├── tests/             project-level tests (settings, common, cache/celery)
└── requirements/      base / development / production (+ optional celery)
```

## Configuration

Every setting comes from the environment. Copy `.env.example` to `.env` for
local work; the file is read only if it exists. On the server systemd provides
the environment from `/srv/flash/shared/.env`.

`DJANGO_SETTINGS_MODULE` defaults to `config.settings.development` in
`manage.py` and to `config.settings.production` in `config/wsgi.py`
(gunicorn: `config.wsgi:application`). The environment always wins.

Production refuses to start without `SECRET_KEY`, `ALLOWED_HOSTS`,
`DATABASE_URL`, `STATIC_ROOT`, `MEDIA_ROOT`, `HEALTH_CHECK_PASSWORD` and a
shared `RATELIMIT_CACHE_URL` (not `locmem://`).

## Commands

See `Makefile`. The local machine (Python 3.12) is for editing and static
checks only (`make lint`, `make format-check`, `make check`).
**Test suites run on the server** (REQ-009): `make test-remote`, which calls
`make test-backend-remote WORKTREE=1` in the repo root. Results land in
`backend/.remote-results/`.

`pytest` always uses `config.settings.test` (development + LocMem cache, fast
hashing and a test-only app).

## API

- `GET /api/status/` public liveness for browsers
- `GET /api/health/`, `GET /api/health/ready/` header `X-Health-Check-Token`
- `POST /api/auth/token/`, `POST /api/auth/token/refresh/`, `GET /api/users/me/`
- `/api/schema/`, `/api/docs/`, `/api/redoc/` (staff only in production)

Contracts: `.ai/architecture/api-contracts.md`.

## Seeding users

```
FLASH_NEW_USER_PASSWORD=... python manage.py create_role_user --username qa_driver --role DRIVER
printf '%s\n' "$PASSWORD" | python manage.py create_role_user --username qa_admin --role ADMIN --superuser --password-stdin --update
```
The password is never accepted on the command line and never printed.
