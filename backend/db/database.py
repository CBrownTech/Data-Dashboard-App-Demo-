''' db/database.py — BigQuery connection and query helpers.

This replaces the previous MongoDB (PyMongo) setup. The repositories call the
helpers defined here instead of talking to a database driver directly, so the
service and route layers are unaffected by the switch.

HOW THE CONNECTION WORKS:
  1. load_dotenv() reads the .env file and injects BIGQUERY_PROJECT,
     BIGQUERY_DATASET, and GOOGLE_APPLICATION_CREDENTIALS into the environment.
  2. bigquery.Client() authenticates using the service-account JSON key pointed
     at by GOOGLE_APPLICATION_CREDENTIALS — once at module load.
  3. Repositories call query()/query_one()/insert_row()/update_row()/next_id().

WHY DML (INSERT/UPDATE/MERGE) INSTEAD OF THE STREAMING API:
  Rows written with BigQuery's streaming insert API sit in a streaming buffer
  and cannot be UPDATE-d or DELETE-d for up to ~90 minutes. This app frequently
  inserts a row and mutates it moments later (e.g. create a nonprofit, then
  upsert its metrics), so every write here uses an INSERT/UPDATE/MERGE DML
  statement, whose rows are immediately queryable and mutable.

WHY INTEGER IDS VIA MAX()+1:
  MongoDB used a `counters` collection for auto-increment ids. BigQuery has no
  auto-increment, so next_id() computes MAX(id)+1. This preserves the integer-id
  contract the frontend depends on. It is not safe under concurrent writers, but
  it is correct for this demo's single-writer load.
'''
import os

from dotenv import load_dotenv
from google.cloud import bigquery

# Read .env and load its variables into os.environ before we read them.
load_dotenv(override=True)

PROJECT = os.getenv("BIGQUERY_PROJECT")
DATASET = os.getenv("BIGQUERY_DATASET", "bank_db")

if not PROJECT:
    raise RuntimeError(
        "BIGQUERY_PROJECT is not set. Copy .env.example to .env and fill in your "
        "GCP project id, dataset, and GOOGLE_APPLICATION_CREDENTIALS path."
    )

# The BigQuery client — created once, reused for every request. It picks up the
# service-account credentials from GOOGLE_APPLICATION_CREDENTIALS automatically.
_client = bigquery.Client(project=PROJECT)


def get_client():
    ''' Return the shared BigQuery client. '''
    return _client


def table(name):
    ''' Fully-qualified `project.dataset.table` reference for use inside SQL. '''
    return f"`{PROJECT}.{DATASET}.{name}`"


def param(name, type_, value):
    ''' Build a scalar query parameter, e.g. param("email", "STRING", email). '''
    return bigquery.ScalarQueryParameter(name, type_, value)


def array_param(name, type_, values):
    ''' Build an array query parameter for `col IN UNNEST(@name)` clauses. '''
    return bigquery.ArrayQueryParameter(name, type_, list(values))


def query(sql, params=None):
    ''' Run SQL with named parameters; return rows as a list of plain dicts. '''
    job_config = bigquery.QueryJobConfig(query_parameters=params or [])
    job = _client.query(sql, job_config=job_config)
    rows = job.result()
    return [dict(row) for row in rows]


def query_one(sql, params=None):
    ''' Return the first matching row as a dict, or None if nothing matched. '''
    rows = query(sql, params)
    return rows[0] if rows else None


def dml(sql, params=None):
    ''' Run an INSERT/UPDATE/DELETE/MERGE statement; return rows affected. '''
    job_config = bigquery.QueryJobConfig(query_parameters=params or [])
    job = _client.query(sql, job_config=job_config)
    job.result()
    return job.num_dml_affected_rows or 0


def insert_row(table_name, row, types):
    ''' INSERT a single row.

    `row`   maps column name -> value.
    `types` maps column name -> BigQuery scalar type (e.g. "INT64", "STRING").
    '''
    cols = list(row.keys())
    col_list = ", ".join(cols)
    val_list = ", ".join(f"@{c}" for c in cols)
    params = [param(c, types[c], row[c]) for c in cols]
    dml(f"INSERT INTO {table(table_name)} ({col_list}) VALUES ({val_list})", params)


def update_row(table_name, key_col, key_val, key_type, updates, types):
    ''' UPDATE columns for the single row where key_col == key_val.

    No-op (returns False) when `updates` is empty.
    '''
    if not updates:
        return False
    sets = ", ".join(f"{c}=@{c}" for c in updates)
    params = [param(c, types[c], v) for c, v in updates.items()]
    params.append(param("__key", key_type, key_val))
    affected = dml(
        f"UPDATE {table(table_name)} SET {sets} WHERE {key_col}=@__key",
        params,
    )
    return affected > 0


def next_id(table_name, id_column):
    ''' Return MAX(id)+1 for a table — the integer-id replacement for counters. '''
    row = query_one(
        f"SELECT COALESCE(MAX({id_column}), 0) + 1 AS next_id FROM {table(table_name)}"
    )
    return int(row["next_id"])


def truncate(table_name):
    ''' Remove all rows from a table (used by the seed script). '''
    dml(f"TRUNCATE TABLE {table(table_name)}")
