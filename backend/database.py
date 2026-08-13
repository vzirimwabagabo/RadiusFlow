"""Database connection — SQLAlchemy engine and session factory."""
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@event.listens_for(Engine, "before_cursor_execute", retval=True)
def _strip_radiusflow_schema_for_sqlite(conn, cursor, statement, parameters, context, execmany):
    if conn.dialect.name == "sqlite" and "radiusflow." in statement:
        statement = statement.replace("radiusflow.", "")
    return statement, parameters


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()