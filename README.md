# P05 – Waiting for the Shuttle

A campus shuttle information and management platform for Lovely Professional University, developed for INT335 – Design Thinking.

The project is being built in phases. The current implementation includes the React/Vite and FastAPI scaffold, relational database models and Alembic migrations, student/administrator authentication, transport and operations APIs, and the Phase 8 data-backed student and administrator dashboard workflows. Frontend pages call the versioned API; there is no fabricated campus operation data, live GPS feed, or arrival prediction.

## Project structure

```text
backend/
  app/
    api/v1/
    core/       # Runtime settings and shared enums
    db/         # SQLAlchemy base and session factory
    models/     # SQLAlchemy 2.0 models
    schemas/    # Pydantic request/response schemas
    services/
    main.py
  alembic/      # Versioned database migrations
  tests/
  requirements.txt
  .env.example
frontend/
  public/
  src/
    assets/
    components/
    context/
    hooks/
    layouts/
    pages/
    services/
    styles/
  package.json
  .env.example
```

## Requirements

- Python 3.11+
- Node.js 20.19+ (or 22.12+)
- PostgreSQL 13+ (local or managed)

## Run locally

### Backend

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
# Set DATABASE_URL in backend\.env to your PostgreSQL connection string.
uvicorn app.main:app --reload
```

The initial health endpoint is available at `http://127.0.0.1:8000/health`. FastAPI's Swagger UI is at `http://127.0.0.1:8000/docs`.

### Database

The initial normalized schema contains:

- `users`, `stops`, `routes`, and the ordered many-to-many `route_stops` relation.
- `shuttles` and append-style `shuttle_status` updates.
- `announcements` and student `feedback`, including an optional 1–5 feedback rating.

IDs are UUIDs. Tables have timezone-aware creation/update timestamps. The database enforces unique user emails, stop names, route codes and vehicle codes; valid user, feedback and shuttle-status values; positive capacities, route durations and stop positions; and unique stop/order assignments within each route. Routes derive their starting point and destination from the first and last ordered route stops.

Configure `DATABASE_URL` in the untracked `backend\.env` file using your own PostgreSQL credentials, for example `postgresql+psycopg://<user>:<url-encoded-password>@localhost:5432/p05_shuttle`. Do not put credentials in source control. Create the empty database with your PostgreSQL tools, then from `backend\` apply and verify the schema:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe check
```

`alembic check` should report `No new upgrade operations detected.` Related route-stop rows are removed with their route; deleting a stop referenced by a route or a shuttle with status history is restricted. Deleting a user with submitted feedback is restricted to preserve the feedback record; optional announcement/status author references are set to null. Prefer deactivation for operational records.

### Frontend

In another PowerShell terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Vite prints the local frontend URL when the development server starts. Set `VITE_API_BASE_URL` in `frontend/.env` to the backend API URL (including `/api/v1`). `VITE_CSRF_COOKIE_NAME` should match `CSRF_COOKIE_NAME` in `backend\.env`. The frontend includes public landing, student login and registration, and admin login pages; protected student and admin workspaces use the existing cookie-authenticated session. Student pages cover routes, stops, shuttle status, announcements, feedback, and profile; administrator pages manage transport records and review feedback. Management writes remain protected by backend role checks.

The shared Axios client is in `frontend\src\services\api.js`, with endpoint wrappers in `frontend\src\services\auth.js`, `stops.js`, `routes.js`, `shuttles.js`, `shuttleStatus.js`, `announcements.js`, and `feedback.js`. The frontend uses the real API response shapes, including paginated `{items, total, skip, limit}` lists. Start both backend and frontend to sign in and use data-backed pages.

### Authentication

The browser session uses a signed JWT in an `HttpOnly` cookie; the JWT is not returned to JavaScript or stored in `localStorage`. A separate CSRF cookie is sent in `X-CSRF-Token` for unsafe requests, and the backend validates request origins against `CORS_ORIGINS`. Tokens expire after 30 minutes by default. Student registration always creates a `STUDENT`; it rejects client-supplied role fields.

Generate a signing secret locally and place it in `backend\.env` as `JWT_SECRET_KEY`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

In production, use HTTPS and set `AUTH_COOKIE_SECURE=true`. If the frontend and backend use different sites, set `AUTH_COOKIE_SAMESITE=none`, keep `AUTH_COOKIE_SECURE=true`, and configure exact frontend origins in `CORS_ORIGINS`. Set `VITE_CSRF_COOKIE_NAME` to the same value as `CSRF_COOKIE_NAME` if you customize the cookie name.

