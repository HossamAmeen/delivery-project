Django REST Framework Engineering Skill
Purpose
This skill defines the standard architecture, development workflow, testing strategy, Docker configuration, deployment structure, and engineering rules for Django REST Framework backend projects.
This skill is domain-agnostic.
It can be used for:
SaaS applications
Delivery platforms
Healthcare systems
E-commerce systems
ERP systems
CRM systems
Booking systems
Fintech applications
Internal business applications
APIs
Microservices
This skill supports three modes:
CREATE — create a new DRF project.
REFACTOR — refactor an existing Django/DRF project.
UPDATE — add or modify functionality in an existing project.

1. Engineering Principles
The agent MUST:
Read and understand the project before making changes.
Keep business domains separated into Django apps.
Keep business logic in the backend.
Keep shared infrastructure in common/.
Use environment variables for configuration and secrets.
Use automated tests for business behavior.
Preserve existing behavior when refactoring unless explicitly requested otherwise.
Avoid unnecessary rewrites.
Prefer incremental and testable changes.
Maintain backward compatibility whenever possible.
Keep API contracts consistent.
Use Django migrations for database schema changes.
Never hardcode secrets, domains, ports, filesystem paths, or service names.
Treat deployment configuration as code.
Validate changes before declaring work complete.
The backend is the source of truth for:
Business rules
Validation
Authorization
State transitions
Data integrity
Security
Business calculations
Lifecycle rules
Frontend applications must not duplicate backend business rules.

2. Technology Stack
Required
Python 3.13+
Django
Django REST Framework
django-environ
dj-database-url
djangorestframework-simplejwt
drf-spectacular
django-jazzmin
pytest
pytest-django
pytest-cov
Docker
Docker Compose
Database
Local development:
SQLite

Staging:
PostgreSQL

Production:
PostgreSQL

Optional Infrastructure
Redis
Celery
Celery Beat
Nginx
systemd
Celery and Redis are optional and must be controlled through environment configuration.

3. Standard Project Structure
A new project SHOULD use:
backend/
├── manage.py
│
├── config/
│   ├── __init__.py
│   ├── celery.py
│   │
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   │
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   ├── __init__.py
│   │
│   ├── users/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── managers.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── permissions.py
│   │   ├── services.py
│   │   ├── selectors.py
│   │   ├── tasks.py
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py
│   │   │   ├── test_models.py
│   │   │   ├── test_serializers.py
│   │   │   ├── test_views.py
│   │   │   ├── test_services.py
│   │   │   └── test_tasks.py
│   │   └── migrations/
│   │
│   └── <domain_apps>/
│
├── common/
│   ├── __init__.py
│   ├── models.py
│   ├── managers.py
│   ├── exceptions.py
│   ├── exception_handler.py
│   ├── responses.py
│   ├── pagination.py
│   └── permissions.py
│
├── tests/
│   ├── __init__.py
│   └── conftest.py
│
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
│
├── docker/
│   ├── local/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   │
│   ├── staging/
│   │   ├── Dockerfile
│   │   └── docker-compose.yml
│   │
│   └── production/
│       ├── Dockerfile
│       └── docker-compose.yml
│
├── deploy/
│   ├── nginx/
│   │   ├── generate.sh
│   │   └── templates/
│   │       └── nginx.conf.template
│   │
│   ├── systemd/
│   │   └── templates/
│   │       └── backend.service.template
│   │
│   └── scripts/
│       ├── deploy.sh
│       ├── migrate.sh
│       ├── collectstatic.sh
│       ├── restart.sh
│       └── healthcheck.sh
│
├── scripts/
│   ├── entrypoint.sh
│   └── wait_for_db.sh
│
├── .env
├── .env.example
├── .gitignore
├── Makefile
├── pytest.ini
└── README.md

The structure may be adapted for an existing project when necessary.
Do not force a large refactor merely to match this structure if the existing architecture is already valid.

4. CREATE Mode
When creating a new DRF project, follow this order:
Requirements
    ↓
Project structure
    ↓
Settings
    ↓
Environment configuration
    ↓
Database
    ↓
DRF
    ↓
JWT
    ↓
Common infrastructure
    ↓
OpenAPI
    ↓
Jazzmin
    ↓
Health API
    ↓
Testing
    ↓
