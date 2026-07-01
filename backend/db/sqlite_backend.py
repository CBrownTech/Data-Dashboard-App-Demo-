''' db/sqlite_backend.py — local SQLite implementation of the data backend.

This backend exists so the app can run for a demo with zero cloud setup
(DB_BACKEND=sqlite, the default). It stores data in a local file so the seed
script and the server — separate processes — share the same data.

It deliberately accepts the same BigQuery-flavored SQL the repositories emit and
translates the small set of dialect differences the app actually uses:
  - named params:     @name        -> :name
  - array membership: IN UNNEST(@x) -> IN (:x_0, :x_1, ...)
  - upserts:          handled by upsert() as INSERT ... ON CONFLICT
  - truncation:       handled by truncate() as DELETE FROM
Everything else (SELECT *, WHERE, LOWER, IFNULL, COALESCE, MAX, ORDER BY, LIMIT,
TRUE/FALSE) is valid in modern SQLite as-is.

The BigQuery backend remains the production path; nothing here changes it.
'''
import os
import re
import sqlite3
import threading
from datetime import date, datetime

# CREATE TABLE bodies. Declared types (TIMESTAMP/DATE) drive the converters
# registered below so reads return datetime/date objects, matching what the
# BigQuery client returns. Integer primary keys mirror the app's integer IDs.
SCHEMA = {
    "users": """
        user_id INTEGER PRIMARY KEY, name TEXT, email TEXT, password_hash TEXT,
        is_admin BOOL, role TEXT, nonprofit_id INTEGER,
        is_deleted BOOL, deleted_at TIMESTAMP, created_at TIMESTAMP
    """,
    "nonprofits": """
        nonprofit_id INTEGER PRIMARY KEY, name TEXT, slug TEXT, mission TEXT, location TEXT,
        reference_code TEXT, source_code TEXT, is_active BOOL, created_at TIMESTAMP
    """,
    "donors": """
        donor_id INTEGER PRIMARY KEY, nonprofit_id INTEGER, name TEXT, email TEXT,
        donation_amount REAL, created_at TIMESTAMP
    """,
    "programs": """
        program_id INTEGER PRIMARY KEY, nonprofit_id INTEGER, name TEXT, status TEXT,
        participants INTEGER, budget REAL, created_at TIMESTAMP
    """,
    "nonprofit_metrics": """
        nonprofit_id INTEGER PRIMARY KEY, updated_at TIMESTAMP,
        donor_count INTEGER, total_donations REAL, active_volunteers INTEGER, volunteer_hours INTEGER,
        funding_goal REAL, funding_raised REAL, grants_received REAL,
        email_opens_current INTEGER, email_opens_previous INTEGER, highest_donation REAL,
        biggest_donor_name TEXT, email_opens_change INTEGER, email_opens_change_pct REAL,
        p2p_messages_sent INTEGER, p2p_responses INTEGER, p2p_opt_outs INTEGER, p2p_response_rate REAL,
        call_hours REAL, calls_made INTEGER, contacts_reached INTEGER, call_avg_duration_minutes REAL,
        email_donations REAL, email_donation_count INTEGER, p2p_donations REAL, p2p_donation_count INTEGER,
        call_donations REAL, call_donation_count INTEGER
    """,
    "nonprofit_weekly_metrics": """
        nonprofit_id INTEGER, week_start DATE,
        email_opens INTEGER, p2p_messages_sent INTEGER, p2p_responses INTEGER, p2p_opt_outs INTEGER,
        call_hours REAL, calls_made INTEGER, contacts_reached INTEGER,
        donations_total REAL, email_donations REAL, p2p_donations REAL, call_donations REAL,
        donor_count INTEGER, active_volunteers INTEGER, volunteer_hours INTEGER, funding_raised REAL
    """,
}

# Columns that should read back as Python bool rather than 0/1.
BOOL_COLUMNS = {"is_admin", "is_deleted", "is_active"}

