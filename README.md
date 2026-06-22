# ImpactDash — Backend

A Flask REST API backed by MongoDB Atlas, using PyMongo. The backend powers **ImpactDash**, a multi-tenant nonprofit dashboard platform: platform admins manage multiple organizations, and each nonprofit user views and updates their own KPI dashboard. The API follows a strict three-layer architecture: routes handle HTTP, services enforce business rules, and repositories own all database access.

---

## Tech Stack

| Library | Role |
|---------|------|
| **Flask** | HTTP framework and route registration |
| **flask-cors** | Cross-origin requests for the Vite frontend |
| **PyMongo** | MongoDB driver — all DB reads and writes go through repositories |
| **MongoDB Atlas** | Primary database (cloud-hosted) |
| **python-dotenv** | Loads credentials from `.env` so they stay out of version control |
| **PyJWT** | JWT tokens for authenticated nonprofit routes |
| **Werkzeug** | Password hashing (`generate_password_hash` / `check_password_hash`) |
| **fpdf2** | PDF dashboard report generation |

---

## Project Structure

```
backend/
├── run.py                  # Entry point — creates Flask app via create_app()
├── __init__.py             # Application factory; registers blueprints
├── nonprofit_routes.py     # HTTP layer — health, login, nonprofits, import, report
├── auth.py                 # JWT helpers and @require_auth decorator
├── seed_nonprofits.py      # Demo nonprofits, programs, donors, and users
├── postman_tests.json      # Postman collection for API testing
├── .env                    # Local credentials — never committed (see .gitignore)
├── .env.example            # Template — copy to .env and fill in your values
├── db/
│   └── database.py         # MongoClient setup and get_mongo_db() factory
├── repositories/
│   ├── user_repo.py        # users collection
│   ├── nonprofit_repo.py   # nonprofits collection
│   ├── program_repo.py     # programs collection
│   ├── metrics_repo.py     # nonprofit_metrics collection
│   └── donor_repo.py       # donors collection
└── services/
    ├── auth_service.py         # Login and credential validation
    ├── nonprofit_service.py      # RBAC, dashboard aggregation, CRUD
    ├── csv_import_service.py     # CSV parse/import for bulk updates
    └── report_service.py         # PDF report generation
```

---

## Environment Variables

Credentials are stored in a `.env` file that is **never committed to git**.

**Step 1** — copy the example file:
```bash
cp .env.example .env
```

**Step 2** — open `.env` and fill in your values:
```
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<dbname>
JWT_SECRET=your-secret-key-change-in-production
```

| Variable | Required | Description |
|----------|----------|-------------|
| `MONGO_URI` | Yes | MongoDB Atlas connection string |
| `JWT_SECRET` | No | HS256 signing key for JWTs (defaults to a dev secret if omitted) |

The app will raise a clear error on startup if `MONGO_URI` is missing.

### MongoDB Atlas Network Access

When deploying to a cloud host (e.g. Render), you must whitelist the host's IP in **MongoDB Atlas → Network Access**.

- **Development / demo**: Allow Access from Anywhere (`0.0.0.0/0`) — acceptable for course projects with no real user data.
- **Production**: Add only your host's static outbound IP. Using `0.0.0.0/0` in production leaves the cluster exposed to brute-force attempts — the only protection is your Atlas password.

---

## Architecture

### Three-Layer Design

**Routes (`nonprofit_routes.py`)** — HTTP only. Reads request data (JSON body, query params, uploaded files), calls the service, returns JSON or file responses with the correct status code. Contains no business logic and no database access.

**Services (`nonprofit_service.py`, `auth_service.py`, etc.)** — Business rules. Validates inputs, enforces RBAC (platform admin vs nonprofit user), aggregates dashboard data, coordinates CSV import, and triggers PDF generation.

**Repositories (`*_repo.py`)** — Database only. Each repository gets the MongoDB database handle in its `__init__` and exposes clean methods for the service layer to call. No query logic exists anywhere outside these files.

### Authentication and Roles

- `POST /api/login` validates email/password and returns `{ userId, name, email, role, nonprofitId, token }`.
- Protected routes require `Authorization: Bearer <token>` via `@require_auth` in `auth.py`.
- RBAC is enforced in `nonprofit_service.py`:

| Role | Access |
|------|--------|
| `platform_admin` | List/create/update all nonprofits; view any dashboard; import CSV; list users |
| `nonprofit_user` | Read/write only their `nonprofit_id` dashboard (metrics + programs) |

### Integer IDs

