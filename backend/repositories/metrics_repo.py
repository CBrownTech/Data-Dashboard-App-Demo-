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
    "p2p_messages_sent": 0,
    "p2p_responses": 0,
    "p2p_opt_outs": 0,
    "p2p_response_rate": 0.0,
    "call_hours": 0.0,
    "calls_made": 0,
    "contacts_reached": 0,
    "call_avg_duration_minutes": 0.0,
    "email_donations": 0.0,
    "email_donation_count": 0,
    "p2p_donations": 0.0,
    "p2p_donation_count": 0,
    "call_donations": 0.0,
    "call_donation_count": 0,
}

WEEKLY_METRIC_FIELDS = (
    "email_opens",
    "p2p_messages_sent",
    "p2p_responses",
    "p2p_opt_outs",
    "call_hours",
    "calls_made",
    "contacts_reached",
    "donations_total",
    "email_donations",
    "p2p_donations",
    "call_donations",
    "donor_count",
    "active_volunteers",
    "volunteer_hours",
    "funding_raised",
)


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
            "p2p_messages_sent",
            "p2p_responses",
            "p2p_opt_outs",
            "p2p_response_rate",
            "call_hours",
            "calls_made",
            "contacts_reached",
            "call_avg_duration_minutes",
            "email_donations",
            "email_donation_count",
            "p2p_donations",
            "p2p_donation_count",
            "call_donations",
            "call_donation_count",
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

        messages_sent = int(metrics.get("p2p_messages_sent") or 0)
        responses = int(metrics.get("p2p_responses") or 0)
        response_rate = round((responses / messages_sent) * 100, 1) if messages_sent > 0 else 0.0

        return self.upsert(nonprofit_id, {
            "highest_donation": highest_donation,
            "biggest_donor_name": biggest_donor_name,
            "email_opens_change": change,
            "email_opens_change_pct": change_pct,
            "p2p_response_rate": response_rate,
        })

    def list_weekly(self, nonprofit_id, limit=6):
        cursor = (
            self._db.nonprofit_weekly_metrics.find({"nonprofit_id": nonprofit_id})
            .sort("week_start", -1)
            .limit(limit)
        )
        return list(cursor)

    def get_weekly_by_start(self, nonprofit_id, week_start):
        return self._db.nonprofit_weekly_metrics.find_one({
            "nonprofit_id": nonprofit_id,
            "week_start": week_start,
        })

    def replace_weekly_for_nonprofit(self, nonprofit_id, weeks):
        self._db.nonprofit_weekly_metrics.delete_many({"nonprofit_id": nonprofit_id})
        if not weeks:
            return []
        docs = []
        for week in weeks:
            doc = {"nonprofit_id": nonprofit_id, **week}
            docs.append(doc)
        if docs:
            self._db.nonprofit_weekly_metrics.insert_many(docs)
        return docs

    def delete_all_weekly(self):
        self._db.nonprofit_weekly_metrics.delete_many({})
