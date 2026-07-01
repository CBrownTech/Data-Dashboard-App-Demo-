''' db/bigquery_backend.py — Google BigQuery implementation of the data backend.

This is the production backend. It is only imported when DB_BACKEND=bigquery, so
the local SQLite demo does not require google-cloud-bigquery to be configured.

WHY DML (INSERT/UPDATE/MERGE) INSTEAD OF THE STREAMING API:
  Rows written with BigQuery's streaming insert API sit in a streaming buffer and
  cannot be UPDATE-d or DELETE-d for up to ~90 minutes. This app frequently
  inserts a row and mutates it moments later (e.g. create a nonprofit, then upsert
  its metrics), so every write uses an INSERT/UPDATE/MERGE DML statement, whose
  rows are immediately queryable and mutable.
'''
from google.cloud import bigquery

from db.params import param

_client = None
_project = None
_dataset = None


def configure(project, dataset):
    global _client, _project, _dataset
    if not project:
        raise RuntimeError(
            "BIGQUERY_PROJECT is not set. Set it in .env (with GOOGLE_APPLICATION_CREDENTIALS) "
            "or use DB_BACKEND=sqlite to run the local demo."
        )
    _project = project
    _dataset = dataset
    # Authenticates from GOOGLE_APPLICATION_CREDENTIALS automatically.
    _client = bigquery.Client(project=project)


def get_client():
    return _client


def table_ref(name):
    return f"`{_project}.{_dataset}.{name}`"


def _to_native(params):
    native = []
    for p in params:
        if p.is_array:
            native.append(bigquery.ArrayQueryParameter(p.name, p.type, p.value))
        else:
            native.append(bigquery.ScalarQueryParameter(p.name, p.type, p.value))
    return native


def execute_query(sql, params):
    job_config = bigquery.QueryJobConfig(query_parameters=_to_native(params))
    job = _client.query(sql, job_config=job_config)
    return [dict(row) for row in job.result()]


def execute_dml(sql, params):
    job_config = bigquery.QueryJobConfig(query_parameters=_to_native(params))
    job = _client.query(sql, job_config=job_config)
    job.result()
    return job.num_dml_affected_rows or 0


def insert_row(table_name, row, types):
    cols = list(row.keys())
    col_list = ", ".join(cols)
    val_list = ", ".join(f"@{c}" for c in cols)
    execute_dml(
        f"INSERT INTO {table_ref(table_name)} ({col_list}) VALUES ({val_list})",
        [param(c, types[c], row[c]) for c in cols],
    )


def update_row(table_name, key_col, key_val, key_type, updates, types):
    if not updates:
        return False
    sets = ", ".join(f"{c}=@{c}" for c in updates)
    params = [param(c, types[c], v) for c, v in updates.items()]
    params.append(param("__key", key_type, key_val))
    affected = execute_dml(
        f"UPDATE {table_ref(table_name)} SET {sets} WHERE {key_col}=@__key",
        params,
    )
    return affected > 0


def upsert(table_name, key_col, key_val, key_type, values, types):
    ''' Insert the row if the key is new, else update it — via a MERGE statement. '''
    cols = [c for c in values if c != key_col]
    set_clause = ", ".join(f"{c}=@{c}" for c in cols) or f"{key_col}=@{key_col}"
    insert_cols = [key_col] + cols
    insert_vals = [f"@{key_col}"] + [f"@{c}" for c in cols]

    params = [param(key_col, key_type, key_val)]
    params.extend(param(c, types[c], values[c]) for c in cols)

    execute_dml(
        f"""
        MERGE {table_ref(table_name)} T
        USING (SELECT @{key_col} AS {key_col}) S
        ON T.{key_col} = S.{key_col}
        WHEN MATCHED THEN UPDATE SET {set_clause}
        WHEN NOT MATCHED THEN
            INSERT ({", ".join(insert_cols)}) VALUES ({", ".join(insert_vals)})
        """,
        params,
    )


def truncate(table_name):
    execute_dml(f"TRUNCATE TABLE {table_ref(table_name)}")
