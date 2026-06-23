# Hotel Management System — Multi-Tenant ERP / PMS

Production-grade, multi-tenant Hotel Management System. This repository currently
implements **Phase 1 — Foundation** (see `PHASE_01_FOUNDATION.md`): tenancy,
identity, RBAC, properties and audit logging, plus the infrastructure and
frontend scaffolding the later phases build on.

## Tech stack

| Layer        | Technology                                             |
|--------------|--------------------------------------------------------|
| Backend      | Python 3.13, Django 6, Django REST Framework, SimpleJWT |
| Database     | PostgreSQL 16                                           |
| Cache / Queue| Redis, Celery                                          |
| Frontend     | Next.js 15 (App Router), TypeScript, Tailwind v4, shadcn/ui |
| Infra        | Docker, docker-compose, Gunicorn, WhiteNoise           |

## Architecture (Phase 1)

Domain-Driven Design with a clean, layered structure. Every app exposes the same
file set: `models.py`, `serializers.py`, `views.py`, `services.py` (write side),
`selectors.py` (read side), `permissions.py`, `urls.py`, `tests/`.

```
backend/
  config/                 # settings (base/dev/prod), celery, urls, wsgi/asgi
  apps/
    common/               # base models, tenant context, managers, pagination, exceptions
    accounts/             # email-based custom User (identity)
    rbac/                 # Role + RolePermission, permission catalogue, DRF gates
    organizations/        # Organization (tenant) + Membership + tenant middleware
    properties/           # org-scoped Property
    audit/                # append-only AuditLog + capture middleware
frontend/
  src/{app,components/ui,lib,types}
```

### Multi-tenancy model

- **Organization** is the tenant root. Every tenant-scoped row (`TenantScopedModel`)
  carries an `organization` FK and is isolated automatically by a tenant-aware
  manager that reads the active org from request/async context.
- **Membership** joins a `User` to an `Organization` with an RBAC `Role` and an
  optional property-level scope. One user can belong to many organizations.
- The active tenant is resolved per request by `TenantResolverMiddleware` from a
  subdomain, the `X-Org-Slug` header, or an `?org=` query parameter.

### RBAC

Roles are provisioned per organization from system templates (`OWNER`, `ADMIN`,
`MANAGER`, `FRONT_DESK`, `HOUSEKEEPING`, `ACCOUNTANT`, `READ_ONLY`) and map to a
catalogue of permission codes. DRF views declare `required_permissions`; the
`HasOrgPermission` gate enforces them against the caller's membership role.

## Running with Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
# backend  → http://localhost:8000   (API docs at /api/docs/)
# frontend → http://localhost:3000
```

`docker compose` brings up Postgres, Redis, the Django API, a Celery worker, a
Celery beat scheduler and the Next.js app. The backend container runs migrations
and `collectstatic` on start.

## Running locally

### Backend

```bash
cd backend
cp .env.example .env                 # point DATABASE_URL at your Postgres
python -m venv .venv && . .venv/Scripts/activate   # (.venv already present)
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Run the test suite (SQLite, no external services needed):

```bash
DJANGO_ENV=dev DATABASE_URL="sqlite:///test.sqlite3" \
  python manage.py test apps.accounts apps.rbac apps.organizations apps.properties apps.audit
```

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

## Key API endpoints

| Method | Path                                   | Notes                          |
|--------|----------------------------------------|--------------------------------|
| POST   | `/api/auth/token/`                     | Obtain JWT (email + password)  |
| POST   | `/api/auth/token/refresh/`             | Refresh JWT                    |
| POST   | `/api/accounts/auth/register/`         | Self-service registration      |
| GET    | `/api/accounts/me/`                    | Current profile                |
| GET/POST| `/api/organizations/`                 | List my orgs / create one      |
| GET/POST| `/api/organizations/members/`         | Members of active org (tenant header) |
| GET    | `/api/rbac/roles/`, `/api/rbac/permissions/` | Roles & permission catalogue |
| CRUD   | `/api/properties/`                     | Tenant-scoped properties       |
| GET    | `/api/audit/logs/`                     | Audit trail (needs `audit.view`) |
| GET    | `/api/docs/`                           | Swagger UI                     |

Tenant-scoped endpoints require the active organization via the `X-Org-Slug`
header (or subdomain).
