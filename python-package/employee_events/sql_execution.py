# flake8: noqa

# Database execution layer: entity classes construct SQL, while this module
# executes it against the packaged SQLite file and returns Python data.

from sqlite3 import connect
from pathlib import Path
from functools import wraps
import pandas as pd

# The database lives beside this module, independent of the working directory.
db_path = (Path(__file__).parent / "employee_events.db").resolve()


# Each method opens its own connection. The finally blocks close it even when
# SQL execution fails, keeping connection handling out of the entity classes.
class QueryMixin:

    # DataFrames retain SQL column names for charts, notes, and model features.
    def pandas_query(self, sql_query):
        connection = connect(db_path)
        try:
            df = pd.read_sql(sql_query, connection)
            return df
        finally:
            connection.close()

    # Tuple results support simple lookups such as dropdown (label, ID) pairs.
    def query(self, sql_query: str):
        connection = connect(db_path)
        try:
            cursor = connection.cursor()
            result = cursor.execute(sql_query).fetchall()
            return result
        finally:
            connection.close()


# Alternative interface for functions that return SQL strings: the decorator
# executes the returned SQL and substitutes its rows as the function result.
# Employee and Team currently use QueryMixin rather than this decorator.
def query(func):
    """
    Decorator that runs a standard sql execution
    and returns a list of tuples
    """

    # Preserve the wrapped function's name and documentation for introspection.
    @wraps(func)
    def run_query(*args, **kwargs):
        query_string = func(*args, **kwargs)
        connection = connect(db_path)
        cursor = connection.cursor()
        result = cursor.execute(query_string).fetchall()
        connection.close()
        return result

    return run_query
