"""Seed demo nonprofits, programs, metrics, and users for ImpactDash."""
import argparse
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from db.database import get_mongo_db
from repositories.donor_repo import DonorRepo
from repositories.metrics_repo import MetricsRepo
from repositories.nonprofit_repo import NonprofitRepo
from repositories.program_repo import ProgramRepo
from repositories.user_repo import UserRepo

PASSWORD = "demo1234"

# Retired demo member emails removed on re-seed (avoid duplicate About listings).
STALE_MEMBER_EMAILS = frozenset({
    "volunteer@rivervalley.org",
    "mentor@brightfutures.org",
    "foster@pawshearts.org",
    "events@pawshearts.org",
})

NONPROFITS = [
    {
        "name": "River Valley Food Bank",
        "slug": "river-valley-food-bank",
        "reference_code": "RVFB-001",
        "source_code": "SRC-PDX-EMAIL",
        "mission": "Reduce hunger in our community through food distribution and nutrition programs.",
        "location": "Portland, OR",
        "metrics": {
            "donor_count": 842,
            "total_donations": 125400.0,
            "active_volunteers": 156,
            "volunteer_hours": 4280,
            "funding_goal": 200000.0,
            "funding_raised": 148500.0,
            "grants_received": 45000.0,
            "email_opens_current": 12500,
            "email_opens_previous": 10800,
            "p2p_messages_sent": 4200,
            "p2p_responses": 890,
            "p2p_opt_outs": 45,
            "call_hours": 312.5,
            "calls_made": 1850,
            "contacts_reached": 1420,
            "call_avg_duration_minutes": 10.2,
            "email_donations": 52000.0,
            "email_donation_count": 310,
            "p2p_donations": 38000.0,
            "p2p_donation_count": 145,
            "call_donations": 22400.0,
            "call_donation_count": 89,
        },
        "donors": [
            {"name": "Jane Doe", "email": "jane@example.com", "donation_amount": 5000},
            {"name": "Acme Corp", "email": "giving@acme.org", "donation_amount": 25000},
            {"name": "Portland Community Fund", "email": "fund@pcf.org", "donation_amount": 12000},
        ],
        "programs": [
            {"name": "Weekend Meal Kits", "status": "active", "participants": 320, "budget": 45000},
            {"name": "Mobile Pantry", "status": "active", "participants": 180, "budget": 28000},
            {"name": "Senior Nutrition", "status": "paused", "participants": 95, "budget": 12000},
        ],
        "user": {"name": "Sarah Chen", "email": "sarah@rivervalley.org"},
        "members": [
            {"name": "James Ortiz", "email": "james.ortiz@rivervalley.org"},
        ],
    },
    {
        "name": "Bright Futures Youth Mentoring",
        "slug": "bright-futures-youth",
        "reference_code": "BFYM-002",
        "source_code": "SRC-AUS-P2P",
        "mission": "Pair at-risk youth with mentors to improve academic and life outcomes.",
        "location": "Austin, TX",
        "metrics": {
            "donor_count": 412,
            "total_donations": 67800.0,
            "active_volunteers": 89,
            "volunteer_hours": 2150,
            "funding_goal": 120000.0,
            "funding_raised": 89200.0,
            "grants_received": 25000.0,
            "email_opens_current": 6200,
            "email_opens_previous": 5800,
            "p2p_messages_sent": 2800,
            "p2p_responses": 520,
            "p2p_opt_outs": 28,
            "call_hours": 186.0,
            "calls_made": 980,
            "contacts_reached": 740,
            "call_avg_duration_minutes": 11.4,
            "email_donations": 18200.0,
            "email_donation_count": 95,
            "p2p_donations": 28400.0,
            "p2p_donation_count": 128,
            "call_donations": 12600.0,
            "call_donation_count": 52,
        },
        "donors": [
            {"name": "Austin Education Trust", "email": "donate@aet.org", "donation_amount": 15000},
            {"name": "Maria Santos", "email": "maria@email.com", "donation_amount": 2500},
        ],
        "programs": [
            {"name": "School Partnership", "status": "active", "participants": 140, "budget": 38000},
            {"name": "Summer Leadership Camp", "status": "active", "participants": 60, "budget": 22000},
        ],
        "user": {"name": "Marcus Williams", "email": "marcus@brightfutures.org"},
        "members": [
            {"name": "Aisha Patel", "email": "aisha.patel@brightfutures.org"},
        ],
    },
    {
        "name": "Paws & Hearts Animal Rescue",
        "slug": "paws-hearts-rescue",
        "reference_code": "PAWS-003",
        "source_code": "SRC-DEN-CALL",
        "mission": "Rescue, rehabilitate, and rehome abandoned and neglected animals.",
        "location": "Denver, CO",
        "metrics": {
            "donor_count": 1205,
            "total_donations": 198600.0,
            "active_volunteers": 234,
            "volunteer_hours": 6120,
            "funding_goal": 250000.0,
            "funding_raised": 221000.0,
            "grants_received": 62000.0,
            "email_opens_current": 8900,
            "email_opens_previous": 9200,
            "p2p_messages_sent": 5100,
            "p2p_responses": 1100,
            "p2p_opt_outs": 62,
            "call_hours": 428.0,
            "calls_made": 2340,
            "contacts_reached": 1890,
            "call_avg_duration_minutes": 11.0,
            "email_donations": 44600.0,
            "email_donation_count": 280,
            "p2p_donations": 52800.0,
            "p2p_donation_count": 210,
            "call_donations": 71200.0,
            "call_donation_count": 315,
        },
        "donors": [
            {"name": "Denver Pet Lovers", "email": "hello@dpl.org", "donation_amount": 18000},
            {"name": "Robert Chen", "email": "rchen@email.com", "donation_amount": 7500},
            {"name": "Mountain West Foundation", "email": "grants@mwf.org", "donation_amount": 30000},
        ],
        "programs": [
            {"name": "Adoption Center", "status": "active", "participants": 410, "budget": 85000},
            {"name": "Spay/Neuter Clinic", "status": "active", "participants": 275, "budget": 55000},
            {"name": "Foster Network", "status": "active", "participants": 120, "budget": 18000},
        ],
        "user": {"name": "Elena Rodriguez", "email": "elena@pawshearts.org"},
        "members": [
            {"name": "Tom Nguyen", "email": "tom.nguyen@pawshearts.org"},
            {"name": "Lisa Park", "email": "lisa.park@pawshearts.org"},
        ],
    },
]


