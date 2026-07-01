from datetime import date, datetime, timezone

from db.database import dml, insert_row, param, query, query_one, table
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

# Column -> BigQuery type for the nonprofit_metrics table.
METRIC_TYPES = {
    "nonprofit_id": "INT64",
    "updated_at": "TIMESTAMP",
    "donor_count": "INT64",
    "total_donations": "FLOAT64",
    "active_volunteers": "INT64",
    "volunteer_hours": "INT64",
    "funding_goal": "FLOAT64",
    "funding_raised": "FLOAT64",
    "grants_received": "FLOAT64",
    "email_opens_current": "INT64",
    "email_opens_previous": "INT64",
    "highest_donation": "FLOAT64",
    "biggest_donor_name": "STRING",
    "email_opens_change": "INT64",
    "email_opens_change_pct": "FLOAT64",
    "p2p_messages_sent": "INT64",
    "p2p_responses": "INT64",
    "p2p_opt_outs": "INT64",
    "p2p_response_rate": "FLOAT64",
    "call_hours": "FLOAT64",
    "calls_made": "INT64",
    "contacts_reached": "INT64",
    "call_avg_duration_minutes": "FLOAT64",
    "email_donations": "FLOAT64",
    "email_donation_count": "INT64",
    "p2p_donations": "FLOAT64",
    "p2p_donation_count": "INT64",
    "call_donations": "FLOAT64",
    "call_donation_count": "INT64",
}

# Column -> BigQuery type for the nonprofit_weekly_metrics table.
WEEKLY_TYPES = {
    "nonprofit_id": "INT64",
    "week_start": "DATE",
    "email_opens": "INT64",
    "p2p_messages_sent": "INT64",
    "p2p_responses": "INT64",
    "p2p_opt_outs": "INT64",
    "call_hours": "FLOAT64",
    "calls_made": "INT64",
    "contacts_reached": "INT64",
    "donations_total": "FLOAT64",
    "email_donations": "FLOAT64",
    "p2p_donations": "FLOAT64",
    "call_donations": "FLOAT64",
    "donor_count": "INT64",
    "active_volunteers": "INT64",
    "volunteer_hours": "INT64",
    "funding_raised": "FLOAT64",
}

ALLOWED_METRIC_FIELDS = frozenset(METRIC_TYPES) - {"nonprofit_id", "updated_at"}


def _coerce(bq_type, value):
    ''' Coerce a Python value to match its BigQuery column type.

    JSON request bodies arrive as strings/ints/floats interchangeably; BigQuery
    rejects a float passed to an INT64 parameter, so normalize here.
    '''
    if value is None:
        return None
    if bq_type == "INT64":
        return int(value)
    if bq_type == "FLOAT64":
        return float(value)
    if bq_type == "DATE":
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        return date.fromisoformat(str(value)[:10])
    return value


class MetricsRepo:
    def __init__(self):
        self._donor_repo = DonorRepo()

    def get_for_nonprofit(self, nonprofit_id):
        doc = query_one(
            f"SELECT * FROM {table('nonprofit_metrics')} WHERE nonprofit_id = @np LIMIT 1",
            [param("np", "INT64", nonprofit_id)],
        )
        if doc:
            return doc
        return {"nonprofit_id": nonprofit_id, **DEFAULT_METRICS}

    def upsert(self, nonprofit_id, updates):
        payload = {
            k: _coerce(METRIC_TYPES[k], v)
            for k, v in updates.items()
            if k in ALLOWED_METRIC_FIELDS
        }
        now = datetime.now(timezone.utc)
        cols = list(payload.keys())

        # MERGE = update the row if this nonprofit already has metrics, else insert.
        set_clause = ", ".join([f"{c} = @{c}" for c in cols] + ["updated_at = @updated_at"])
        insert_cols = ["nonprofit_id", "updated_at"] + cols
        insert_vals = ["@nonprofit_id", "@updated_at"] + [f"@{c}" for c in cols]

        params = [
            param("nonprofit_id", "INT64", nonprofit_id),
            param("updated_at", "TIMESTAMP", now),
        ]
        params.extend(param(c, METRIC_TYPES[c], payload[c]) for c in cols)

        dml(
            f"""
            MERGE {table('nonprofit_metrics')} T
            USING (SELECT @nonprofit_id AS nonprofit_id) S
            ON T.nonprofit_id = S.nonprofit_id
            WHEN MATCHED THEN UPDATE SET {set_clause}
            WHEN NOT MATCHED THEN
                INSERT ({", ".join(insert_cols)}) VALUES ({", ".join(insert_vals)})
            """,
            params,
        )
        return self.get_for_nonprofit(nonprofit_id)

    def seed_defaults(self, nonprofit_id, metrics):
        now = datetime.now(timezone.utc)
        merged = {**DEFAULT_METRICS, **metrics}
        doc = {"nonprofit_id": nonprofit_id, "updated_at": now}
        for field, value in merged.items():
            if field in METRIC_TYPES:
                doc[field] = _coerce(METRIC_TYPES[field], value)
        insert_row("nonprofit_metrics", doc, METRIC_TYPES)
        return self.get_for_nonprofit(nonprofit_id)

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
        return query(
            f"""SELECT * FROM {table('nonprofit_weekly_metrics')}
                WHERE nonprofit_id = @np
                ORDER BY week_start DESC
                LIMIT @lim""",
            [param("np", "INT64", nonprofit_id), param("lim", "INT64", int(limit))],
        )

    def get_weekly_by_start(self, nonprofit_id, week_start):
        return query_one(
            f"""SELECT * FROM {table('nonprofit_weekly_metrics')}
                WHERE nonprofit_id = @np AND week_start = @ws LIMIT 1""",
            [
                param("np", "INT64", nonprofit_id),
                param("ws", "DATE", _coerce("DATE", week_start)),
            ],
        )

    def replace_weekly_for_nonprofit(self, nonprofit_id, weeks):
        dml(
            f"DELETE FROM {table('nonprofit_weekly_metrics')} WHERE nonprofit_id = @np",
            [param("np", "INT64", nonprofit_id)],
        )
        if not weeks:
            return []
        docs = []
        for week in weeks:
            doc = {"nonprofit_id": nonprofit_id}
            for field, value in week.items():
                if field in WEEKLY_TYPES:
                    doc[field] = _coerce(WEEKLY_TYPES[field], value)
            insert_row("nonprofit_weekly_metrics", doc, WEEKLY_TYPES)
            docs.append(doc)
        return docs

    def delete_all_weekly(self):
        dml(f"DELETE FROM {table('nonprofit_weekly_metrics')} WHERE TRUE")
