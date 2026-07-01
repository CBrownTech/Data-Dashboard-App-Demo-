# ImpactDash — Backend

A Flask REST API with a pluggable data layer: it runs on **Google BigQuery** for production/cloud use, or on a local **SQLite** file for zero-setup demos and development — selected with the `DB_BACKEND` env var. The backend powers **ImpactDash**, a multi-tenant nonprofit dashboard platform: platform admins manage multiple organizations, and each nonprofit user views and updates their own KPI dashboard. The API follows a strict three-layer architecture: routes handle HTTP, services enforce business rules, and repositories own all database access.

> **Just want to run the demo?** Copy `.env.example` to `.env` (it defaults to `DB_BACKEND=sqlite`), then `uv sync && uv run python seed_nonprofits.py && uv run python run.py`. No cloud account or credentials required.

---

## Tech Stack

| Library | Role |
|---------|------|
| **Flask** | HTTP framework and route registration |
| **flask-cors** | Cross-origin requests for the Vite frontend |
| **google-cloud-bigquery** | BigQuery client — used when `DB_BACKEND=bigquery` (production path) |
| **Google BigQuery** | Cloud database (data warehouse) for production/shared use |
| **sqlite3** (stdlib) | Local file database — used when `DB_BACKEND=sqlite` (default; demos/dev) |
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
├── setup_bigquery.py       # Creates the BigQuery dataset and tables (BigQuery mode only; --drop to recreate)
├── postman_tests.json      # Postman collection for API testing
├── local_demo.db           # Local SQLite data file (auto-created in sqlite mode; gitignored)
├── .env                    # Local credentials — never committed (see .gitignore)
├── .env.example            # Template — copy to .env and fill in your values
├── db/
│   ├── database.py         # Backend dispatcher + query/insert/update/upsert/next_id helpers
│   ├── params.py           # Backend-neutral query parameter (param / array_param)
│   ├── bigquery_backend.py # BigQuery implementation (INSERT/UPDATE/MERGE DML)
│   └── sqlite_backend.py   # Local SQLite implementation (auto-creates schema)
├── repositories/
│   ├── user_repo.py        # users table
│   ├── nonprofit_repo.py   # nonprofits table
│   ├── program_repo.py     # programs table
│   ├── metrics_repo.py     # nonprofit_metrics + nonprofit_weekly_metrics tables
│   └── donor_repo.py       # donors table
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

**Step 2** — open `.env` and choose a backend. The default runs the local demo with no cloud setup:
```
DB_BACKEND=sqlite
JWT_SECRET=your-secret-key-change-in-production
```

To use BigQuery instead, set `DB_BACKEND=bigquery` and provide the BigQuery settings:
```
DB_BACKEND=bigquery
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
BIGQUERY_PROJECT=your-gcp-project-id
BIGQUERY_DATASET=bank_db
JWT_SECRET=your-secret-key-change-in-production
```

| Variable | Required | Description |
|----------|----------|-------------|
| `DB_BACKEND` | No | `sqlite` (default, local demo) or `bigquery` |
| `SQLITE_DB_PATH` | No | SQLite file path when `DB_BACKEND=sqlite` (defaults to `backend/local_demo.db`) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Only for BigQuery | Absolute path to a GCP service-account JSON key |
| `BIGQUERY_PROJECT` | Only for BigQuery | GCP project id that owns the dataset |
| `BIGQUERY_DATASET` | No | Dataset name holding the app tables (defaults to `bank_db`) |
| `JWT_SECRET` | No | HS256 signing key for JWTs (defaults to a dev secret if omitted) |

When `DB_BACKEND=bigquery`, the app raises a clear error on startup if `BIGQUERY_PROJECT` is missing.

### Database Backends

The repositories are written once against the dispatcher in `db/database.py`; `DB_BACKEND` decides which implementation runs. Both expose the same operations, so switching backends requires no code changes.

**`sqlite` (default)** — Stores data in a local file (`backend/local_demo.db`, gitignored), auto-creating the schema on first use. No credentials, no network. Ideal for demos and local development. Not intended for multi-user or production traffic.

**`bigquery`** — The production path. Authentication uses a **service account** rather than IP allowlisting:

