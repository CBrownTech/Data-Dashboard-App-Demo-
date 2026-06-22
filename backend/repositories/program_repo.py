from datetime import datetime, timezone

import re

from pymongo import ReturnDocument

from db.database import get_mongo_db
from repositories.user_repo import _next_id


class ProgramRepo:
    def __init__(self):
        self._db = get_mongo_db()

    def list_for_nonprofit(self, nonprofit_id):
        return list(
            self._db.programs.find({"nonprofit_id": nonprofit_id}).sort("name", 1)
        )

    def get_by_id(self, program_id):
        return self._db.programs.find_one({"program_id": program_id})

    def get_by_name(self, nonprofit_id, name):
        return self._db.programs.find_one({
            "nonprofit_id": nonprofit_id,
            "name": {"$regex": f"^{re.escape(name)}$", "$options": "i"},
        })

    def add(self, nonprofit_id, name, status, participants, budget):
        program_id = _next_id(self._db, "programs")
        doc = {
            "program_id": program_id,
            "nonprofit_id": nonprofit_id,
            "name": name,
            "status": status,
            "participants": participants,
            "budget": budget,
            "created_at": datetime.now(timezone.utc),
        }
        self._db.programs.insert_one(doc)
        return doc

    def update(self, program_id, updates):
        allowed = {"name", "status", "participants", "budget"}
        payload = {k: v for k, v in updates.items() if k in allowed}
        if not payload:
            return self.get_by_id(program_id)
        return self._db.programs.find_one_and_update(
            {"program_id": program_id},
            {"$set": payload},
            return_document=ReturnDocument.AFTER,
        )

    def delete(self, program_id):
        result = self._db.programs.delete_one({"program_id": program_id})
        return result.deleted_count > 0
