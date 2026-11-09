# flake8: noqa

# Smoke checks for the bundled database: the file and three core tables exist.
# These tests do not exercise query results, model predictions, or dashboard routes.

import pytest
from pathlib import Path

# Locate the repository relative to this test file during normal pytest runs.
try:
    project_root = Path(__file__).parent.parent
except NameError:
    # Interactive execution may lack __file__; this fallback assumes the current
    # directory is one level below the repository root.
    project_root = Path.cwd().parent
print(f"Project Root is: {project_root}")


# Pytest injects fixtures by parameter name. This path fixture is the start
# of the dependency chain: db_path -> db_conn -> table_names -> table checks.
@pytest.fixture
def db_path():
    path_return = (
        project_root / "python-package" / "employee_events" / "employee_events.db"
    )
    return path_return


# Check that the database artifact is present, independently of its contents.
def test_db_exists(db_path):

    assert db_path.is_file()


# Each requesting test gets a connection to the bundled database; the tests
# below only inspect SQLite metadata and do not insert or update application data.
@pytest.fixture
def db_conn(db_path):
    from sqlite3 import connect

    return connect(db_path)


@pytest.fixture
def table_names(db_conn):
    # Read the actual table catalog and flatten the one-column tuple results
    # into strings so the tests can check membership by table name.
    name_tuples = db_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table';"
    ).fetchall()
    return [x[0] for x in name_tuples]


# These checks establish schema presence only, not columns, keys, or row counts.
def test_employee_table_exists(table_names):

    assert "employee" in table_names


def test_team_table_exists(table_names):

    assert "team" in table_names


def test_employee_events_table_exists(table_names):

    assert "employee_events" in table_names
