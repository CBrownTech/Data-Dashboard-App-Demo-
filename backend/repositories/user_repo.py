# Data access for the users table — BigQuery via google-cloud-bigquery.
#
# KEY POINTS for this BigQuery version:
#   - Reads return plain dicts: {"user_id": 1, "name": "Jorge", ...}, exactly as
#     the old PyMongo version did, so the service layer is unchanged.
#   - Writes use INSERT/UPDATE DML statements (see db/database.py for why), then
#     re-SELECT the row so callers still get the full document back, matching the
#     old find_one_and_update(return_document=AFTER) behaviour.
#   - Integer ids come from next_id() (MAX+1), replacing Mongo's counters.
from datetime import datetime, timezone

from db.database import insert_row, next_id, param, query, query_one, table, update_row

# Column -> BigQuery type for the users table. Used to type query parameters.
USER_TYPES = {
    "user_id": "INT64",
    "name": "STRING",
    "email": "STRING",
    "password_hash": "STRING",
    "is_admin": "BOOL",
    "role": "STRING",
    "nonprofit_id": "INT64",
    "is_deleted": "BOOL",
    "deleted_at": "TIMESTAMP",
    "created_at": "TIMESTAMP",
}


class UserRepo:
    def get_user_by_email(self, email):
        # {"email": email} in Mongo == WHERE email = @email here.
        return query_one(
            f"SELECT * FROM {table('users')} WHERE email = @email LIMIT 1",
            [param("email", "STRING", email)],
        )

    def get_user_by_id(self, user_id):
        return query_one(
            f"SELECT * FROM {table('users')} WHERE user_id = @id LIMIT 1",
            [param("id", "INT64", user_id)],
        )

    def get_all_users(self):
        return query(f"SELECT * FROM {table('users')}")

    def list_for_nonprofit(self, nonprofit_id):
        return query(
            f"""SELECT * FROM {table('users')}
                WHERE nonprofit_id = @np AND IFNULL(is_deleted, FALSE) = FALSE
                ORDER BY name""",
            [param("np", "INT64", nonprofit_id)],
        )

    def soft_delete(self, user_id):
        # UPDATE users SET is_deleted=TRUE, deleted_at=NOW() WHERE user_id=?
        now = datetime.now(timezone.utc)
        update_row(
            "users", "user_id", user_id, "INT64",
            {"is_deleted": True, "deleted_at": now},
            USER_TYPES,
        )
        return self.get_user_by_id(user_id)

    def reactivate_user(self, user_id, name, password_hash=None):
        # Restore a soft-deleted user so they can sign in again.
        update_row(
            "users", "user_id", user_id, "INT64",
            {
                "is_deleted": False,
                "deleted_at": None,
                "name": name,
                "password_hash": password_hash,
            },
            USER_TYPES,
        )
        return self.get_user_by_id(user_id)

    def update_user(self, user_id, updates):
        allowed = {"role", "nonprofit_id", "is_admin", "name", "email", "password_hash"}
        payload = {k: v for k, v in updates.items() if k in allowed}
        if not payload:
            return self.get_user_by_id(user_id)
        update_row("users", "user_id", user_id, "INT64", payload, USER_TYPES)
        return self.get_user_by_id(user_id)

    def add_user(self, name, email, password_hash=None, role="nonprofit_user", nonprofit_id=None, is_admin=False):
        user_id = next_id("users", "user_id")
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
        insert_row("users", doc, USER_TYPES)
        return self.get_user_by_id(user_id)
