"""Parse and import nonprofit dashboard data from CSV files."""
import csv
import io
import re
from dataclasses import dataclass, field

from auth import get_auth_context
from repositories.donor_repo import DonorRepo
from repositories.metrics_repo import MetricsRepo
from repositories.nonprofit_repo import NonprofitRepo
from repositories.program_repo import ProgramRepo
from services import nonprofit_service

nonprofit_repo = NonprofitRepo()
program_repo = ProgramRepo()
donor_repo = DonorRepo()
metrics_repo = MetricsRepo()

VALID_MODES = ("auto", "update", "create")
VALID_PROGRAM_STATUSES = ("active", "paused")

CORE_REQUIRED_COLUMNS = {
    "row_type",
    "name",
    "slug",
    "mission",
    "location",
    "donor_count",
    "total_donations",
    "active_volunteers",
    "volunteer_hours",
    "funding_goal",
    "funding_raised",
    "grants_received",
    "status",
    "participants",
    "budget",
}

METRIC_COLUMNS = {
    "donor_count": "donorCount",
    "total_donations": "totalDonations",
    "active_volunteers": "activeVolunteers",
    "volunteer_hours": "volunteerHours",
    "funding_goal": "fundingGoal",
    "funding_raised": "fundingRaised",
    "grants_received": "grantsReceived",
    "email_opens_current": "emailOpensCurrent",
    "email_opens_previous": "emailOpensPrevious",
}

CSV_COLUMNS = [
    "row_type",
    "name",
    "slug",
    "mission",
    "location",
    "donor_count",
    "total_donations",
    "active_volunteers",
    "volunteer_hours",
    "funding_goal",
    "funding_raised",
    "grants_received",
    "email_opens_current",
    "email_opens_previous",
    "status",
    "participants",
    "budget",
    "email",
    "donation_amount",
]

TEMPLATE_ROWS = [
    {
        "row_type": "nonprofit",
        "name": "Example Nonprofit",
        "slug": "example-nonprofit",
        "mission": "Our mission statement",
        "location": "City ST",
        "donor_count": "100",
        "total_donations": "50000",
        "active_volunteers": "25",
        "volunteer_hours": "1200",
        "funding_goal": "100000",
        "funding_raised": "75000",
        "grants_received": "20000",
        "email_opens_current": "12500",
        "email_opens_previous": "10800",
    },
    {
        "row_type": "donor",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "donation_amount": "5000",
    },
    {
        "row_type": "donor",
        "name": "Acme Corp",
        "email": "giving@acme.org",
        "donation_amount": "25000",
    },
    {
        "row_type": "program",
        "name": "Example Program",
        "status": "active",
        "participants": "50",
        "budget": "10000",
    },
]


@dataclass
class ParsedImport:
    nonprofit: dict
    programs: list = field(default_factory=list)
    donors: list = field(default_factory=list)


def _require_platform_admin():
    ctx = get_auth_context()
    if not ctx or ctx.get("role") != "platform_admin":
        raise ValueError("Forbidden")
    return ctx