Docker
    ↓
Celery/Redis if enabled
    ↓
Deployment structure
    ↓
Domain applications
    ↓
Business features
    ↓
Validation

The agent MUST establish the foundation before implementing business features.

5. REFACTOR Mode
When refactoring an existing project:
DO NOT immediately rewrite the project.
First inspect:
Project structure
Settings
Requirements
Models
Managers
Views
ViewSets
Serializers
URLs
Permissions
Authentication
Services
Selectors
Tasks
Tests
Migrations
Environment configuration
Docker
Docker Compose
Nginx
systemd
Deployment scripts
API documentation
Celery configuration

Then identify:
Current architecture
Problems
Technical debt
Security risks
Testing gaps
Deployment problems
Performance problems
Potential breaking changes
Recommended refactoring order

Refactor incrementally.
Recommended order:
1. Environment configuration
2. Settings separation
3. Common infrastructure
4. Authentication
5. Exception handling
6. Response standardization
7. Base model
8. Soft delete/managers
9. Domain separation
10. Services/selectors
11. Testing
12. OpenAPI
13. Docker
14. Deployment
15. Performance

Never perform a large rewrite without a clear reason.

6. UPDATE Mode
When adding a feature to an existing project:
Read
→ Understand
→ Identify affected domain
→ Inspect existing implementation
→ Inspect tests
→ Implement
→ Add/update tests
→ Update OpenAPI
→ Run validation

Do not modify unrelated functionality.

7. Settings
Never put all settings into one file.
Use:
config/settings/
├── base.py
├── development.py
└── production.py

base.py
Contains shared settings:
Installed apps
Middleware
DRF
Authentication
JWT
OpenAPI
Jazzmin
Internationalization
Static/media configuration
Shared security configuration
Celery configuration
development.py
Contains local development configuration.
production.py
Contains production configuration.

8. Environment Variables
Use .env for local configuration.
Commit only:
.env.example

Never commit:
.env

Example .env.example:
# Django
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=30
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Health API
HEALTH_CHECK_PASSWORD=change-me

# Celery
CELERY_ENABLED=False
CELERY_BEAT_ENABLED=False
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_TASK_ALWAYS_EAGER=False
CELERY_TASK_EAGER_PROPAGATES=False
CELERY_WORKER_CONCURRENCY=2

# Deployment
DOMAIN=example.com

BACKEND_PORT=8000
FRONTEND_PORT=3000

BACKEND_PATH=/opt/myapp/backend
FRONTEND_PATH=/opt/myapp/frontend

MEDIA_PATH=/opt/myapp/backend/media
STATIC_PATH=/opt/myapp/backend/static

SYSTEMD_SERVICE_NAME=myapp-backend

Never hardcode:
Passwords
Secret keys
Database credentials
API keys
JWT secrets
Domains
Ports
Filesystem paths
systemd service names

9. Database
Use DATABASE_URL.
Example:
import dj_database_url

DATABASES = {
    "default": dj_database_url.config(
        default="sqlite:///db.sqlite3",
        conn_max_age=600,
    )
}

Local development defaults to:
SQLite

Staging and production normally use:
PostgreSQL

All schema changes MUST use Django migrations.

10. Common Package
Use:
common/

instead of utils/ for shared architectural infrastructure.
Do not turn utils/ into a dumping ground.
common/ may contain:
common/
├── models.py
├── managers.py
├── exceptions.py
├── exception_handler.py
├── responses.py
├── pagination.py
└── permissions.py

Only functionality shared across multiple applications belongs here.
Domain-specific functionality MUST remain inside domain applications.

11. Base Model
Create an abstract base model in:
common/models.py

It must contain:
created_at
modified_at
deleted_at

Example:
from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


12. Soft Delete
Soft deletion should normally set:
deleted_at = current timestamp

instead of physically deleting records.
Provide:
soft_delete()
restore()

where appropriate.

13. Custom Managers
Create reusable managers in:
common/managers.py

Example:
class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            deleted_at__isnull=True
        )


class DeletedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            deleted_at__isnull=False
        )


class AllManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

Example model:
class Example(BaseModel):
    objects = ActiveManager()
    deleted_objects = DeletedManager()
    all_objects = AllManager()

