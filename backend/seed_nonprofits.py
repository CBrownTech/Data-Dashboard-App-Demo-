"""Seed demo nonprofits, programs, metrics, and users for ImpactDash."""
from werkzeug.security import generate_password_hash

from db.database import get_mongo_db
from repositories.donor_repo import DonorRepo
from repositories.metrics_repo import MetricsRepo
from repositories.nonprofit_repo import NonprofitRepo
from repositories.program_repo import ProgramRepo
from repositories.user_repo import UserRepo

PASSWORD = "demo1234"

NONPROFITS = [
    {
        "name": "River Valley Food Bank",
        "slug": "river-valley-food-bank",
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
    },
    {
        "name": "Bright Futures Youth Mentoring",
        "slug": "bright-futures-youth",
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
    },
    {
        "name": "Paws & Hearts Animal Rescue",
        "slug": "paws-hearts-rescue",
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
    },
]


def main():
    db = get_mongo_db()
    for coll in ("donors", "programs", "nonprofit_metrics", "nonprofits"):
        db[coll].delete_many({})

    nonprofit_repo = NonprofitRepo()
    program_repo = ProgramRepo()
    metrics_repo = MetricsRepo()
    donor_repo = DonorRepo()
    user_repo = UserRepo()
    password_hash = generate_password_hash(PASSWORD)

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
                "role": "nonprofit_user",
                "nonprofit_id": np["nonprofit_id"],
                "is_admin": False,
                "password_hash": password_hash,
            })
        else:
            user_repo.add_user(
                item["user"]["name"],
                item["user"]["email"],
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
    main()