MongoDB generates a random `ObjectId` as `_id` by default. This app keeps integer IDs (`user_id`, `nonprofit_id`, `program_id`, etc.) for a stable API contract with the frontend. A `counters` collection tracks the last-used integer per collection and is incremented atomically using `find_one_and_update` with `$inc`.

### Data Model (MongoDB Collections)

| Collection | Purpose |
|------------|---------|
| `users` | Login accounts (`role`, `nonprofit_id`, password hash) |
| `nonprofits` | Organization profile (name, slug, mission, location) |
| `programs` | Programs per nonprofit (status, participants, budget) |
| `nonprofit_metrics` | KPI snapshot per nonprofit (donors, funding, email engagement, computed highlights) |
| `donors` | Individual donor records (name, email, donation amount) |
| `counters` | Auto-increment integer IDs per collection |

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/health` | No | Server liveness check |
| `POST` | `/api/login` | No | Authenticate; returns JWT |
| `GET` | `/api/nonprofits` | Yes | List nonprofits (scoped by role) |
| `POST` | `/api/nonprofits` | Yes | Create nonprofit (platform admin) |
| `GET` | `/api/nonprofits/<id>` | Yes | Get nonprofit profile |
| `PUT` | `/api/nonprofits/<id>` | Yes | Update nonprofit profile |
| `GET` | `/api/nonprofits/<id>/dashboard` | Yes | Full dashboard JSON (metrics, programs, donors, insights) |
| `PUT` | `/api/nonprofits/<id>/metrics` | Yes | Update KPI fields |
| `GET` | `/api/nonprofits/<id>/programs` | Yes | List programs |
| `POST` | `/api/nonprofits/<id>/programs` | Yes | Create program |
| `PUT` | `/api/nonprofits/<id>/programs/<program_id>` | Yes | Update program |
| `DELETE` | `/api/nonprofits/<id>/programs/<program_id>` | Yes | Delete program |
| `GET` | `/api/nonprofits/<id>/report` | Yes | Download PDF dashboard report |
| `GET` | `/api/users` | Yes | List users (platform admin) |
| `GET` | `/api/nonprofits/import/template` | Yes | Download CSV import template |
| `POST` | `/api/nonprofits/import` | Yes | Upload CSV (`?mode=auto\|update\|create`) |

---

## Key Design Decisions

### Dashboard Aggregation

`GET /api/nonprofits/<id>/dashboard` combines nonprofit profile, KPI metrics, program list, top donors, and computed **insights** (biggest donor, highest donation, email open trend) in a single response for the frontend charts and PDF export.

### CSV Import

Platform admins upload a CSV with one `nonprofit` row (profile + KPIs + email opens), optional `program` rows, and optional `donor` rows. Import modes:

- **auto** — match existing org by slug or name; update if found, create if not
- **update** — require `nonprofitId` query param; update that org only
- **create** — force new org; error if slug/name already exists

Programs and donors **merge** by name (and email for donors): matching records update, new records insert, omitted records are kept.

### PDF Reports

`GET /api/nonprofits/<id>/report` generates a PDF via fpdf2 with organization profile, KPI summary, donor highlights, email engagement, funding breakdown, and full program list. Report content reflects live data including CSV-imported donors and metrics.

### Password Hashing

Passwords are never stored in plain text. On registration or seed, the password is run through Werkzeug's `generate_password_hash` before being saved. On login, `check_password_hash` compares the submitted password against the stored hash.

### Soft-Deleted Users

Users can be soft-deleted (`is_deleted`, `deleted_at`). Soft-deleted accounts cannot log in. Documents remain in the database for audit purposes.

---

## Seed Data

Load demo nonprofits, programs, donors, metrics, and users:

```bash
cd bank_app/backend
uv run python seed_nonprofits.py
```

| Email | Role | Password |
|-------|------|----------|
| `admin@platform.org` | platform_admin | `demo1234` |
| `sarah@rivervalley.org` | nonprofit_user (River Valley Food Bank) | `demo1234` |
| `marcus@brightfutures.org` | nonprofit_user (Bright Futures Youth Mentoring) | `demo1234` |
| `elena@pawshearts.org` | nonprofit_user (Paws & Hearts Animal Rescue) | `demo1234` |

---

## Running Locally

```bash
cd bank_app/backend
cp .env.example .env        # then fill in MONGO_URI (and optionally JWT_SECRET)
uv sync                     # install dependencies
uv run python seed_nonprofits.py   # optional: load demo data
uv run python run.py        # starts at http://127.0.0.1:5000
```

Visit `http://127.0.0.1:5000/api/health` to confirm the server is up.
