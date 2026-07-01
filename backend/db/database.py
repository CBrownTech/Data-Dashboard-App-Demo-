''' db/database.py — data-access dispatcher.

The repositories call the helpers here (query, query_one, dml, insert_row,
update_row, upsert, next_id, truncate) and never talk to a database driver
directly, so the service, route, and auth layers are unaffected by which backend
is active.

BACKEND SELECTION (DB_BACKEND env var):
  - "sqlite"   (default) — a local SQLite file. Zero cloud setup; ideal for demos
                and local development. Requires no credentials.
  - "bigquery"           — Google BigQuery. The production path. Requires
                BIGQUERY_PROJECT and GOOGLE_APPLICATION_CREDENTIALS.

Both backends expose the same operations; the repositories are written once
against this dispatcher. Reads return plain dicts; writes go through
INSERT/UPDATE/MERGE (or the SQLite equivalents). See db/bigquery_backend.py and
db/sqlite_backend.py.
'''
import os

from dotenv import load_dotenv

# Re-export the backend-neutral parameter helpers so repositories can keep
# importing them from db.database.
from db.params import Param, array_param, param  # noqa: F401

# Read .env before consulting the environment.
load_dotenv(override=True)

DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").strip().lower()

# BigQuery settings (only required when DB_BACKEND=bigquery).
PROJECT = os.getenv("BIGQUERY_PROJECT")
DATASET = os.getenv("BIGQUERY_DATASET", "bank_db")

if DB_BACKEND == "bigquery":
    from db import bigquery_backend as _backend
    _backend.configure(PROJECT, DATASET)
elif DB_BACKEND == "sqlite":
    from db import sqlite_backend as _backend
    _backend.configure(os.getenv("SQLITE_DB_PATH"))
else:
    raise RuntimeError(
        f"Unknown DB_BACKEND={DB_BACKEND!r}. Use 'sqlite' (local demo) or 'bigquery'."
    )


def table(name):
    ''' Backend-appropriate table reference for use inside SQL strings. '''
    return _backend.table_ref(name)


def query(sql, params=None):
    ''' Run SQL with named parameters; return rows as a list of plain dicts. '''
    return _backend.execute_query(sql, params or [])


def query_one(sql, params=None):
    ''' Return the first matching row as a dict, or None if nothing matched. '''
    rows = query(sql, params)
    return rows[0] if rows else None


def dml(sql, params=None):
    ''' Run an INSERT/UPDATE/DELETE/MERGE statement; return rows affected. '''
    return _backend.execute_dml(sql, params or [])


def insert_row(table_name, row, types):
    ''' INSERT a single row. `row` maps column->value; `types` maps column->type. '''
    return _backend.insert_row(table_name, row, types)


def update_row(table_name, key_col, key_val, key_type, updates, types):
    ''' UPDATE the single row where key_col == key_val. No-op if updates is empty. '''
    return _backend.update_row(table_name, key_col, key_val, key_type, updates, types)


def upsert(table_name, key_col, key_val, key_type, values, types):
    ''' Insert the row if the key is new, else update it (BQ MERGE / SQLite ON CONFLICT). '''
    return _backend.upsert(table_name, key_col, key_val, key_type, values, types)


def next_id(table_name, id_column):
    ''' Return MAX(id)+1 for a table — the integer-id replacement for counters.

    Not safe under concurrent writers; correct for this app's single-writer load.
    '''
    row = query_one(
        f"SELECT COALESCE(MAX({id_column}), 0) + 1 AS next_id FROM {table(table_name)}"
    )
    return int(row["next_id"])


def truncate(table_name):
    ''' Remove all rows from a table (used by the seed script). '''
    return _backend.truncate(table_name)


def get_client():
    ''' Return the underlying client (BigQuery backend only). '''
    return _backend.get_client()