Expected behavior:
Example.objects.all()
Example.deleted_objects.all()
Example.all_objects.all()

The default manager should normally return only active records.

14. Django Applications
Business domains must be separated into Django apps.
Example:
apps/
├── users/
├── orders/
├── products/
├── payments/
└── notifications/

The actual apps depend on project requirements.
Do not create one giant application for the entire system.

15. DRF API Architecture
All APIs must use Django REST Framework.
Each API should contain the appropriate:
Serializer
View/ViewSet
URL
Permission
Validation
Tests
Use the simplest appropriate DRF abstraction.

16. Business Logic
Business logic belongs in the backend.
Preferred layers:
models.py
services.py
selectors.py

Use services for business workflows.
Use selectors for complex read/query logic.
Do not duplicate business logic in:
Web
PWA
Flutter
Mobile clients

17. Authentication
Use:
djangorestframework-simplejwt

Support:
Access Token
Refresh Token

Typical endpoints:
POST /api/auth/token/
POST /api/auth/token/refresh/

JWT configuration should come from environment variables where appropriate.

18. Authorization
Use DRF permissions.
Examples:
IsAuthenticated
IsAdminUser
CustomRolePermission
Object-level permissions

Never rely on frontend permissions as a security mechanism.

19. Standard API Responses
All APIs should use a consistent response format.
Success:
{
    "success": true,
    "message": "Operation completed successfully.",
    "data": {}
}

Error:
{
    "success": false,
    "message": "Validation failed.",
    "errors": {
        "field": [
            "This field is required."
        ]
    }
}

For an existing project, do not change an established API response contract unnecessarily.

20. Centralized Exception Handling
Implement:
common/exception_handler.py

Handle:
Validation errors
Authentication errors
Permission errors
Not found errors
Throttling errors
Custom application exceptions
Unexpected exceptions
All API errors should follow the standard response structure.
Do not duplicate exception formatting inside individual views.

21. OpenAPI Documentation
Use:
drf-spectacular

Provide:
/api/schema/
/api/docs/
/api/redoc/

where appropriate.
Every public API must be documented.
Document:
Request body
Response
Authentication
Query parameters
Path parameters
Important validation rules

22. Django Jazzmin
Install:
django-jazzmin

Add Jazzmin before Django Admin in INSTALLED_APPS:
INSTALLED_APPS = [
    "jazzmin",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
]

Basic configuration:
JAZZMIN_SETTINGS = {
    "site_title": "Django Admin",
    "site_header": "Django Administration",
    "site_brand": "Backend",
    "welcome_sign": "Welcome to the administration panel",
    "copyright": "Backend",
    "show_sidebar": True,
    "navigation_expanded": True,
}

Jazzmin must not be coupled to a specific business domain.
Django Admin must remain protected by Django authentication and staff/superuser permissions.

23. Health API
Every new DRF project must provide a health-check endpoint.
Recommended endpoint:
GET /api/health/

The health endpoint must use a password/token configured through .env.
Example:
HEALTH_CHECK_PASSWORD=change-me

Never hardcode the password.

24. Health API Authentication
Recommended request:
GET /api/health/?password=<HEALTH_CHECK_PASSWORD>

The password must be read from environment configuration.
Example:
HEALTH_CHECK_PASSWORD = env(
    "HEALTH_CHECK_PASSWORD",
)

Do not expose the configured password in responses or logs.
For production deployments, a dedicated HTTP header such as:
X-Health-Check-Token

is preferred when possible, because query parameters may appear in access logs.

25. Health API Response
Successful:
{
    "success": true,
    "message": "Service is healthy.",
    "data": {
        "status": "healthy"
    }
}

Invalid password:
{
    "success": false,
    "message": "Invalid health check password.",
    "errors": {}
}

Do not expose:
Environment variables
Passwords
Database credentials
Secret keys
Stack traces
Filesystem paths
Internal exceptions

26. Health vs Readiness
The basic health endpoint should verify that the Django application is running.
It should NOT depend on optional services.
Optional readiness endpoint:
GET /api/health/ready/

may verify:
Database
Redis
Celery
Required external services
If:
CELERY_ENABLED=False

the readiness check must not require Celery.

27. Health API Tests
Required tests:
test_health_endpoint_returns_success_with_valid_password
test_health_endpoint_rejects_invalid_password
test_health_endpoint_requires_password
test_health_endpoint_does_not_expose_secret