1. In **GCP → IAM & Admin → Service Accounts**, create a service account and grant it **BigQuery Data Editor** (read/write rows) and **BigQuery Job User** (run queries) on the project.
2. Create a JSON key for that account and download it; point `GOOGLE_APPLICATION_CREDENTIALS` at its absolute path.
3. Create the dataset and tables once with `uv run python setup_bigquery.py`.

Prefer workload identity / attached service accounts over long-lived JSON keys in production, and scope the account to only the dataset it needs.

---

## Architecture

### Three-Layer Design

**Routes (`nonprofit_routes.py`)** — HTTP only. Reads request data (JSON body, query params, uploaded files), calls the service, returns JSON or file responses with the correct status code. Contains no business logic and no database access.

**Services (`nonprofit_service.py`, `auth_service.py`, etc.)** — Business rules. Validates inputs, enforces RBAC (platform admin vs nonprofit user), aggregates dashboard data, coordinates CSV import, and triggers PDF generation.

**Repositories (`*_repo.py`)** — Database only. Each repository builds parameterized SQL and calls the shared helpers in `db/database.py` (`query`, `query_one`, `insert_row`, `update_row`, `upsert`, `dml`, `next_id`), which dispatch to the active backend (BigQuery or SQLite). Reads return plain dicts and writes go through `INSERT`/`UPDATE`/`MERGE` (BigQuery) or their SQLite equivalents, so no query logic exists anywhere outside these files.

### Authentication and Roles

- `POST /api/login` validates email/password and returns `{ userId, name, email, role, nonprofitId, token }`.
- Protected routes require `Authorization: Bearer <token>` via `@require_auth` in `auth.py`.
- RBAC is enforced in `nonprofit_service.py`:

| Role | Access |
|------|--------|
| `platform_admin` | List/create/update all nonprofits; view any dashboard; import CSV; list users |
| `nonprofit_user` | Read/write only their `nonprofit_id` dashboard (metrics + programs) |

### Integer IDs

BigQuery has no auto-increment column. This app keeps integer IDs (`user_id`, `nonprofit_id`, `program_id`, etc.) for a stable API contract with the frontend, generated by `next_id()` in `db/database.py` as `COALESCE(MAX(id), 0) + 1`. This preserves the integer-ID contract without a separate counters table. Note: `MAX+1` is not safe under concurrent writers — it is correct for this demo's single-writer load, not high-concurrency production writes.

### Why DML instead of the streaming API

Rows written with BigQuery's streaming insert API sit in a streaming buffer and cannot be `UPDATE`-d or `DELETE`-d for up to ~90 minutes. This app frequently inserts a row and mutates it moments later (e.g. create a nonprofit, then upsert its metrics), so every write uses an `INSERT`/`UPDATE`/`MERGE` DML statement, whose rows are immediately queryable and mutable.

### Data Model (BigQuery Tables)

| Table | Purpose |
|-------|---------|
| `users` | Login accounts (`role`, `nonprofit_id`, password hash) |
| `nonprofits` | Organization profile (name, slug, mission, location) |
| `programs` | Programs per nonprofit (status, participants, budget) |
| `nonprofit_metrics` | KPI snapshot per nonprofit (donors, funding, email engagement, computed highlights) |
| `nonprofit_weekly_metrics` | Weekly KPI snapshots per nonprofit (6-week history for trends and WoW comparisons) |
| `donors` | Individual donor records (name, email, donation amount) |

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

BigQuery mode only — create the dataset and tables first (idempotent; skip in SQLite mode, where the schema is auto-created):

```bash
cd bank_app/backend
uv run python setup_bigquery.py
```

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
cp .env.example .env        # defaults to DB_BACKEND=sqlite (local demo, no cloud setup)
uv sync                     # install dependencies
uv run python seed_nonprofits.py   # load demo data (auto-creates the SQLite schema)
uv run python run.py        # starts at http://127.0.0.1:5000

# BigQuery mode: set DB_BACKEND=bigquery (+ BIGQUERY_PROJECT, GOOGLE_APPLICATION_CREDENTIALS)
# in .env, then run `uv run python setup_bigquery.py` once before seeding.
```

Visit `http://127.0.0.1:5000/api/health` to confirm the server is up.
