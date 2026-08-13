import sys
from pathlib import Path
from sqlalchemy import event
from sqlalchemy.engine import Engine

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@event.listens_for(Engine, "before_cursor_execute", retval=True)
def _strip_radiusflow_schema_for_sqlite(conn, cursor, statement, parameters, context, execmany):
    if conn.dialect.name == "sqlite" and "radiusflow." in statement:
        statement = statement.replace("radiusflow.", "")
    return statement, parameters
