from datetime import datetime, timezone

from db.database import (
    array_param,
    insert_row,
    next_id,
    param,
    query,
    query_one,
    table,
    update_row,
)

# Column -> BigQuery type for the nonprofits table.
NONPROFIT_TYPES = {
    "nonprofit_id": "INT64",
    "name": "STRING",
    "slug": "STRING",
    "mission": "STRING",
    "location": "STRING",
    "reference_code": "STRING",
    "source_code": "STRING",
    "is_active": "BOOL",
    "created_at": "TIMESTAMP",
}


class NonprofitRepo:
    def list_all(self, include_inactive=False):
        where = "" if include_inactive else "WHERE is_active = TRUE"
        return query(f"SELECT * FROM {table('nonprofits')} {where} ORDER BY name")

    def list_by_ids(self, nonprofit_ids):
        ids = list(nonprofit_ids)
        if not ids:
            return []
        return query(
            f"SELECT * FROM {table('nonprofits')} WHERE nonprofit_id IN UNNEST(@ids)",
            [array_param("ids", "INT64", ids)],
        )

    def get_by_id(self, nonprofit_id):
        return query_one(
            f"SELECT * FROM {table('nonprofits')} WHERE nonprofit_id = @id LIMIT 1",
            [param("id", "INT64", nonprofit_id)],
        )

    def get_by_slug(self, slug):
        return query_one(
            f"SELECT * FROM {table('nonprofits')} WHERE slug = @slug LIMIT 1",
            [param("slug", "STRING", slug)],
        )

    def get_by_name_insensitive(self, name):
        # Mongo regex ^name$ /i == case-insensitive equality here.
        return query_one(
            f"SELECT * FROM {table('nonprofits')} WHERE LOWER(name) = LOWER(@name) LIMIT 1",
            [param("name", "STRING", name)],
        )

    def add(self, name, slug, mission, location, reference_code="", source_code=""):
        nonprofit_id = next_id("nonprofits", "nonprofit_id")
        doc = {
            "nonprofit_id": nonprofit_id,
            "name": name,
            "slug": slug,
            "mission": mission,
            "location": location,
            "reference_code": reference_code or "",
            "source_code": source_code or "",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        insert_row("nonprofits", doc, NONPROFIT_TYPES)
        return self.get_by_id(nonprofit_id)

    def update(self, nonprofit_id, updates):
        allowed = {"name", "slug", "mission", "location", "is_active", "reference_code", "source_code"}
        payload = {k: v for k, v in updates.items() if k in allowed}
        if not payload:
            return self.get_by_id(nonprofit_id)
        update_row("nonprofits", "nonprofit_id", nonprofit_id, "INT64", payload, NONPROFIT_TYPES)
        return self.get_by_id(nonprofit_id)
