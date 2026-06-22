"""Business logic for nonprofit dashboards with RBAC."""
import re

from auth import get_auth_context
from repositories.donor_repo import DonorRepo
from repositories.metrics_repo import MetricsRepo
from repositories.nonprofit_repo import NonprofitRepo
from repositories.program_repo import ProgramRepo
from repositories.user_repo import UserRepo

nonprofit_repo = NonprofitRepo()
program_repo = ProgramRepo()
metrics_repo = MetricsRepo()
donor_repo = DonorRepo()
user_repo = UserRepo()

VALID_PROGRAM_STATUSES = ("active", "paused")


def _ctx():
    ctx = get_auth_context()
    if not ctx:
        raise ValueError("Authentication required")
    return ctx


def _is_platform_admin(ctx):
    return ctx["role"] == "platform_admin"


def _require_nonprofit_access(nonprofit_id):
    ctx = _ctx()
    if _is_platform_admin(ctx):
        return ctx
    if ctx["role"] != "nonprofit_user":
        raise ValueError("Forbidden")
    if ctx.get("nonprofit_id") != nonprofit_id:
        raise ValueError("Forbidden")
    return ctx


def _nonprofit_ids_for_ctx(ctx):
    if _is_platform_admin(ctx):
        return [n["nonprofit_id"] for n in nonprofit_repo.list_all(include_inactive=True)]
    if ctx.get("nonprofit_id"):
        return [ctx["nonprofit_id"]]
    return []