Create the initial administrator only from a trusted backend environment, after applying migrations. The command prompts for the email, name, and password and stores only an Argon2 hash:

```powershell
cd backend
python -m app.cli create-admin
```

Authentication endpoints are `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/admin/login`, `GET /api/v1/auth/me`, `GET /api/v1/auth/admin/me`, and `POST /api/v1/auth/logout`. The admin profile endpoint returns `403` for students.

### Stops, routes, and shuttles APIs

All management APIs require an authenticated administrator; students can list and retrieve active stops, routes, and shuttles. Student lists always filter out inactive records. List responses use `{items, total, skip, limit}` and accept `skip`/`limit` (maximum 100), `q`, and `is_active` filters.

- Stops: `GET /api/v1/stops`, `GET /api/v1/stops/{stop_id}`, `POST /api/v1/stops`, `PATCH /api/v1/stops/{stop_id}`.
- Routes: `GET /api/v1/routes`, `GET /api/v1/routes/{route_id}`, `POST /api/v1/routes`, `PATCH /api/v1/routes/{route_id}`.
- Route stop ordering: create a route with ordered `stop_ids`; add with `POST /api/v1/routes/{route_id}/stops` and optional 1-based `position`; reorder with `PUT /api/v1/routes/{route_id}/stops/order`; remove with `DELETE /api/v1/routes/{route_id}/stops/{stop_id}`.
- Shuttles: `GET /api/v1/shuttles`, `GET /api/v1/shuttles/{shuttle_id}`, `POST /api/v1/shuttles`, `PATCH /api/v1/shuttles/{shuttle_id}`. A shuttle can be assigned to an active route with `route_id`; send `null` to unassign.

Use Swagger UI at `http://127.0.0.1:8000/docs` to try the APIs. First provision an admin as above, then call `POST /api/v1/auth/admin/login` with its email/password. Swagger's same-origin session cookie is retained for subsequent requests. Create test-only stops, then a route using their returned IDs, followed by a shuttle assigned to that route. Duplicate names/codes return `409`; missing IDs return `404`; invalid route-stop order returns `422`. Deactivation uses `PATCH` with `{"is_active": false}`. The API does not seed routes or vehicles.

### Shuttle status, announcements, and feedback APIs

All endpoints below require the existing authenticated HttpOnly-cookie session. Students can read current status and published announcements, submit feedback, and read their own feedback. Administrator-only operations require the admin role. Cross-origin unsafe requests must include the CSRF token header described above. List endpoints return `{items, total, skip, limit}` and accept `skip` (default `0`) and `limit` (default `50`, maximum `100`).

Status values are `ON_TIME`, `DELAYED`, `UNAVAILABLE`, and `NOT_UPDATED`. Shuttle availability is a separate `shuttle.is_active` field. The current-status APIs return `NOT_UPDATED` with a null update timestamp when no status record exists. Status updates are administrator-entered records; they do not represent GPS data or predicted arrival times.

| Method and endpoint | Access | Purpose |
| --- | --- | --- |
| `GET /api/v1/shuttle-status` | Student/admin | Current status for each visible shuttle, paginated. |
| `GET /api/v1/shuttle-status/route/{route_id}` | Student/admin | Current status for shuttles assigned to a route. |
| `GET /api/v1/shuttle-status/shuttle/{shuttle_id}` | Student/admin | Current status plus public shuttle details. |
| `GET /api/v1/shuttle-status/shuttle/{shuttle_id}/history` | Student/admin | Status updates for one shuttle, newest first. |
| `POST /api/v1/shuttle-status` | Admin | Append a manual status update; returns `201`. |
| `GET /api/v1/announcements` | Student/admin | Current published announcements for students; admins can also see drafts and scheduled/expired entries. Sorted by publication/start date, newest first. |
| `GET /api/v1/announcements/{announcement_id}` | Student/admin | Retrieve one visible announcement. |
| `POST /api/v1/announcements` | Admin | Create an announcement; returns `201`. |
| `PATCH /api/v1/announcements/{announcement_id}` | Admin | Update provided announcement fields. |
| `DELETE /api/v1/announcements/{announcement_id}` | Admin | Delete an announcement; returns `204`. |
| `POST /api/v1/feedback` | Student | Submit feedback; returns `201`. |
| `GET /api/v1/feedback/mine` | Authenticated user | Retrieve the current user's feedback and review status. |
| `GET /api/v1/feedback` | Admin | Review all feedback; optional `status` and `category` filters. |
| `GET /api/v1/feedback/{feedback_id}` | Owner/admin | Retrieve a feedback record; students cannot access other users' records. |
| `PATCH /api/v1/feedback/{feedback_id}/status` | Admin | Set review status and optional response. |

