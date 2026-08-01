from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import settings


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_existing_database():
    """Idempotently upgrade the existing local database without losing games."""
    if "games" not in inspect(engine).get_table_names():
        return
    existing = {column["name"] for column in inspect(engine).get_columns("games")}
    additions = {
        "status": "VARCHAR(20) DEFAULT 'completed' NOT NULL",
        "current_fen": "TEXT",
        "moves_json": "TEXT DEFAULT '[]' NOT NULL",
        "white_clock_ms": "INTEGER",
        "black_clock_ms": "INTEGER",
        "engine_config_json": "TEXT",
        "creator_owner_id": "VARCHAR(64)",
        "error": "TEXT",
        "started_at": "DATETIME",
        "completed_at": "DATETIME",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE games ADD COLUMN {name} {definition}"))