def _slugify(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "nonprofit"


def _serialize_nonprofit(doc):
    return {
        "nonprofitId": doc["nonprofit_id"],
        "name": doc["name"],
        "slug": doc["slug"],
        "mission": doc.get("mission", ""),
        "location": doc.get("location", ""),
        "isActive": doc.get("is_active", True),
        "createdAt": doc.get("created_at").isoformat() if doc.get("created_at") else None,
    }


def _serialize_program(doc):
    return {
        "programId": doc["program_id"],
        "nonprofitId": doc["nonprofit_id"],
        "name": doc["name"],
        "status": doc["status"],
        "participants": doc.get("participants", 0),
        "budget": doc.get("budget", 0),
    }


def _serialize_donor(doc):
    return {
        "donorId": doc["donor_id"],
        "name": doc["name"],
        "email": doc.get("email", ""),
        "donationAmount": float(doc.get("donation_amount") or 0),
    }


def _email_trend(change):
    if change > 0:
        return "up"
    if change < 0:
        return "down"
    return "flat"


def _serialize_insights(metrics):
    change = int(metrics.get("email_opens_change") or 0)
    return {
        "highestDonation": float(metrics.get("highest_donation") or 0),
        "biggestDonorName": metrics.get("biggest_donor_name") or "",
        "emailOpensCurrent": int(metrics.get("email_opens_current") or 0),
        "emailOpensPrevious": int(metrics.get("email_opens_previous") or 0),
        "emailOpensChange": change,
        "emailOpensChangePct": float(metrics.get("email_opens_change_pct") or 0),
        "emailOpensTrend": _email_trend(change),
    }


def _serialize_metrics(doc):
    goal = float(doc.get("funding_goal") or 0)
    raised = float(doc.get("funding_raised") or 0)
    progress = round((raised / goal) * 100, 1) if goal > 0 else 0.0
    return {
        "donorCount": int(doc.get("donor_count") or 0),
        "totalDonations": float(doc.get("total_donations") or 0),
        "activeVolunteers": int(doc.get("active_volunteers") or 0),
        "volunteerHours": int(doc.get("volunteer_hours") or 0),
        "fundingGoal": goal,
        "fundingRaised": raised,
        "grantsReceived": float(doc.get("grants_received") or 0),
        "fundingProgress": progress,
        "emailOpensCurrent": int(doc.get("email_opens_current") or 0),
        "emailOpensPrevious": int(doc.get("email_opens_previous") or 0),
        "highestDonation": float(doc.get("highest_donation") or 0),
        "biggestDonorName": doc.get("biggest_donor_name") or "",
        "emailOpensChange": int(doc.get("email_opens_change") or 0),
        "emailOpensChangePct": float(doc.get("email_opens_change_pct") or 0),
        "updatedAt": doc.get("updated_at").isoformat() if doc.get("updated_at") else None,
    }


def list_nonprofits():
    ctx = _ctx()
    ids = _nonprofit_ids_for_ctx(ctx)
    if not ids:
        return []
    docs = nonprofit_repo.list_by_ids(ids)
    return [_serialize_nonprofit(d) for d in docs]


def create_nonprofit(name, mission, location, slug=None):
    ctx = _ctx()
    if not _is_platform_admin(ctx):
        raise ValueError("Forbidden")
    if not name or not name.strip():
        raise ValueError("name is required")
    slug = (slug or _slugify(name)).strip()
    if nonprofit_repo.get_by_slug(slug):
        raise ValueError("slug already in use")
    doc = nonprofit_repo.add(name.strip(), slug, (mission or "").strip(), (location or "").strip())
    metrics_repo.upsert(doc["nonprofit_id"], {})
    return _serialize_nonprofit(doc)


def get_nonprofit(nonprofit_id):
    _require_nonprofit_access(nonprofit_id)
    doc = nonprofit_repo.get_by_id(nonprofit_id)
    if not doc:
        raise ValueError("Nonprofit not found")
    return _serialize_nonprofit(doc)


def update_nonprofit(nonprofit_id, updates):
    ctx = _require_nonprofit_access(nonprofit_id)
    if not _is_platform_admin(ctx):
        allowed = {"mission", "location"}
        updates = {k: v for k, v in updates.items() if k in allowed}
    mapping = {
        "name": "name",
        "slug": "slug",
        "mission": "mission",
        "location": "location",
        "isActive": "is_active",
    }
    payload = {}
    for src, dest in mapping.items():
        if src in updates and updates[src] is not None:
            payload[dest] = updates[src]
    doc = nonprofit_repo.update(nonprofit_id, payload)
    if not doc:
        raise ValueError("Nonprofit not found")
    return _serialize_nonprofit(doc)


def get_dashboard(nonprofit_id):
    _require_nonprofit_access(nonprofit_id)
    nonprofit = nonprofit_repo.get_by_id(nonprofit_id)
    if not nonprofit:
        raise ValueError("Nonprofit not found")
    metrics = metrics_repo.get_for_nonprofit(nonprofit_id)
    programs = program_repo.list_for_nonprofit(nonprofit_id)
    donors = donor_repo.list_for_nonprofit(nonprofit_id, limit=10)
    active_programs = sum(1 for p in programs if p.get("status") == "active")
    return {
        "nonprofit": _serialize_nonprofit(nonprofit),
        "summary": {
            "donorCount": int(metrics.get("donor_count") or 0),
            "totalDonations": float(metrics.get("total_donations") or 0),
            "activeVolunteers": int(metrics.get("active_volunteers") or 0),
            "volunteerHours": int(metrics.get("volunteer_hours") or 0),
            "activePrograms": active_programs,
            "totalPrograms": len(programs),
        },
        "metrics": _serialize_metrics(metrics),
        "insights": _serialize_insights(metrics),
        "donors": [_serialize_donor(d) for d in donors],
        "programs": [_serialize_program(p) for p in programs],
    }


def update_metrics(nonprofit_id, data):
    _require_nonprofit_access(nonprofit_id)
    if not nonprofit_repo.get_by_id(nonprofit_id):
        raise ValueError("Nonprofit not found")
    mapping = {
        "donorCount": "donor_count",
        "totalDonations": "total_donations",
        "activeVolunteers": "active_volunteers",
        "volunteerHours": "volunteer_hours",
        "fundingGoal": "funding_goal",
        "fundingRaised": "funding_raised",
        "grantsReceived": "grants_received",
        "emailOpensCurrent": "email_opens_current",
        "emailOpensPrevious": "email_opens_previous",
    }
    updates = {}
    for camel, snake in mapping.items():
        if camel in data:
            updates[snake] = data[camel]
    doc = metrics_repo.upsert(nonprofit_id, updates)
    doc = metrics_repo.recompute_highlights(nonprofit_id)
    return _serialize_metrics(doc)


def list_programs(nonprofit_id):
    _require_nonprofit_access(nonprofit_id)
    return [_serialize_program(p) for p in program_repo.list_for_nonprofit(nonprofit_id)]


def create_program(nonprofit_id, name, status, participants, budget):
    _require_nonprofit_access(nonprofit_id)
    if not nonprofit_repo.get_by_id(nonprofit_id):
        raise ValueError("Nonprofit not found")
    if not name or not name.strip():
        raise ValueError("name is required")
    status = (status or "active").lower()
    if status not in VALID_PROGRAM_STATUSES:
        raise ValueError("status must be active or paused")
    doc = program_repo.add(
        nonprofit_id,
        name.strip(),
        status,
        int(participants or 0),
        float(budget or 0),
    )
    return _serialize_program(doc)


def update_program(nonprofit_id, program_id, updates):
    _require_nonprofit_access(nonprofit_id)
    program = program_repo.get_by_id(program_id)
    if not program or program["nonprofit_id"] != nonprofit_id:
        raise ValueError("Program not found")
    status = updates.get("status")
    if status is not None:
        status = status.lower()
        if status not in VALID_PROGRAM_STATUSES:
            raise ValueError("status must be active or paused")
    payload = {}
    if "name" in updates:
        payload["name"] = updates["name"]
    if status is not None:
        payload["status"] = status
    if "participants" in updates:
        payload["participants"] = int(updates["participants"])
    if "budget" in updates:
        payload["budget"] = float(updates["budget"])
    doc = program_repo.update(program_id, payload)
    return _serialize_program(doc)


def delete_program(nonprofit_id, program_id):
    _require_nonprofit_access(nonprofit_id)
    program = program_repo.get_by_id(program_id)
    if not program or program["nonprofit_id"] != nonprofit_id:
        raise ValueError("Program not found")
    if not program_repo.delete(program_id):
        raise ValueError("Program not found")
    return {"deleted": True}


def list_users():
    ctx = _ctx()
    if not _is_platform_admin(ctx):
        raise ValueError("Forbidden")
    users = user_repo.get_all_users()
    return [
        {
            "userId": u["user_id"],
            "name": u["name"],
            "email": u["email"],
            "role": u.get("role", "nonprofit_user"),
            "nonprofitId": u.get("nonprofit_id"),
            "isDeleted": u.get("is_deleted", False),
        }
        for u in users
        if not u.get("is_deleted")
    ]


def generate_report_pdf(nonprofit_id):
    from services.report_service import build_nonprofit_pdf

    ctx = _require_nonprofit_access(nonprofit_id)
    dashboard = get_dashboard(nonprofit_id)
    return build_nonprofit_pdf(dashboard, generated_by=ctx["name"], role=ctx["role"])