Readiness tests should cover dependency failures when readiness checks are implemented.
Tests must use test environment values, never production secrets.

28. Celery
Celery is an optional infrastructure component.
The same application must support:
CELERY_ENABLED=False

and:
CELERY_ENABLED=True

without changing business code.
Configuration:
CELERY_ENABLED=False
CELERY_BEAT_ENABLED=False

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

CELERY_TASK_ALWAYS_EAGER=False
CELERY_TASK_EAGER_PROPAGATES=False

CELERY_WORKER_CONCURRENCY=2

When disabled:
Django must start normally.
Redis must not be required for normal Django operation.
Celery workers must not be started.
Celery Beat must not be started.
When enabled:
The configured broker must be available.
Celery workers must be deployed.
Celery Beat must only be deployed when enabled.

29. Celery Configuration
Use:
config/celery.py

Example:
import os

from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.development",
)

app = Celery("backend")

app.config_from_object(
    "django.conf:settings",
    namespace="CELERY",
)

app.autodiscover_tasks()

Update:
# config/__init__.py

from .celery import app as celery_app

__all__ = ("celery_app",)

Celery tasks belong to the Django app that owns the business functionality.
Example:
apps/
└── notifications/
    └── tasks.py


30. Celery Business Logic
Celery tasks should be thin wrappers around services.
Preferred:
Celery Task
    ↓
Service
    ↓
Business Logic
    ↓
Database

Do not place large business workflows directly inside tasks.

31. Celery Transactions
When a task depends on data created inside a database transaction, use:
from django.db import transaction

transaction.on_commit(
    lambda: task.delay(object.id)
)

This prevents workers from running before the transaction commits.

32. Celery Reliability
Tasks interacting with external systems should consider:
Retries
Backoff
Maximum retry count
Failure handling
Idempotency
Do not blindly retry non-idempotent operations.

33. Celery Docker
When enabled, Docker Compose should provide:
redis
celery-worker

When Beat is enabled:
celery-beat

Do not start these services when disabled.

34. Testing
Use:
pytest
pytest-django
pytest-cov

Every business feature must have automated tests.
Test:
Models
Creation
Modification
Soft delete
Restore
Managers
Constraints
Model methods
Serializers
Valid input
Invalid input
Required fields
Validation
Representation
APIs
Authentication
Authorization
Success
Validation errors
Not found
Permissions
Pagination
Filtering
Services
Happy paths
Business rules
Failure cases
Edge cases
Transactions
Celery
Task execution
Arguments
Success
Failure
Retry behavior
Idempotency where applicable

35. Fixtures
Use pytest fixtures.
Global:
tests/conftest.py

Application-specific:
apps/<app>/tests/conftest.py

Use fixtures for:
Users
API clients
Authentication
Domain objects
Roles
Permissions
Common test data
Do not duplicate setup unnecessarily.

36. Coverage
Run:
pytest --cov=. --cov-report=term-missing

Coverage must represent meaningful tests.
Do not create meaningless tests only to increase coverage.
Recommended initial minimum:
80%

unless project requirements specify otherwise.

37. pytest Configuration
Use:
pytest.ini

Example:
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.development
python_files = tests.py test_*.py *_tests.py
addopts = --strict-markers


38. Migrations
All schema changes MUST use Django migrations.
Run:
python manage.py makemigrations
python manage.py migrate

Validate:
python manage.py makemigrations --check

Never destructively modify migration history in an established project without explicit approval.

39. Query Performance
Avoid N+1 queries.
Use:
select_related()
prefetch_related()

where appropriate.
Do not optimize prematurely.

40. Pagination
Collection APIs should use pagination where appropriate.
Never expose unbounded large querysets through public APIs.

41. Docker Architecture
Separate Docker configuration by environment:
docker/
├── local/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── staging/
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── production/
    ├── Dockerfile
    └── docker-compose.yml


42. Local Docker
Local Docker should optimize developer experience.
Depending on project requirements, it may contain:
backend
database
redis
celery-worker
celery-beat

SQLite may be used locally when PostgreSQL is not required.

43. Staging Docker
Staging should resemble production as closely as practical.
Typical services:
backend
postgres
redis
celery-worker
celery-beat
nginx

