''' db/params.py — backend-neutral query parameter.

Repositories build parameters with param()/array_param() without knowing which
database backend is active. Each backend converts these into its own native
form: the BigQuery backend into ScalarQueryParameter/ArrayQueryParameter, the
SQLite backend into a name->value bind dict.

`type` is a BigQuery scalar type string (e.g. "STRING", "INT64", "FLOAT64",
"TIMESTAMP", "DATE"). The SQLite backend ignores it — it relies on Python value
types and column declarations instead — but it is kept so the same call site
works for both backends.
'''


class Param:
    __slots__ = ("name", "type", "value", "is_array")

    def __init__(self, name, type, value, is_array=False):
        self.name = name
        self.type = type
        self.value = value
        self.is_array = is_array


def param(name, type_, value):
    ''' A scalar parameter, e.g. param("email", "STRING", email). '''
    return Param(name, type_, value, is_array=False)


def array_param(name, type_, values):
    ''' An array parameter for `col IN UNNEST(@name)` clauses. '''
    return Param(name, type_, list(values), is_array=True)
