from datetime import datetime, timezone

from pymongo import ReturnDocument

from db.database import get_mongo_db
from repositories.donor_repo import DonorRepo


DEFAULT_METRICS = {
    "donor_count": 0,
    "total_donations": 0.0,
    "active_volunteers": 0,
    "volunteer_hours": 0,
    "funding_goal": 0.0,
    "funding_raised": 0.0,
    "grants_received": 0.0,
    "email_opens_current": 0,
    "email_opens_previous": 0,
    "highest_donation": 0.0,
    "biggest_donor_name": "",
    "email_opens_change": 0,
    "email_opens_change_pct": 0.0,
}


class MetricsRepo:
    def __init__(self):
        self._db = get_mongo_db()
        self._donor_repo = DonorRepo()

    def get_for_nonprofit(self, nonprofit_id):
        doc = self._db.nonprofit_metrics.find_one({"nonprofit_id": nonprofit_id})
        if doc:
            return doc
        return {"nonprofit_id": nonprofit_id, **DEFAULT_METRICS}

    def upsert(self, nonprofit_id, updates):
        allowed = {
            "donor_count",
            "total_donations",
            "active_volunteers",
            "volunteer_hours",
            "funding_goal",
            "funding_raised",
            "grants_received",
            "email_opens_current",
            "email_opens_previous",
            "highest_donation",
            "biggest_donor_name",
            "email_opens_change",
            "email_opens_change_pct",
        }
        payload = {k: v for k, v in updates.items() if k in allowed}
        payload["updated_at"] = datetime.now(timezone.utc)
        return self._db.nonprofit_metrics.find_one_and_update(
            {"nonprofit_id": nonprofit_id},
            {"$set": payload, "$setOnInsert": {"nonprofit_id": nonprofit_id}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    def seed_defaults(self, nonprofit_id, metrics):
        now = datetime.now(timezone.utc)
        doc = {"nonprofit_id": nonprofit_id, "updated_at": now, **DEFAULT_METRICS, **metrics}
        self._db.nonprofit_metrics.insert_one(doc)
        return doc

    def recompute_highlights(self, nonprofit_id):
        metrics = self.get_for_nonprofit(nonprofit_id)
        donors = self._donor_repo.list_for_nonprofit(nonprofit_id)

        highest_donation = 0.0
        biggest_donor_name = ""
        if donors:
            top = max(donors, key=lambda d: float(d.get("donation_amount") or 0))
            highest_donation = float(top.get("donation_amount") or 0)
            biggest_donor_name = top.get("name") or ""

        current = int(metrics.get("email_opens_current") or 0)
        previous = int(metrics.get("email_opens_previous") or 0)
        change = current - previous
        change_pct = round((change / previous) * 100, 1) if previous > 0 else 0.0

        return self.upsert(nonprofit_id, {
            "highest_donation": highest_donation,
            "biggest_donor_name": biggest_donor_name,
            "email_opens_change": change,
            "email_opens_change_pct": change_pct,
        })