Only required services should be included.
Staging must remain isolated from production.

44. Production Docker
Production may contain:
backend
postgres
redis
celery-worker
celery-beat
nginx

Managed infrastructure may replace Docker services.
Do not force infrastructure into Docker when managed services are used.

45. Makefile
Every new project must contain a Makefile.
It should expose the main commands.
Example:
install:
	pip install -r requirements/base.txt

install-dev:
	pip install -r requirements/development.txt

run:
	python manage.py runserver

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

test:
	pytest

coverage:
	pytest --cov=. --cov-report=term-missing

check:
	python manage.py check

lint:
	ruff check .

format:
	ruff format .

shell:
	python manage.py shell

collectstatic:
	python manage.py collectstatic --noinput

celery-worker:
	celery -A config worker --loglevel=INFO

celery-beat:
	celery -A config beat --loglevel=INFO

docker-local:
	docker compose -f docker/local/docker-compose.yml up --build

docker-staging:
	docker compose -f docker/staging/docker-compose.yml up --build -d

docker-production:
	docker compose -f docker/production/docker-compose.yml up --build -d

deploy-staging:
	bash deploy/scripts/deploy.sh staging

deploy-production:
	bash deploy/scripts/deploy.sh production

The agent may add project-specific commands.

46. Deployment Structure
Deployment configuration belongs in:
deploy/
├── nginx/
│   ├── generate.sh
│   └── templates/
│       └── nginx.conf.template
│
├── systemd/
│   └── templates/
│       └── backend.service.template
│
└── scripts/
    ├── deploy.sh
    ├── migrate.sh
    ├── collectstatic.sh
    ├── restart.sh
    └── healthcheck.sh


47. Deployment Environment Variables
Deployment MUST read configuration from .env.
At minimum:
DOMAIN=example.com

BACKEND_PORT=8000
FRONTEND_PORT=3000

BACKEND_PATH=/opt/myapp/backend
FRONTEND_PATH=/opt/myapp/frontend

MEDIA_PATH=/opt/myapp/backend/media
STATIC_PATH=/opt/myapp/backend/static

SYSTEMD_SERVICE_NAME=myapp-backend

HEALTH_CHECK_PASSWORD=change-me

Never hardcode these values in deployment scripts.

48. Nginx Configuration
Nginx must use a template:
deploy/nginx/templates/nginx.conf.template

and generator:
deploy/nginx/generate.sh

The generator must read environment variables.
At minimum:
DOMAIN
BACKEND_PORT
FRONTEND_PORT
BACKEND_PATH
FRONTEND_PATH
MEDIA_PATH
STATIC_PATH

Example:
server {
    listen 80;
    server_name ${DOMAIN};

    location /api/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
    }

    location /media/ {
        alias ${MEDIA_PATH}/;
    }

    location /static/ {
        alias ${STATIC_PATH}/;
    }

    location / {
        root ${FRONTEND_PATH};
        try_files $uri $uri/ /index.html;
    }
}

The exact configuration must be adapted to the actual project.
The agent MUST NOT hardcode:
Domain
Backend port
Frontend path
Media path
Static path

49. systemd
For deployments using systemd:
deploy/systemd/templates/backend.service.template

Values must come from .env.
Required variables:
SYSTEMD_SERVICE_NAME
BACKEND_PATH
BACKEND_PORT

Example:
[Unit]
Description=${SYSTEMD_SERVICE_NAME}
After=network.target

[Service]
WorkingDirectory=${BACKEND_PATH}

ExecStart=${BACKEND_PATH}/venv/bin/gunicorn \
    config.wsgi:application \
    --bind 127.0.0.1:${BACKEND_PORT}

Restart=always

[Install]
WantedBy=multi-user.target

The actual server may use Gunicorn, Uvicorn, or another appropriate server.

50. Deployment Scripts
Required:
deploy/scripts/deploy.sh
deploy/scripts/migrate.sh
deploy/scripts/collectstatic.sh
deploy/scripts/restart.sh
deploy/scripts/healthcheck.sh

Deployment flow:
Load environment
    ↓
Validate required variables
    ↓
Build/pull application
    ↓
Install dependencies
    ↓
Run migrations
    ↓
Collect static files
    ↓
Generate Nginx configuration
    ↓
