# Data access for the users collection — MongoDB via PyMongo.
#
# KEY DIFFERENCES from the old SQLAlchemy version:
#   - No `session` parameter. MongoDB repos get their db handle in __init__,
#     not passed in per call. There is no shared transaction object to pass around.
#   - No model class (User). Documents are plain Python dicts.
#   - No session.add() / session.flush() / session.commit(). Writes go to
#     MongoDB immediately when you call insert_one() or update_one().
#   - Reads return dicts: {"user_id": 1, "name": "Jorge", ...}
#     The service layer accesses fields with dict notation: user["name"].
from datetime import datetime, timezone
from pymongo import ReturnDocument
from db.database import get_mongo_db


def _next_id(db, collection_name):
    ''' Generate the next auto-increment integer ID for a collection.

    MongoDB does not auto-generate integer primary keys — it uses ObjectId by
    default. Since our routes and frontend use integer IDs everywhere, we
    maintain a `counters` collection that tracks the last-used integer per
    collection name.

    find_one_and_update does this atomically in one round-trip:
      - $inc increments the `seq` field by 1.
      - upsert=True creates the counter document if it doesn't exist yet.
      - ReturnDocument.AFTER returns the document AFTER the increment,
        so we always get the new value (not the old one).

    Example counters collection:
      { "_id": "users",        "seq": 3 }
      { "_id": "accounts",     "seq": 5 }
      { "_id": "transactions", "seq": 12 }
    '''
    result = db.counters.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return result["seq"]


class UserRepo:
    def __init__(self):
        # Get the database handle once at startup.
        # mongo_db is a module-level singleton — this is safe and cheap.
        self._db = get_mongo_db()

    def get_user_by_email(self, email):
        # find_one returns a dict matching the filter, or None if not found.
        # {"email": email} is the MongoDB equivalent of WHERE email = ?
        return self._db.users.find_one({"email": email})

    def get_user_by_id(self, user_id):
        return self._db.users.find_one({"user_id": user_id})

    def get_all_users(self):
        # find() with no filter returns all documents as a cursor.
        # list() materializes the cursor into a Python list of dicts.
        return list(self._db.users.find())

    def soft_delete(self, user_id):
        # update_one finds the first matching document and applies the update.
        # $set only touches the specified fields — all other fields are unchanged.
        # This is the MongoDB equivalent of:
        #   UPDATE users SET is_deleted=TRUE, deleted_at=NOW() WHERE user_id=?
        now = datetime.now(timezone.utc)
        result = self._db.users.find_one_and_update(
            {"user_id": user_id},
            {"$set": {"is_deleted": True, "deleted_at": now}},
            return_document=ReturnDocument.AFTER  # return the updated document
        )
        # result is None if no document matched — service layer checks for this.
        return result

    def reactivate_user(self, user_id, name, password_hash=None):
        # Restore a soft-deleted user so they can sign in again.
        # Called when someone re-registers with an email that was deactivated.
        update = {
            "is_deleted": False,
            "deleted_at": None,
            "name":         name,
            "password_hash": password_hash,
        }
        return self._db.users.find_one_and_update(
            {"user_id": user_id},
            {"$set": update},
            return_document=ReturnDocument.AFTER
        )

    def update_user(self, user_id, updates):
        allowed = {"role", "nonprofit_id", "is_admin", "name", "email"}
        payload = {k: v for k, v in updates.items() if k in allowed}
        if not payload:
            return self.get_user_by_id(user_id)
        return self._db.users.find_one_and_update(
            {"user_id": user_id},
            {"$set": payload},
            return_document=ReturnDocument.AFTER,
        )

    def add_user(self, name, email, password_hash=None, role="nonprofit_user", nonprofit_id=None, is_admin=False):
        user_id = _next_id(self._db, "users")
        doc = {
            "user_id":       user_id,
            "name":          name,
            "email":         email,
            "password_hash": password_hash,
            "is_admin":      is_admin,
            "role":          role,
            "nonprofit_id":  nonprofit_id,
            "is_deleted":    False,
            "deleted_at":    None,
            "created_at":    datetime.now(timezone.utc),
        }
        # insert_one writes the document immediately — no commit needed.
        # MongoDB also adds an `_id` (ObjectId) field automatically, but we
        # don't use it — our app identifies users by the integer user_id.
        self._db.users.insert_one(doc)
        return doc