def _slugify(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "nonprofit"


def _cell(value):
    if value is None:
        return ""
    return str(value).strip()


def _parse_number(value, field_name, row_num, integer=False):
    text = _cell(value)
    if not text:
        return 0
    try:
        number = float(text)
        if integer:
            return int(number)
        return number
    except ValueError as exc:
        raise ValueError(f"Row {row_num}: {field_name} must be a number") from exc


def _normalize_row(row):
    return {k.strip().lower(): v for k, v in row.items() if k is not None}


def parse_csv(file_stream):
    """Parse uploaded CSV into nonprofit, program, and donor rows."""
    content = file_stream.read()
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError("CSV file is empty or missing a header row")

    headers = {h.strip().lower() for h in reader.fieldnames if h}
    missing = CORE_REQUIRED_COLUMNS - headers
    if missing:
        raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")

    nonprofit_rows = []
    programs = []
    donors = []

    for row_num, raw_row in enumerate(reader, start=2):
        row = _normalize_row(raw_row)
        row_type = _cell(row.get("row_type")).lower()
        if not row_type:
            continue

        if row_type == "nonprofit":
            nonprofit_rows.append((row_num, row))
        elif row_type == "program":
            name = _cell(row.get("name"))
            if not name:
                raise ValueError(f"Row {row_num}: program name is required")
            status = _cell(row.get("status")).lower() or "active"
            if status not in VALID_PROGRAM_STATUSES:
                raise ValueError(f"Row {row_num}: status must be active or paused")
            programs.append({
                "name": name,
                "status": status,
                "participants": _parse_number(row.get("participants"), "participants", row_num, integer=True),
                "budget": _parse_number(row.get("budget"), "budget", row_num),
            })
        elif row_type == "donor":
            name = _cell(row.get("name"))
            if not name:
                raise ValueError(f"Row {row_num}: donor name is required")
            donors.append({
                "name": name,
                "email": _cell(row.get("email")),
                "donation_amount": _parse_number(row.get("donation_amount"), "donation_amount", row_num),
            })
        else:
            raise ValueError(f"Row {row_num}: row_type must be nonprofit, program, or donor")

    if len(nonprofit_rows) == 0:
        raise ValueError("CSV must contain exactly one nonprofit row")
    if len(nonprofit_rows) > 1:
        rows = ", ".join(str(r[0]) for r in nonprofit_rows)
        raise ValueError(f"CSV must contain exactly one nonprofit row (found rows {rows})")

    row_num, row = nonprofit_rows[0]
    name = _cell(row.get("name"))
    if not name:
        raise ValueError(f"Row {row_num}: nonprofit name is required")

    slug = _cell(row.get("slug")) or _slugify(name)
    integer_metrics = {"donor_count", "active_volunteers", "volunteer_hours", "email_opens_current", "email_opens_previous"}
    nonprofit = {
        "name": name,
        "slug": slug,
        "mission": _cell(row.get("mission")),
        "location": _cell(row.get("location")),
        "metrics": {
            camel: _parse_number(
                row.get(snake),
                snake,
                row_num,
                integer=(snake in integer_metrics),
            )
            for snake, camel in METRIC_COLUMNS.items()
        },
    }

    return ParsedImport(nonprofit=nonprofit, programs=programs, donors=donors)


def _find_existing(nonprofit_data):
    slug = nonprofit_data.get("slug")
    if slug:
        existing = nonprofit_repo.get_by_slug(slug)
        if existing:
            return existing
    name = nonprofit_data.get("name")
    if name:
        return nonprofit_repo.get_by_name_insensitive(name)
    return None


def _apply_profile(nonprofit_id, nonprofit_data):
    nonprofit_service.update_nonprofit(nonprofit_id, {
        "name": nonprofit_data["name"],
        "mission": nonprofit_data["mission"],
        "location": nonprofit_data["location"],
    })


def _apply_metrics(nonprofit_id, metrics):
    nonprofit_service.update_metrics(nonprofit_id, metrics)
    return len(metrics)


def _upsert_programs(nonprofit_id, programs):
    added = 0
    updated = 0
    for program in programs:
        existing = program_repo.get_by_name(nonprofit_id, program["name"])
        if existing:
            nonprofit_service.update_program(nonprofit_id, existing["program_id"], program)
            updated += 1
        else:
            nonprofit_service.create_program(
                nonprofit_id,
                program["name"],
                program["status"],
                program["participants"],
                program["budget"],
            )
            added += 1
    return added, updated


def _upsert_donors(nonprofit_id, donors):
    added = 0
    updated = 0
    for donor in donors:
        existing = None
        if donor.get("email"):
            existing = donor_repo.get_by_email(nonprofit_id, donor["email"])
        if not existing:
            existing = donor_repo.get_by_name_insensitive(nonprofit_id, donor["name"])
        if existing:
            donor_repo.update(existing["donor_id"], {
                "name": donor["name"],
                "email": donor.get("email") or existing.get("email", ""),
                "donation_amount": donor["donation_amount"],
            })
            updated += 1
        else:
            donor_repo.add(
                nonprofit_id,
                donor["name"],
                donor.get("email", ""),
                donor["donation_amount"],
            )
            added += 1
    return added, updated


def _finalize_import(nonprofit_id, np_data, parsed):
    metrics_count = _apply_metrics(nonprofit_id, np_data["metrics"])
    programs_added, programs_updated = _upsert_programs(nonprofit_id, parsed.programs)
    donors_added, donors_updated = _upsert_donors(nonprofit_id, parsed.donors)
    metrics_repo.recompute_highlights(nonprofit_id)
    return metrics_count, programs_added, programs_updated, donors_added, donors_updated


def _import_result(action, nonprofit_id, nonprofit_name, counts):
    metrics_count, programs_added, programs_updated, donors_added, donors_updated = counts
    return {
        "action": action,
        "nonprofitId": nonprofit_id,
        "nonprofitName": nonprofit_name,
        "metricsUpdated": metrics_count,
        "programsAdded": programs_added,
        "programsUpdated": programs_updated,
        "donorsAdded": donors_added,
        "donorsUpdated": donors_updated,
        "warnings": [],
    }


def import_csv(parsed, mode="auto", nonprofit_id=None):
    """Import parsed CSV data. Platform admin only."""
    _require_platform_admin()
    if mode not in VALID_MODES:
        raise ValueError("mode must be auto, update, or create")

    np_data = parsed.nonprofit

    if mode == "update":
        if not nonprofit_id:
            raise ValueError("nonprofitId is required for update mode")
        existing = nonprofit_repo.get_by_id(nonprofit_id)
        if not existing:
            raise ValueError("Nonprofit not found")
        _apply_profile(nonprofit_id, np_data)
        counts = _finalize_import(nonprofit_id, np_data, parsed)
        return _import_result("updated", nonprofit_id, existing["name"], counts)

    if mode == "create":
        match = _find_existing(np_data)
        if match:
            raise ValueError(f"Nonprofit already exists: {match['name']}")
        created = nonprofit_service.create_nonprofit(
            np_data["name"],
            np_data["mission"],
            np_data["location"],
            np_data["slug"],
        )
        nonprofit_id = created["nonprofitId"]
        counts = _finalize_import(nonprofit_id, np_data, parsed)
        return _import_result("created", nonprofit_id, np_data["name"], counts)

    existing = _find_existing(np_data)
    if existing:
        nonprofit_id = existing["nonprofit_id"]
        _apply_profile(nonprofit_id, np_data)
        counts = _finalize_import(nonprofit_id, np_data, parsed)
        return _import_result("updated", nonprofit_id, existing["name"], counts)

    created = nonprofit_service.create_nonprofit(
        np_data["name"],
        np_data["mission"],
        np_data["location"],
        np_data["slug"],
    )
    nonprofit_id = created["nonprofitId"]
    counts = _finalize_import(nonprofit_id, np_data, parsed)
    return _import_result("created", nonprofit_id, np_data["name"], counts)


def get_template_csv():
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(TEMPLATE_ROWS)
    return buffer.getvalue()