def _monday_on_or_before(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _week_start_dates(count=6, anchor: date | None = None) -> list[str]:
    """Return ISO week-start dates (oldest first) ending with the current week."""
    today = anchor or date.today()
    current_monday = _monday_on_or_before(today)
    starts = []
    for offset in range(count - 1, -1, -1):
        week = current_monday - timedelta(weeks=offset)
        starts.append(week.isoformat())
    return starts


def _scale_int(value, factor):
    return max(0, int(round(float(value) * factor)))


def _scale_float(value, factor):
    return max(0.0, round(float(value) * factor, 1))


def build_weekly_snapshots(metrics: dict, week_starts: list[str]) -> list[dict]:
    """Build weekly history; latest week aligns with dashboard metrics."""
    n = len(week_starts)
    if n == 0:
        return []

    email_current = int(metrics.get("email_opens_current") or 0)
    email_previous = int(metrics.get("email_opens_previous") or 0)
    email_ratio = (email_previous / email_current) if email_current > 0 else 0.9

    def snapshot_at(index: int) -> dict:
        if index == n - 1:
            factor = 1.0
            email_opens = email_current
        elif index == n - 2:
            factor = email_ratio
            email_opens = email_previous
        else:
            progress = (index + 1) / n
            factor = 0.78 + (0.22 * progress)
            email_opens = _scale_int(email_current, factor)

        return {
            "week_start": week_starts[index],
            "email_opens": email_opens,
            "p2p_messages_sent": _scale_int(metrics.get("p2p_messages_sent"), factor),
            "p2p_responses": _scale_int(metrics.get("p2p_responses"), factor),
            "p2p_opt_outs": max(1, _scale_int(metrics.get("p2p_opt_outs"), factor)),
            "call_hours": _scale_float(metrics.get("call_hours"), factor),
            "calls_made": _scale_int(metrics.get("calls_made"), factor),
            "contacts_reached": _scale_int(metrics.get("contacts_reached"), factor),
            "donations_total": _scale_float(metrics.get("total_donations"), factor * 0.12),
            "email_donations": _scale_float(metrics.get("email_donations"), factor * 0.12),
            "p2p_donations": _scale_float(metrics.get("p2p_donations"), factor * 0.12),
            "call_donations": _scale_float(metrics.get("call_donations"), factor * 0.12),
            "donor_count": _scale_int(metrics.get("donor_count"), 0.85 + (0.15 * factor)),
            "active_volunteers": _scale_int(metrics.get("active_volunteers"), 0.9 + (0.1 * factor)),
            "volunteer_hours": _scale_int(metrics.get("volunteer_hours"), factor * 0.15),
            "funding_raised": _scale_float(metrics.get("funding_raised"), 0.88 + (0.12 * factor)),
        }

    return [snapshot_at(i) for i in range(n)]


def backfill_weekly_metrics():
    """Create 6-week snapshots for orgs that have aggregate metrics but no weekly history."""
    nonprofit_repo = NonprofitRepo()
    metrics_repo = MetricsRepo()
    week_starts = _week_start_dates(6)
    backfilled = 0
    skipped = 0

    for np in nonprofit_repo.list_all(include_inactive=True):
        nonprofit_id = np["nonprofit_id"]
        if metrics_repo.list_weekly(nonprofit_id):
            skipped += 1
            continue
        metrics = metrics_repo.get_for_nonprofit(nonprofit_id)
        snapshots = build_weekly_snapshots(metrics, week_starts)
        if not snapshots:
            continue
        metrics_repo.replace_weekly_for_nonprofit(nonprofit_id, snapshots)
        backfilled += 1
        print(f"  Backfilled weekly metrics for {np.get('name')} (id={nonprofit_id})")

    print(f"Backfill complete: {backfilled} org(s) updated, {skipped} already had weekly data.")
    return backfilled


def main():
    db = get_mongo_db()
    for coll in ("donors", "programs", "nonprofit_metrics", "nonprofit_weekly_metrics", "nonprofits"):
        db[coll].delete_many({})

    nonprofit_repo = NonprofitRepo()
    program_repo = ProgramRepo()
    metrics_repo = MetricsRepo()
    donor_repo = DonorRepo()
    user_repo = UserRepo()
    password_hash = generate_password_hash(PASSWORD)
    week_starts = _week_start_dates(6)

    for stale_email in STALE_MEMBER_EMAILS:
        stale = user_repo.get_user_by_email(stale_email)
        if stale and not stale.get("is_deleted"):
            user_repo.soft_delete(stale["user_id"])

    admin = user_repo.get_user_by_email("admin@platform.org")
    if admin:
        user_repo.update_user(admin["user_id"], {
            "name": "Platform Admin",
            "role": "platform_admin",
            "is_admin": True,
            "nonprofit_id": None,
            "password_hash": password_hash,
        })
    else:
        user_repo.add_user(
            "Platform Admin",
            "admin@platform.org",
            password_hash=password_hash,
            role="platform_admin",
            is_admin=True,
        )

    for item in NONPROFITS:
        np = nonprofit_repo.add(
            item["name"],
            item["slug"],
            item["mission"],
            item["location"],
            item.get("reference_code", ""),
            item.get("source_code", ""),
        )
        metrics_repo.seed_defaults(np["nonprofit_id"], item["metrics"])
        for donor in item.get("donors", []):
            donor_repo.add(
                np["nonprofit_id"],
                donor["name"],
                donor.get("email", ""),
                donor["donation_amount"],
            )
        metrics_repo.recompute_highlights(np["nonprofit_id"])
        metrics_repo.replace_weekly_for_nonprofit(
            np["nonprofit_id"],
            build_weekly_snapshots(item["metrics"], week_starts),
        )
        for prog in item["programs"]:
            program_repo.add(
                np["nonprofit_id"],
                prog["name"],
                prog["status"],
                prog["participants"],
                prog["budget"],
            )

        existing = user_repo.get_user_by_email(item["user"]["email"])
        if existing:
            user_repo.update_user(existing["user_id"], {
                "name": item["user"]["name"],
                "role": "nonprofit_owner",
                "nonprofit_id": np["nonprofit_id"],
                "is_admin": False,
                "password_hash": password_hash,
            })
        else:
            user_repo.add_user(
                item["user"]["name"],
                item["user"]["email"],
                password_hash=password_hash,
                role="nonprofit_owner",
                nonprofit_id=np["nonprofit_id"],
            )

        for member in item.get("members", []):
            mem_email = member["email"]
            mem_existing = user_repo.get_user_by_email(mem_email)
            if mem_existing:
                if mem_existing.get("is_deleted"):
                    user_repo.reactivate_user(
                        mem_existing["user_id"],
                        member["name"],
                        password_hash=password_hash,
                    )
                user_repo.update_user(mem_existing["user_id"], {
                    "name": member["name"],
                    "role": "nonprofit_user",
                    "nonprofit_id": np["nonprofit_id"],
                    "is_admin": False,
                    "password_hash": password_hash,
                })
            else:
                user_repo.add_user(
                    member["name"],
                    mem_email,
                    password_hash=password_hash,
                    role="nonprofit_user",
                    nonprofit_id=np["nonprofit_id"],
                )

    print("Seeded 3 nonprofits with programs, metrics, and demo users.")
    print("Platform admin: admin@platform.org")
    for item in NONPROFITS:
        print(f"  {item['user']['email']} -> {item['name']}")
    print(f"Password for all: {PASSWORD}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed or backfill ImpactDash demo data.")
    parser.add_argument(
        "--backfill-only",
        action="store_true",
        help="Backfill nonprofit_weekly_metrics for orgs missing weekly snapshots (non-destructive).",
    )
    args = parser.parse_args()
    if args.backfill_only:
        backfill_weekly_metrics()
    else:
        main()
