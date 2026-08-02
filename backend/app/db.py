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
    game_existing = {column["name"] for column in inspect(engine).get_columns("games")} if "games" in tables else set()
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
    sample_descriptions = {
        "Stockfish Level 1": "Stockfish benchmark at Skill Level 1: a restrained tactical baseline.",
        "Stockfish Level 2": "Low-strength Stockfish benchmark for early ladder testing.",
        "Stockfish Level 3": "Developing Stockfish benchmark with basic tactical pressure.",
        "Stockfish Level 5": "Mid-low Stockfish benchmark balancing tactics and safety.",
        "Stockfish Level 8": "Intermediate Stockfish benchmark with sharper calculation.",
        "Stockfish Level 13": "Strong Stockfish benchmark with consistent tactical depth.",
        "Stockfish Level 20": "High-strength Stockfish benchmark with relentless calculation.",
        "Stockfish Skill 1": "Stockfish benchmark at Skill Level 1: a restrained tactical baseline.",
        "Stockfish Skill 2": "Low-strength Stockfish benchmark for early ladder testing.",
        "Stockfish Skill 3": "Developing Stockfish benchmark with basic tactical pressure.",
        "Stockfish Skill 5": "Mid-low Stockfish benchmark balancing tactics and safety.",
        "Stockfish Skill 8": "Intermediate Stockfish benchmark with sharper calculation.",
        "Stockfish Skill 13": "Strong Stockfish benchmark with consistent tactical depth.",
        "Stockfish Skill 20": "High-strength Stockfish benchmark with relentless calculation.",
        "Stockfish Alpha": "Experimental Stockfish entry for arena testing.",
        "Random One": "Random-move baseline for measuring the floor of the ladder.",
        "Random Two": "Random-move baseline for measuring the floor of the ladder.",
        "Random Three": "Random-move baseline for measuring the floor of the ladder.",
    }
    with engine.begin() as connection:
        if "games" in tables:
            for name, definition in game_additions.items():
                if name not in game_existing:
                    connection.execute(text(f"ALTER TABLE games ADD COLUMN {name} {definition}"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_games_white_bot_id ON games (white_bot_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_games_black_bot_id ON games (black_bot_id)"))
        if "bots" in tables:
            bot_existing = {column["name"] for column in inspect(engine).get_columns("bots")}
            bot_additions = {
                "description": "TEXT DEFAULT '' NOT NULL",
                "engine_kind": "VARCHAR(20) DEFAULT 'uploaded' NOT NULL",
                "stockfish_skill": "INTEGER",
                "avatar_path": "TEXT",
                "avatar_sha256": "VARCHAR(64)",
                "avatar_style": "VARCHAR(20) DEFAULT 'legacy' NOT NULL",
                "binary_size": "INTEGER DEFAULT 0 NOT NULL",
            }
            for name, definition in bot_additions.items():
                if name not in bot_existing:
                    connection.execute(text(f"ALTER TABLE bots ADD COLUMN {name} {definition}"))
            for name, description in sample_descriptions.items():
                connection.execute(
                    text("UPDATE bots SET description = :description "
                         "WHERE lower(name) = lower(:name) "
                         "AND (description IS NULL OR trim(description) = '')"),
                    {"name": name, "description": description},
                )
