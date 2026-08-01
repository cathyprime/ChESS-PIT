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
    tables = inspect(engine).get_table_names()
    if "games" not in tables:
        return
    game_existing = {column["name"] for column in inspect(engine).get_columns("games")}
    game_additions = {
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
        for name, definition in game_additions.items():
            if name not in game_existing:
                connection.execute(text(f"ALTER TABLE games ADD COLUMN {name} {definition}"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_games_white_bot_id ON games (white_bot_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_games_black_bot_id ON games (black_bot_id)"))
        if "bots" in tables:
            bot_existing = {column["name"] for column in inspect(engine).get_columns("bots")}
            bot_additions = {
                "engine_kind": "VARCHAR(20) DEFAULT 'uploaded' NOT NULL",
                "stockfish_skill": "INTEGER",
            }
            for name, definition in bot_additions.items():
                if name not in bot_existing:
                    connection.execute(text(f"ALTER TABLE bots ADD COLUMN {name} {definition}"))
