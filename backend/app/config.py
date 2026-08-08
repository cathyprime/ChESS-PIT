from dataclasses import dataclass
from pathlib import Path
import ipaddress
import os


ROOT = Path(__file__).resolve().parents[2]


def secret_setting(name: str, default: str = "") -> str:
    """Read a setting directly or from a Docker/Kubernetes-style secret file."""
    value = os.getenv(name)
    file_name = os.getenv(f"{name}_FILE")
    if value is not None and file_name:
        raise RuntimeError(f"Set only one of {name} or {name}_FILE")
    if file_name:
        try:
            return Path(file_name).read_text().rstrip("\r\n")
        except OSError as exc:
            raise RuntimeError(f"Could not read {name}_FILE") from exc
    return default if value is None else value


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("ENVIRONMENT", "development")
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'arena.db'}")
    storage_dir: Path = Path(os.getenv("STORAGE_DIR", ROOT / "data"))
    arena_password: str = os.getenv("ARENA_PASSWORD", "fightclub")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin-fightclub")
    arena_password_hash: str = secret_setting("ARENA_PASSWORD_HASH")
    admin_password_hash: str = secret_setting("ADMIN_PASSWORD_HASH")
    secret_key: str = os.getenv("SECRET_KEY", "local-development-secret-change-me")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:5173")
    stockfish_path: str = os.getenv("STOCKFISH_PATH", str(ROOT / "tools" / "stockfish"))
    fastchess_path: str = os.getenv("FASTCHESS_PATH", str(ROOT / "tools" / "fastchess"))
    runner_mode: str = os.getenv("RUNNER_MODE", "disabled")
    runner_wrapper: str = os.getenv("RUNNER_WRAPPER", str(ROOT / "scripts" / "sandbox-engine.py"))
    runner_socket: str = os.getenv("RUNNER_SOCKET", "/run/chesspit-runner/runner.sock")
    secure_cookies: bool = os.getenv("SECURE_COOKIES", "false").lower() == "true"
    trusted_proxies: tuple[str, ...] = tuple(
        value.strip() for value in os.getenv("TRUSTED_PROXIES", "127.0.0.1").split(",") if value.strip()
    )
    max_bots_per_owner: int = int(os.getenv("MAX_BOTS_PER_OWNER", "5"))
    max_bots_total: int = int(os.getenv("MAX_BOTS_TOTAL", "100"))
    max_bot_storage_bytes: int = int(os.getenv("MAX_BOT_STORAGE_BYTES", str(5 * 1024**3)))
    max_active_user_games: int = int(os.getenv("MAX_ACTIVE_USER_GAMES", "2"))

    def validate(self) -> None:
        if self.runner_mode not in {"disabled", "socket"}:
            raise RuntimeError("RUNNER_MODE must be 'disabled' or 'socket'")
        try:
            for proxy in self.trusted_proxies:
                ipaddress.ip_network(proxy, strict=False)
        except ValueError as exc:
            raise RuntimeError("TRUSTED_PROXIES must contain IP addresses or CIDR networks") from exc
        if self.environment == "production":
            if not self.arena_password_hash.startswith("$argon2id$") or not self.admin_password_hash.startswith("$argon2id$"):
                raise RuntimeError("Production requires ARENA_PASSWORD_HASH and ADMIN_PASSWORD_HASH")
            if self.secret_key == "local-development-secret-change-me" or len(self.secret_key) < 32:
                raise RuntimeError("Production requires a random SECRET_KEY of at least 32 characters")
            if not self.secure_cookies or not self.frontend_origin.startswith("https://"):
                raise RuntimeError("Production requires secure cookies and an HTTPS FRONTEND_ORIGIN")
            if self.runner_mode != "socket":
                raise RuntimeError("Production requires the socket sandbox runner")


settings = Settings()
settings.validate()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
(settings.storage_dir / "bots").mkdir(exist_ok=True)
(settings.storage_dir / "matches").mkdir(exist_ok=True)
(settings.storage_dir / "avatars").mkdir(exist_ok=True)
