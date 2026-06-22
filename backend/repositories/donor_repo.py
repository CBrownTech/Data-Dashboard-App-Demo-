import re
from datetime import datetime, timezone

from pymongo import ReturnDocument

from db.database import get_mongo_db
from repositories.user_repo import _next_id


class DonorRepo:
    def __init__(self):
        self._db = get_mongo_db()

    def list_for_nonprofit(self, nonprofit_id, limit=None):
        cursor = self._db.donors.find({"nonprofit_id": nonprofit_id}).sort("donation_amount", -1)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def get_by_id(self, donor_id):
        return self._db.donors.find_one({"donor_id": donor_id})

    def get_by_email(self, nonprofit_id, email):
        if not email:
            return None
        return self._db.donors.find_one({
            "nonprofit_id": nonprofit_id,
            "email": {"$regex": f"^{re.escape(email.strip())}$", "$options": "i"},
        })

    def get_by_name_insensitive(self, nonprofit_id, name):
        if not name:
            return None
        return self._db.donors.find_one({
            "nonprofit_id": nonprofit_id,
            "name": {"$regex": f"^{re.escape(name.strip())}$", "$options": "i"},
        })

    def add(self, nonprofit_id, name, email, donation_amount):
        donor_id = _next_id(self._db, "donors")
        doc = {
            "donor_id": donor_id,
            "nonprofit_id": nonprofit_id,
            "name": name.strip(),
            "email": (email or "").strip(),
            "donation_amount": float(donation_amount or 0),
            "created_at": datetime.now(timezone.utc),
        }
        self._db.donors.insert_one(doc)
        return doc

    def update(self, donor_id, updates):
        allowed = {"name", "email", "donation_amount"}
        payload = {k: v for k, v in updates.items() if k in allowed}
        if not payload:
            return self.get_by_id(donor_id)
        return self._db.donors.find_one_and_update(
            {"donor_id": donor_id},
            {"$set": payload},
            return_document=ReturnDocument.AFTER,
        )
