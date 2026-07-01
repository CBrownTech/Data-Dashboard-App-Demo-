from datetime import datetime, timezone

from db.database import dml, insert_row, next_id, param, query, query_one, table, update_row

# Column -> BigQuery type for the programs table.
PROGRAM_TYPES = {
    "program_id": "INT64",
    "nonprofit_id": "INT64",
    "name": "STRING",
    "status": "STRING",
    "participants": "INT64",
    "budget": "FLOAT64",
    "created_at": "TIMESTAMP",
}


class ProgramRepo:
    def list_for_nonprofit(self, nonprofit_id):
        return query(
            f"SELECT * FROM {table('programs')} WHERE nonprofit_id = @np ORDER BY name",
            [param("np", "INT64", nonprofit_id)],
        )

    def get_by_id(self, program_id):
        return query_one(
            f"SELECT * FROM {table('programs')} WHERE program_id = @id LIMIT 1",
            [param("id", "INT64", program_id)],
        )

    def get_by_name(self, nonprofit_id, name):
        return query_one(
            f"""SELECT * FROM {table('programs')}
                WHERE nonprofit_id = @np AND LOWER(name) = LOWER(@name) LIMIT 1""",
            [param("np", "INT64", nonprofit_id), param("name", "STRING", name)],
        )

    def add(self, nonprofit_id, name, status, participants, budget):
        program_id = next_id("programs", "program_id")
        doc = {
            "program_id": program_id,
            "nonprofit_id": nonprofit_id,
            "name": name,
            "status": status,
            "participants": int(participants or 0),
            "budget": float(budget or 0),
            "created_at": datetime.now(timezone.utc),
        }
        insert_row("programs", doc, PROGRAM_TYPES)
        return self.get_by_id(program_id)

    def update(self, program_id, updates):
        allowed = {"name", "status", "participants", "budget"}
        payload = {k: v for k, v in updates.items() if k in allowed}
        if not payload:
            return self.get_by_id(program_id)
        if "participants" in payload:
            payload["participants"] = int(payload["participants"] or 0)
        if "budget" in payload:
            payload["budget"] = float(payload["budget"] or 0)
        update_row("programs", "program_id", program_id, "INT64", payload, PROGRAM_TYPES)
        return self.get_by_id(program_id)

    def delete(self, program_id):
        affected = dml(
            f"DELETE FROM {table('programs')} WHERE program_id = @id",
            [param("id", "INT64", program_id)],
        )
        return affected > 0
