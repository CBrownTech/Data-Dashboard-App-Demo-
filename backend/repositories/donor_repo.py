from datetime import datetime, timezone

from db.database import insert_row, next_id, param, query, query_one, table, update_row

# Column -> BigQuery type for the donors table.
DONOR_TYPES = {
    "donor_id": "INT64",
    "nonprofit_id": "INT64",
    "name": "STRING",
    "email": "STRING",
    "donation_amount": "FLOAT64",
    "created_at": "TIMESTAMP",
}


class DonorRepo:
    def list_for_nonprofit(self, nonprofit_id, limit=None):
        sql = (
            f"SELECT * FROM {table('donors')} "
            f"WHERE nonprofit_id = @np ORDER BY donation_amount DESC"
        )
        params = [param("np", "INT64", nonprofit_id)]
        if limit:
            sql += " LIMIT @lim"
            params.append(param("lim", "INT64", int(limit)))
        return query(sql, params)

    def get_by_id(self, donor_id):
        return query_one(
            f"SELECT * FROM {table('donors')} WHERE donor_id = @id LIMIT 1",
            [param("id", "INT64", donor_id)],
        )

    def get_by_email(self, nonprofit_id, email):
        if not email:
            return None
        return query_one(
            f"""SELECT * FROM {table('donors')}
                WHERE nonprofit_id = @np AND LOWER(email) = LOWER(@email) LIMIT 1""",
            [param("np", "INT64", nonprofit_id), param("email", "STRING", email.strip())],
        )

    def get_by_name_insensitive(self, nonprofit_id, name):
        if not name:
            return None
        return query_one(
            f"""SELECT * FROM {table('donors')}
                WHERE nonprofit_id = @np AND LOWER(name) = LOWER(@name) LIMIT 1""",
            [param("np", "INT64", nonprofit_id), param("name", "STRING", name.strip())],
        )

    def add(self, nonprofit_id, name, email, donation_amount):
        donor_id = next_id("donors", "donor_id")
        doc = {
            "donor_id": donor_id,
            "nonprofit_id": nonprofit_id,
            "name": name.strip(),
            "email": (email or "").strip(),
            "donation_amount": float(donation_amount or 0),
            "created_at": datetime.now(timezone.utc),
        }
        insert_row("donors", doc, DONOR_TYPES)
        return self.get_by_id(donor_id)

    def update(self, donor_id, updates):
        allowed = {"name", "email", "donation_amount"}
        payload = {k: v for k, v in updates.items() if k in allowed}
        if not payload:
            return self.get_by_id(donor_id)
        if "donation_amount" in payload:
            payload["donation_amount"] = float(payload["donation_amount"] or 0)
        update_row("donors", "donor_id", donor_id, "INT64", payload, DONOR_TYPES)
        return self.get_by_id(donor_id)
