from dataclasses import dataclass
from pathlib import Path
import os


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'arena.db'}")
    storage_dir: Path = Path(os.getenv("STORAGE_DIR", ROOT / "data"))
    arena_password: str = os.getenv("ARENA_PASSWORD", "fightclub")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin-fightclub")
    arena_password_hash: str = os.getenv("ARENA_PASSWORD_HASH", "")
    admin_password_hash: str = os.getenv("ADMIN_PASSWORD_HASH", "")
    secret_key: str = os.getenv("SECRET_KEY", "local-development-secret-change-me")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5173")
    stockfish_path: str = os.getenv("STOCKFISH_PATH", str(ROOT / "tools" / "stockfish"))
    fastchess_path: str = os.getenv("FASTCHESS_PATH", str(ROOT / "tools" / "fastchess"))
    runner_mode: str = os.getenv("RUNNER_MODE", "local")
    runner_wrapper: str = os.getenv("RUNNER_WRAPPER", str(ROOT / "scripts" / "sandbox-engine.sh"))
    secure_cookies: bool = os.getenv("SECURE_COOKIES", "false").lower() == "true"


settings = Settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
(settings.storage_dir / "bots").mkdir(exist_ok=True)
(settings.storage_dir / "matches").mkdir(exist_ok=True)