Generate/update systemd configuration
    ↓
Restart backend
    ↓
Start required Celery services
    ↓
Health check

Scripts should use:
set -euo pipefail

when appropriate.
Never expose secrets in logs.

51. Deployment Health Check
After deployment, the deployment system MUST verify the health endpoint.
The health-check script must read:
DOMAIN
HEALTH_CHECK_PASSWORD
BACKEND_PORT

from environment configuration.
The deployment should fail if the backend does not become healthy.
Do not print the health password in logs.

52. Docker Health Check
Docker Compose may use the health endpoint.
Example concept:
healthcheck:
  test:
    [
      "CMD",
      "curl",
      "-f",
      "http://localhost:${BACKEND_PORT}/api/health/"
    ]
  interval: 30s
  timeout: 10s
  retries: 3

If authentication is required, implement the health check using a secure mechanism appropriate to the environment.
Do not expose health credentials unnecessarily.

53. Environment Separation
Clearly separate:
Local
Staging
Production

Docker:
docker/local/
docker/staging/
docker/production/

Django:
config/settings/development.py
config/settings/production.py

Never accidentally deploy staging configuration to production.
Never use production credentials in local development.

54. Security
Never hardcode:
Passwords
Secret keys
Database credentials
API keys
JWT secrets
Health-check secrets
Domains
Production paths
Service names
Use environment variables.
Do not expose .env.
Do not log sensitive environment variables.
Django Admin must remain protected.
Health credentials must not be exposed.

55. Backward Compatibility
When modifying an existing project:
Preserve API contracts where possible.
Preserve existing data.
Preserve authentication behavior.
Preserve business behavior.
Avoid unnecessary field renaming.
Avoid unnecessary endpoint removal.
Avoid destructive migrations.
Breaking changes must be clearly identified.

56. API Contract
For significant features:
Requirement
    ↓
Domain Analysis
    ↓
Data Model
    ↓
API Contract
    ↓
Serializer
    ↓
Service
    ↓
View
    ↓
Permission
    ↓
Tests
    ↓
OpenAPI

The API contract should be defined before dependent frontend clients are implemented.

57. Required Validation Commands
Before completing work, run:
python manage.py check

python manage.py makemigrations --check

pytest

pytest --cov=. --cov-report=term-missing

If configured:
ruff check .

For Docker changes:
docker compose -f docker/local/docker-compose.yml config

and validate the relevant staging/production Compose files when changed.
For deployment changes:
Validate generated Nginx configuration.
Validate generated systemd configuration.
Validate required environment variables.
Run deployment health checks.

58. Definition of Done
A feature is complete only when:
Requirement understood
Correct Django app identified
Model implemented if required
Migration created
Serializer implemented
Business logic implemented
View/ViewSet implemented
URL configured
Permission implemented
Validation implemented
Standard API response verified
Exception handling verified
Tests implemented
Fixtures added where useful
Coverage checked
OpenAPI updated
Existing tests still pass
Django checks pass
Migration checks pass
Docker validated if changed
Celery validated if used
Jazzmin configured if applicable
Health API implemented
Nginx validated if changed
systemd validated if changed
Deployment scripts validated if changed
No secrets are hardcoded
No environment-specific values are hardcoded

59. Existing Project Safety Rules
When working on an existing project:
Read before changing.
Understand existing behavior.
Inspect existing tests.
Inspect migrations.
Inspect API contracts.
Inspect Docker configuration.
Inspect deployment configuration.
Inspect Nginx configuration.
Inspect systemd configuration.
Inspect Celery configuration.
Inspect environment configuration.
Avoid unnecessary rewrites.
Make incremental changes.
Add regression tests.
Run the existing test suite.
Validate the final architecture.
Document breaking changes.
Never assume an existing project already follows this skill.

60. Final Principle
Business requirements determine:
WHAT the system does.

This skill determines:
HOW the DRF backend is:

- Structured
- Configured
- Implemented
- Tested
- Documented
- Containerized
- Deployed
- Maintained

This skill must remain generic and reusable.
It must work for any Django REST Framework project without being tied to a specific business domain.

