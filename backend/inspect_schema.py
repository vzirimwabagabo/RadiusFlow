from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

tables = db.execute(text(
    "SELECT table_name FROM information_schema.tables WHERE table_schema='radiusflow' ORDER BY table_name"
)).fetchall()
print("radiusflow tables:", [t[0] for t in tables])

has_sessions = db.execute(text(
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='radiusflow' AND table_name='admin_sessions'"
)).scalar()
print("admin_sessions exists:", bool(has_sessions))

if has_sessions:
    cols = db.execute(text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema='radiusflow' AND table_name='admin_sessions' ORDER BY ordinal_position"
    )).fetchall()
    print("admin_sessions columns:", cols)

# Check app_sessions FK
fk = db.execute(text(
    "SELECT constraint_name, column_name FROM information_schema.key_column_usage "
    "WHERE table_name='app_sessions' AND constraint_name LIKE '%fkey%'"
)).fetchall()
print("app_sessions FKs:", fk)

db.close()
