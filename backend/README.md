# ImpactDash — Backend

A Flask REST API with a pluggable data layer: it runs on **Google BigQuery** for production/cloud use, or on a local **SQLite** file for zero-setup demos and development — selected with the `DB_BACKEND` env var. The backend powers **ImpactDash**, a multi-tenant nonprofit dashboard platform: platform admins manage multiple organizations and their members, nonprofit owners manage their org’s member roster, and each nonprofit user views their own KPI dashboard. The API follows a strict three-layer architecture: routes handle HTTP, services enforce business rules, and repositories own all database access.

> **Just want to run the demo?** Copy `.env.example` to `.env` (it defaults to `DB_BACKEND=sqlite`), then `uv sync && uv run python seed_nonprofits.py && uv run python run.py`. No cloud account or credentials required. See [Running Locally](#running-locally).

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
├── nonprofit_routes.py     # HTTP layer — health, login, nonprofits, members, import, report
├── auth.py                 # JWT helpers and @require_auth decorator
├── seed_nonprofits.py      # Demo nonprofits, programs, donors, users; --backfill-only for weekly snapshots
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

**Security:** Never put real credentials in `.env.example` — use placeholders only. The service-account JSON key and real `JWT_SECRET` value belong in gitignored locations on each machine (`GOOGLE_APPLICATION_CREDENTIALS` should point outside the repo). If a key is ever committed, disable/rotate it immediately in **GCP → IAM & Admin → Service Accounts** and rewrite git history before force-pushing.

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

**Services (`nonprofit_service.py`, `auth_service.py`, etc.)** — Business rules. Validates inputs, enforces RBAC (platform admin, nonprofit owner, nonprofit user), aggregates dashboard data, coordinates org member management, CSV import, and triggers PDF generation.

**Repositories (`*_repo.py`)** — Database only. Each repository builds parameterized SQL and calls the shared helpers in `db/database.py` (`query`, `query_one`, `insert_row`, `update_row`, `upsert`, `dml`, `next_id`), which dispatch to the active backend (BigQuery or SQLite). Reads return plain dicts and writes go through `INSERT`/`UPDATE`/`MERGE` (BigQuery) or their SQLite equivalents, so no query logic exists anywhere outside these files.

### Authentication and Roles

- `POST /api/login` validates email/password and returns `{ userId, name, email, role, nonprofitId, token }`.
- Protected routes require `Authorization: Bearer <token>` via `@require_auth` in `auth.py`.
- RBAC is enforced in `nonprofit_service.py`:

| Role | Access |
|------|--------|
| `platform_admin` | List/create/update all nonprofits; view any dashboard; manage org members; import CSV; list users; edit metrics |
| `nonprofit_owner` | Read/write their org dashboard (programs); view and manage org members for their `nonprofit_id` |
| `nonprofit_user` | Read/write their org dashboard (programs); view org members for their `nonprofit_id` (read-only) |

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
| `GET` | `/api/nonprofits/public` | No | Public list of active nonprofits (id, name, location) |
| `GET` | `/api/nonprofits` | Yes | List nonprofits (scoped by role) |
| `POST` | `/api/nonprofits` | Yes | Create nonprofit (platform admin) |
| `GET` | `/api/nonprofits/<id>` | Yes | Get nonprofit profile |
| `PUT` | `/api/nonprofits/<id>` | Yes | Update nonprofit profile |
| `GET` | `/api/nonprofits/<id>/dashboard` | Yes | Full dashboard JSON (metrics, programs, donors, insights, category tabs, weeklyMetrics). Optional query: `weekStart` (ISO Monday date) to view a specific week |
| `PUT` | `/api/nonprofits/<id>/metrics` | Yes | Update KPI fields (platform admin only) |
| `GET` | `/api/nonprofits/<id>/programs` | Yes | List programs |
| `POST` | `/api/nonprofits/<id>/programs` | Yes | Create program |
| `PUT` | `/api/nonprofits/<id>/programs/<program_id>` | Yes | Update program |
| `DELETE` | `/api/nonprofits/<id>/programs/<program_id>` | Yes | Delete program |
| `GET` | `/api/nonprofits/<id>/members` | Yes | List org members (admin, owner, or member of that org) |
| `POST` | `/api/nonprofits/<id>/members` | Yes | Add org member (platform admin or org owner) |
| `PUT` | `/api/nonprofits/<id>/members/<user_id>` | Yes | Update member name/role (platform admin or org owner) |
| `DELETE` | `/api/nonprofits/<id>/members/<user_id>` | Yes | Remove org member (platform admin or org owner) |
| `GET` | `/api/nonprofits/<id>/report` | Yes | Download PDF dashboard report. Optional query: `weekStart` (ISO Monday date) for that week’s metrics and **Week of …** label |
| `GET` | `/api/users` | Yes | List users (platform admin) |
| `GET` | `/api/nonprofits/import/template` | Yes | Download CSV import template |
| `POST` | `/api/nonprofits/import` | Yes | Upload CSV (`?mode=auto\|update\|create`) |

---

## Key Design Decisions

### Dashboard Aggregation

`GET /api/nonprofits/<id>/dashboard` combines nonprofit profile, KPI metrics, program list, top donors, computed **insights** (biggest donor, highest donation, email open trend), **category tabs** (email, P2P, call time, donors), and **weeklyMetrics** in a single response.

Optional **`weekStart`** query parameter (ISO date, must be a Monday) selects which weekly snapshot to display. When weekly history exists, category stats, summary cards, and comparisons reflect the selected week vs its immediately prior week. Invalid or missing snapshots return `400`. Omit `weekStart` to default to the most recent week. Weeks are **Monday–Sunday**.

When weekly snapshots exist, the dashboard response sets top-level `viewMode: "weekly"` and overlays the selected week onto `categories`, `summary`, and `insights`. Aggregate `metrics.fundingGoal` is retained; weekly `fundingRaised` and email-open fields come from the selected snapshot. Without weekly history, `viewMode` is `"aggregate"`.

The dashboard **week picker** and **Weekly Performance** section require rows in `nonprofit_weekly_metrics`. Full seed (`seed_nonprofits.py`) creates 6 weeks per org. Orgs created via CSV import or an older database may have no weekly snapshots until backfilled:

```bash
cd impactdash_app/backend
uv run python seed_nonprofits.py --backfill-only
```

The `weeklyMetrics` object includes:

- `selectedWeekStart` — active week filter (defaults to newest snapshot)
- `availableWeeks` — picker options with `weekStart`, `weekEnd`, `label`, and `reportLabel` (e.g. **Week of Jun 22 – Jun 28, 2026**)
- `reportingWeek` / `priorWeek` — date labels for the selected and comparison weeks
- `history` — last 6 weekly snapshots (email opens, P2P volume, call hours, donations, etc.)
- `comparisons` — week-over-week change, percent, and trend (`up` / `down` / `flat`) per metric
- `summaries` — auto-generated narrative bullets used in PDF executive summaries

### CSV Import

Platform admins upload a CSV with one `nonprofit` row (profile + KPIs + email opens), optional `program` rows, and optional `donor` rows. Import modes:

- **auto** — match existing org by slug or name; update if found, create if not
- **update** — require `nonprofitId` query param; update that org only
- **create** — force new org; error if slug/name already exists

Programs and donors **merge** by name (and email for donors): matching records update, new records insert, omitted records are kept.

### PDF Reports

`GET /api/nonprofits/<id>/report` generates a PDF via fpdf2. Pass the same optional **`weekStart`** query param as the dashboard so the report matches the selected week in the UI.

- Organization profile and KPI summary
- **Week label** — bold **Week of …** line under the org title when weekly data is available
- **Reporting period** — selected week and prior week using `reportLabel`
- **Executive summary** — narrative bullets describing increases and decreases across categories (week-over-week deltas use ASCII `->` in PDF text)
- **Weekly trend table** — last 6 weeks of email opens, P2P messages, call hours, and donations
- **Category detail** — email, P2P texting, call time, donors/channels, funding, and volunteers (with week-over-week deltas)
- Full program list

When `weekStart` is set, the download filename is `nonprofit-dashboard-report-{weekStart}.pdf`; otherwise `nonprofit-dashboard-report.pdf`.

**PDF text encoding:** Reports use Helvetica core fonts (Latin-1). `report_service._safe()` normalizes Unicode punctuation — en/em dashes, arrows, ellipsis — to ASCII before rendering so labels like **Week of Jun 22 - Jun 28, 2026** do not appear as `?` in the PDF. The web UI may still show typographic en-dashes in JSON labels.

Report content reflects live data including CSV-imported donors, metrics, and seeded weekly history.

### Password Hashing

Passwords are never stored in plain text. On registration or seed, the password is run through Werkzeug's `generate_password_hash` before being saved. On login, `check_password_hash` compares the submitted password against the stored hash.

### Soft-Deleted Users

Users can be soft-deleted (`is_deleted`, `deleted_at`). Soft-deleted accounts cannot log in. Documents remain in the database for audit purposes.

### Organization Members

Each nonprofit has a roster of users stored in the `users` table (`nonprofit_id`, `role`). Org-scoped roles are `nonprofit_owner` and `nonprofit_user`.

- **List** — `GET /api/nonprofits/<id>/members` requires auth; caller must be platform admin or belong to that org.
- **Manage** — create, update role, and remove via POST/PUT/DELETE; allowed for platform admin and the org’s `nonprofit_owner`. Owners cannot demote or remove themselves.
- **Member payload** — `{ userId, name, email, role }` where `role` is `nonprofit_owner` or `nonprofit_user`.

Re-running `seed_nonprofits.py` re-links demo owners and members to the newly created nonprofit IDs and soft-deletes retired demo emails.

---

## Seed Data

BigQuery mode only — create the dataset and tables first (idempotent; skip this in SQLite mode, where the schema is auto-created):

```bash
cd impactdash_app/backend
uv run python setup_bigquery.py
```

Load demo nonprofits, programs, donors, metrics, weekly snapshots, and users (**destructive** — truncates and recreates the demo data tables; the `users` table is reconciled by email rather than wiped):

```bash
cd impactdash_app/backend
uv run python seed_nonprofits.py
```

To add weekly snapshots for existing orgs **without** wiping data (enables the dashboard week picker):

```bash
uv run python seed_nonprofits.py --backfill-only
```

The backfill reads each org’s current aggregate metrics from `nonprofit_metrics`, generates 6 weeks of history, and skips orgs that already have weekly rows.

After re-seeding or backfilling, restart the backend if it is already running. Sign out and sign back in after a full re-seed so JWT `nonprofitId` matches the new org IDs.

| Email | Role | Password |
|-------|------|----------|
| `admin@platform.org` | platform_admin | `demo1234` |
| `sarah@rivervalley.org` | nonprofit_owner (River Valley Food Bank) | `demo1234` |
| `james.ortiz@rivervalley.org` | nonprofit_user (River Valley Food Bank) | `demo1234` |
| `marcus@brightfutures.org` | nonprofit_owner (Bright Futures Youth Mentoring) | `demo1234` |
| `aisha.patel@brightfutures.org` | nonprofit_user (Bright Futures Youth Mentoring) | `demo1234` |
| `elena@pawshearts.org` | nonprofit_owner (Paws & Hearts Animal Rescue) | `demo1234` |
| `tom.nguyen@pawshearts.org` | nonprofit_user (Paws & Hearts Animal Rescue) | `demo1234` |
| `lisa.park@pawshearts.org` | nonprofit_user (Paws & Hearts Animal Rescue) | `demo1234` |

**Organization members and search in the UI**

| Page | Who | What |
|------|-----|------|
| **Nonprofits** | Platform admin | Browse all orgs with search (name, mission, location), location filter, and active/inactive status filter; open an org to edit profile and manage members |
| **Nonprofit detail** (`/nonprofits/<id>`) | Platform admin | Organization members panel — search by name/email, filter by role (Owner/Member), add/edit/remove members |
| **Organization** | `nonprofit_owner` | Same members panel for their linked org only — full member management |
| **Organization** | `nonprofit_user` | Same members panel — read-only list with search and role filter |

The **About** page shows platform stats only; it does not include member management.

The **Dashboard** page includes a **Week** dropdown (all authenticated roles) populated from `weeklyMetrics.availableWeeks`, a Weekly Performance section with WoW chips, and a PDF download that passes the selected `weekStart`.

After re-seeding, sign out and sign back in so JWT/session `nonprofitId` matches the new org IDs.

---

## Running Locally

**Local demo (default — SQLite, no cloud setup):**

```bash
cd impactdash_app/backend
cp .env.example .env        # defaults to DB_BACKEND=sqlite
uv sync                     # install dependencies
uv run python seed_nonprofits.py   # load demo data (auto-creates the SQLite schema)
uv run python run.py        # starts at http://127.0.0.1:5000
```

No `setup_bigquery.py` step is needed in SQLite mode — the schema is created automatically in `backend/local_demo.db`.

**BigQuery mode (when credentials are available):** set `DB_BACKEND=bigquery` (plus `BIGQUERY_PROJECT` and `GOOGLE_APPLICATION_CREDENTIALS`) in `.env`, then run `uv run python setup_bigquery.py` once before seeding. Everything else is identical.

Run only **one** backend process on port 5000. Multiple stale `run.py` instances can bind the same port and serve outdated code (e.g. missing `weeklyMetrics` on the dashboard or old PDF text encoding). If the week picker is empty, members fail to load, or PDFs show `?` instead of dashes:

```powershell
netstat -ano | findstr ":5000"
```

Stop duplicate listeners, then restart:

```bash
uv run python run.py
```

Visit `http://127.0.0.1:5000/api/health` to confirm the server is up. The frontend dev server runs separately at `http://localhost:5173` from `impactdash_app/frontend`.
