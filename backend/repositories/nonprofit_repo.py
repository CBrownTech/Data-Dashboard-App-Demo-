from datetime import datetime, timezone

import re

from pymongo import ReturnDocument

from db.database import get_mongo_db
from repositories.user_repo import _next_id


class NonprofitRepo:
    def __init__(self):
        self._db = get_mongo_db()

    def list_all(self, include_inactive=False):
        query = {}
        if not include_inactive:
            query["is_active"] = True
        return list(self._db.nonprofits.find(query).sort("name", 1))

    def list_by_ids(self, nonprofit_ids):
        if not nonprofit_ids:
            return []
        return list(self._db.nonprofits.find({"nonprofit_id": {"$in": list(nonprofit_ids)}}))

    def get_by_id(self, nonprofit_id):
        return self._db.nonprofits.find_one({"nonprofit_id": nonprofit_id})

    def get_by_slug(self, slug):
        return self._db.nonprofits.find_one({"slug": slug})

    def get_by_name_insensitive(self, name):
        return self._db.nonprofits.find_one({
            "name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}
        })

    def add(self, name, slug, mission, location):
        nonprofit_id = _next_id(self._db, "nonprofits")
        doc = {
            "nonprofit_id": nonprofit_id,
            "name": name,
            "slug": slug,
            "mission": mission,
            "location": location,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        self._db.nonprofits.insert_one(doc)
        return doc

    def update(self, nonprofit_id, updates):
        allowed = {"name", "slug", "mission", "location", "is_active"}
        payload = {k: v for k, v in updates.items() if k in allowed}
        if not payload:
            return self.get_by_id(nonprofit_id)
        return self._db.nonprofits.find_one_and_update(
            {"nonprofit_id": nonprofit_id},
            {"$set": payload},
            return_document=ReturnDocument.AFTER,
        )