_conn = None
_lock = threading.Lock()
_path = None


def configure(path):
    global _conn, _path
    _path = path or os.path.join(os.path.dirname(os.path.dirname(__file__)), "local_demo.db")

    # Store datetimes/dates as ISO text and parse them back on read, so callers
    # receive datetime/date objects (the service layer calls .isoformat()).
    sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
    sqlite3.register_adapter(date, lambda d: d.isoformat())
    sqlite3.register_converter("TIMESTAMP", lambda b: datetime.fromisoformat(b.decode()))
    sqlite3.register_converter("DATE", lambda b: date.fromisoformat(b.decode()))

    _conn = sqlite3.connect(_path, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _ensure_schema()


def _ensure_schema():
    with _lock:
        for name, cols in SCHEMA.items():
            _conn.execute(f"CREATE TABLE IF NOT EXISTS {name} ({cols})")
        _conn.commit()


def get_client():
    raise RuntimeError("get_client() is only available with the BigQuery backend.")


def table_ref(name):
    return name


def _row_to_dict(row):
    d = dict(row)
    for key in BOOL_COLUMNS:
        if d.get(key) is not None:
            d[key] = bool(d[key])
    return d


def _translate(sql, params):
    ''' Convert BigQuery-style SQL + Param list into SQLite SQL + bind dict. '''
    binds = {}
    for p in params:
        if p.is_array:
            placeholders = []
            for i, value in enumerate(p.value):
                key = f"{p.name}_{i}"
                binds[key] = value
                placeholders.append(f":{key}")
            replacement = "(" + ", ".join(placeholders) + ")" if placeholders else "(NULL)"
            sql = re.sub(rf"UNNEST\(@{re.escape(p.name)}\)", replacement, sql)
        else:
            binds[p.name] = p.value
    sql = re.sub(r"@(\w+)", r":\1", sql)
    return sql, binds


def execute_query(sql, params):
    tsql, binds = _translate(sql, params)
    with _lock:
        rows = _conn.execute(tsql, binds).fetchall()
    return [_row_to_dict(r) for r in rows]


def execute_dml(sql, params):
    tsql, binds = _translate(sql, params)
    with _lock:
        cur = _conn.execute(tsql, binds)
        _conn.commit()
    return cur.rowcount if cur.rowcount is not None and cur.rowcount >= 0 else 0


def insert_row(table_name, row, types):
    cols = list(row.keys())
    col_list = ", ".join(cols)
    val_list = ", ".join(f":{c}" for c in cols)
    with _lock:
        _conn.execute(f"INSERT INTO {table_name} ({col_list}) VALUES ({val_list})", dict(row))
        _conn.commit()


def update_row(table_name, key_col, key_val, key_type, updates, types):
    if not updates:
        return False
    sets = ", ".join(f"{c}=:{c}" for c in updates)
    binds = dict(updates)
    binds["__key"] = key_val
    with _lock:
        cur = _conn.execute(f"UPDATE {table_name} SET {sets} WHERE {key_col}=:__key", binds)
        _conn.commit()
    return cur.rowcount > 0


def upsert(table_name, key_col, key_val, key_type, values, types):
    cols = [c for c in values if c != key_col]
    all_cols = [key_col] + cols
    col_list = ", ".join(all_cols)
    val_list = ", ".join(f":{c}" for c in all_cols)
    set_clause = ", ".join(f"{c}=excluded.{c}" for c in cols) or f"{key_col}={key_col}"
    binds = {key_col: key_val}
    binds.update({c: values[c] for c in cols})
    with _lock:
        _conn.execute(
            f"INSERT INTO {table_name} ({col_list}) VALUES ({val_list}) "
            f"ON CONFLICT({key_col}) DO UPDATE SET {set_clause}",
            binds,
        )
        _conn.commit()


def truncate(table_name):
    with _lock:
        _conn.execute(f"DELETE FROM {table_name}")
        _conn.commit()