61. API Rate Limiting
All public/open APIs MUST have rate limiting enabled.
The goal is to protect the API against:
Abuse
Brute-force attempts
Excessive requests
Accidental request floods
Denial-of-service patterns
Authentication attacks
Resource exhaustion
Rate limiting must be implemented at the backend level.
Frontend applications must not be responsible for enforcing API rate limits.

62. DRF Throttling
Use Django REST Framework's built-in throttling system by default.
Configure throttling globally through:
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
}

This ensures that APIs are protected by default.
Do not require individual developers to remember to add throttling to every new public endpoint.

63. Environment-Based Rate Limits
Rate limits MUST be configurable through environment variables.
Example:
# API Rate Limiting

RATELIMIT_ANON=60/minute
RATELIMIT_USER=300/minute

# Authentication endpoints

RATELIMIT_AUTH=10/minute

# Sensitive operations

RATELIMIT_SENSITIVE=30/minute

The exact values may be changed per project and environment.
Never hardcode production rate limits when they are expected to vary between environments.

64. Anonymous/Public API Rate Limit
All unauthenticated requests MUST be subject to an anonymous rate limit.
Example:
RATELIMIT_ANON=60/minute

This applies to public endpoints such as:
/api/public/
/api/products/
/api/categories/
/api/health/

where appropriate.
The actual limit must be selected based on the API's expected traffic.

65. Authenticated API Rate Limit
Authenticated users should have a separate rate limit.
Example:
RATELIMIT_USER=300/minute

Authenticated requests should use:
rest_framework.throttling.UserRateThrottle

This allows authenticated users to have a higher limit than anonymous clients.

66. Authentication Rate Limit
Authentication endpoints require stricter throttling.
Examples:
POST /api/auth/token/
POST /api/auth/token/refresh/

The login/token endpoint MUST have a stricter rate limit than normal APIs.
Example:
RATELIMIT_AUTH=10/minute

This protects against:
Brute-force password attempts
Credential stuffing
Automated login attempts
Token abuse
Authentication throttling should be applied explicitly to authentication endpoints when the global throttle is not sufficiently restrictive.

67. Sensitive Endpoint Rate Limiting
Sensitive operations should have stricter limits.
Examples:
Password reset
OTP requests
Email verification
SMS requests
Payment operations
Account recovery
Authentication
Expensive search operations
File processing
External API proxy endpoints

Example:
RATELIMIT_SENSITIVE=30/minute

The actual limit must depend on the business requirements.

68. Custom Throttle Classes
When different endpoints require different limits, create reusable throttle classes.
Recommended location:
common/throttling.py

Example:
from rest_framework.throttling import UserRateThrottle


class AuthRateThrottle(UserRateThrottle):
    scope = "auth"


class SensitiveRateThrottle(UserRateThrottle):
    scope = "sensitive"

Configure the scopes from environment variables.
Example:
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
}


69. Throttle Rates
Configure DRF throttle rates through environment variables.
Example:
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env(
            "RATELIMIT_ANON",
            default="60/minute",
        ),
        "user": env(
            "RATELIMIT_USER",
            default="300/minute",
        ),
        "auth": env(
            "RATELIMIT_AUTH",
            default="10/minute",
        ),
        "sensitive": env(
            "RATELIMIT_SENSITIVE",
            default="30/minute",
        ),
    },
}

The exact implementation may be adapted depending on the selected throttle classes.

70. Redis for Distributed Rate Limiting
For a single-process local development environment, DRF's default cache backend may be sufficient.
For staging and production, when the application runs multiple backend instances, rate limiting MUST use a shared cache.
Recommended:
Redis

Architecture:
Client
   ↓
Nginx / Load Balancer
   ↓
Django Instances
   ↓
Shared Redis

This prevents each application instance from maintaining an independent rate-limit counter.
Example production configuration:
RATELIMIT_CACHE_URL=redis://redis:6379/2

The rate-limit cache should be separate from the Celery result/backend databases when practical.
For example:
Redis DB 0 → Celery broker
Redis DB 1 → Celery result backend
Redis DB 2 → API throttling/cache


71. Cache Configuration
Use a dedicated cache configuration for rate limiting.
Example:
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env(
            "RATELIMIT_CACHE_URL",
            default="redis://localhost:6379/2",
        ),
    },
}

The exact cache backend may be adapted to the deployment environment.
Do not use a local in-memory cache for production rate limiting when multiple backend instances exist.