Example request bodies:

`POST /api/v1/shuttle-status`:

```json
{
  "shuttle_id": "00000000-0000-0000-0000-000000000001",
  "status": "DELAYED",
  "message": "Service update entered by transport staff"
}
```

`POST /api/v1/announcements`:

```json
{
  "title": "Temporary stop change",
  "body": "The shuttle will use the north entrance today.",
  "is_published": true,
  "starts_at": "2026-11-18T08:00:00Z",
  "ends_at": "2026-11-18T18:00:00Z"
}
```

`PATCH /api/v1/announcements/{announcement_id}` (send only fields to change):

```json
{
  "is_published": false,
  "ends_at": null
}
```

`POST /api/v1/feedback`:

```json
{
  "category": "DELAY",
  "message": "The shuttle has not arrived at the listed stop.",
  "rating": 3,
  "route_id": "00000000-0000-0000-0000-000000000002",
  "stop_id": "00000000-0000-0000-0000-000000000003",
  "shuttle_id": "00000000-0000-0000-0000-000000000004"
}
```

`PATCH /api/v1/feedback/{feedback_id}/status`:

```json
{
  "status": "RESOLVED",
  "admin_response": "The route information has been corrected."
}
```

Feedback categories are `DELAY`, `OVERCROWDING`, `INCORRECT_STOP`, `SUGGESTION`, and `OTHER`; `rating` is optional and must be from 1 to 5. Feedback starts with status `PENDING`; administrators can set it to `IN_REVIEW`, `RESOLVED`, or `DISMISSED` and attach an optional `admin_response`.

Successful reads and updates return JSON matching their resource schema; paginated reads use the page shape shown above. A successful status update includes its recorded `created_at`/`updated_at` timestamps and shuttle details. Typical errors are `401` for no valid session, `403` for a role or CSRF violation, `404` for a missing or inaccessible resource, and `422` for invalid fields, enum values, date ranges, pagination, or rating. Invalid optional route/stop/shuttle references in feedback return `404`. FastAPI provides the complete request/response schemas and error details at `/docs`.

Example successful response shapes:

```json
{
  "items": [
    {
      "shuttle": {
        "id": "00000000-0000-0000-0000-000000000004",
        "vehicle_code": "CAMPUS-01",
        "capacity": 24,
        "route_id": "00000000-0000-0000-0000-000000000002",
        "is_active": true
      },
      "status_update_id": null,
      "status": "NOT_UPDATED",
      "message": null,
      "last_updated_at": null
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

```json
{
  "id": "00000000-0000-0000-0000-000000000005",
  "title": "Temporary stop change",
  "body": "The shuttle will use the north entrance today.",
  "is_published": true,
  "starts_at": "2026-11-18T08:00:00Z",
  "ends_at": "2026-11-18T18:00:00Z",
  "published_by_id": "00000000-0000-0000-0000-000000000006",
  "created_at": "2026-11-18T07:55:00Z",
  "updated_at": "2026-11-18T07:55:00Z"
}
```

```json
{
  "id": "00000000-0000-0000-0000-000000000007",
  "user_id": "00000000-0000-0000-0000-000000000008",
  "category": "DELAY",
  "message": "The shuttle has not arrived at the listed stop.",
  "rating": 3,
  "status": "PENDING",
  "admin_response": null,
  "route_id": "00000000-0000-0000-0000-000000000002",
  "stop_id": "00000000-0000-0000-0000-000000000003",
  "shuttle_id": "00000000-0000-0000-0000-000000000004",
  "reviewed_by_id": null,
  "created_at": "2026-11-18T08:05:00Z",
  "updated_at": "2026-11-18T08:05:00Z"
}
```

Example error responses:

```json
{"detail": "Authentication required."}
```

```json
{
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["body", "rating"],
      "msg": "Input should be greater than or equal to 1",
      "input": 6,
      "ctx": {"ge": 1}
    }
  ]
}
```

## Configuration

Copy each `.env.example` to `.env` for local development. Set `DATABASE_URL` and `JWT_SECRET_KEY` in `backend\.env` before running database-backed code. Never commit `.env` files or production secrets. Deployment instructions will be added with the corresponding implementation phase.

## Validation

```powershell
# Backend, from backend\
pytest

# Frontend, from frontend\
npm run build
```