72. Rate Limit Response
When a client exceeds the configured limit, DRF should return:
HTTP 429 Too Many Requests

The response must follow the project's standard API error structure.
Example:
{
    "success": false,
    "message": "Request rate limit exceeded.",
    "errors": {}
}

The API may also expose the appropriate retry information through response headers where supported.
Do not expose internal implementation details.

73. Rate Limit Key
Rate limiting should distinguish between:
Anonymous requests
Usually based on:
Client IP

Authenticated requests
Prefer:
Authenticated user

rather than only IP address.
This prevents users behind the same NAT/network from unnecessarily sharing authenticated rate limits.

74. Proxy and IP Handling
When determining client IP addresses behind:
Nginx
Load balancers
Reverse proxies
Cloud infrastructure
the application must use a correctly configured trusted proxy setup.
Do not blindly trust arbitrary client-provided headers such as:
X-Forwarded-For

because they can be spoofed.
Proxy configuration must be explicitly defined by the deployment architecture.

75. Health API and Rate Limiting
The health endpoint should also be protected against excessive requests.
However, deployment health checks must not be blocked by an overly restrictive rate limit.
If necessary, give the health endpoint a dedicated throttle scope.
Example:
RATELIMIT_HEALTH=120/minute

or use an internal-only health endpoint for infrastructure checks.
Do not completely disable rate limiting on publicly exposed health endpoints unless there is a documented reason.

76. OpenAPI Documentation
Rate-limited endpoints should document that they may return:
429 Too Many Requests

The OpenAPI schema should document this response for public APIs where appropriate.

77. Rate Limit Tests
Every rate-limited API must have automated tests.
At minimum:
test_api_allows_requests_within_rate_limit
test_api_rejects_requests_after_rate_limit
test_anonymous_user_uses_anonymous_throttle
test_authenticated_user_uses_user_throttle
test_auth_endpoint_uses_stricter_throttle

For sensitive endpoints:
test_sensitive_endpoint_has_stricter_rate_limit

The tests must use isolated test cache configuration.
Tests must not depend on production Redis.

78. Rate Limit Environment Configuration
Add the following to .env.example:
# API Rate Limiting
RATELIMIT_ANON=60/minute
RATELIMIT_USER=300/minute
RATELIMIT_AUTH=10/minute
RATELIMIT_SENSITIVE=30/minute
RATELIMIT_HEALTH=120/minute

# Rate Limit Cache
RATELIMIT_CACHE_URL=redis://localhost:6379/2

Production values may be changed without modifying application code.

79. Rate Limiting and Celery
Rate limiting and Celery are separate concerns.
Celery:
Background processing

Rate limiting:
API request protection

Do not make rate limiting dependent on Celery.
Redis may be shared between the two systems, but separate Redis databases or key namespaces should be used when practical.

80. Rate Limiting and Docker
When production/staging rate limiting uses Redis, the relevant Docker Compose environment must provide Redis or configure an external Redis service.
Example:
docker/staging/docker-compose.yml
docker/production/docker-compose.yml

must provide the configured cache infrastructure when required.
Local development may use:
RATELIMIT_CACHE_URL=redis://localhost:6379/2

or an appropriate local cache backend.

81. Rate Limiting and Makefile
The Makefile may include:
test-rate-limit:
	pytest -k "throttle or rate_limit"

The normal:
make test

must also execute rate-limit tests.

82. Rate Limiting Rules for New APIs
When creating a new API:
The endpoint automatically inherits the global rate limit.
Do not disable throttling without a documented reason.
Authentication endpoints must use stricter limits.
Sensitive endpoints must use stricter limits.
Expensive endpoints should have appropriate limits.
Public APIs must never be unintentionally unlimited.
Tests must verify the expected throttling behavior.

83. Rate Limiting Definition of Done
A rate-limited API is complete when:
Global throttling is enabled.
Anonymous requests are throttled.
Authenticated requests are throttled.
Authentication endpoints have stricter limits.
Sensitive endpoints have appropriate limits.
Rate limits are configurable through .env.
Production uses shared cache infrastructure when horizontally scaled.
HTTP 429 responses use the standard API error structure.
Tests cover rate limiting.
OpenAPI documents 429 where appropriate.
No endpoint unintentionally bypasses throttling.

