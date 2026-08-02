from __future__ import annotations

import hashlib
import io
import secrets
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .config import settings
from .models import Bot


MAX_AVATAR_BYTES = 256 * 1024
AVATAR_SIZE = (128, 128)
MIN_TRANSPARENT_PIXELS = int(AVATAR_SIZE[0] * AVATAR_SIZE[1] * .10)
ASSET_DIR = Path(__file__).with_name("assets") / "avatars"
STOCKFISH_VARIANTS = {"1", "2", "3", "5", "8", "13", "20", "full"}
AVATAR_THEMES = {"inferno", "emo", "gangsta", "catppuccin", "angelic", "jamaica"}


def validate_avatar(data: bytes) -> tuple[bytes, str]:
    if not data:
        raise ValueError("Avatar PNG is required")
    if len(data) > MAX_AVATAR_BYTES:
        raise ValueError("Avatar exceeds 256 KB")
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format != "PNG":
                raise ValueError("Avatar must be a PNG image")
            if image.size != AVATAR_SIZE:
                raise ValueError("Avatar must be exactly 128×128 pixels")
            if getattr(image, "is_animated", False):
                raise ValueError("Animated PNG avatars are not supported")
            image.load()
            canonical = image.convert("RGBA")
            transparent = sum(alpha == 0 for alpha in canonical.getchannel("A").getdata())
            if transparent < MIN_TRANSPARENT_PIXELS:
                raise ValueError("Mask must have a transparent background (at least 10% fully transparent pixels)")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Avatar is not a valid PNG image") from exc
    output = io.BytesIO()
    canonical.save(output, format="PNG", optimize=True)
    encoded = output.getvalue()
    return encoded, hashlib.sha256(encoded).hexdigest()


def store_avatar(data: bytes) -> Path:
    target = settings.storage_dir / "avatars" / f"{secrets.token_urlsafe(24)}.png"
    target.write_bytes(data)
    target.chmod(0o600)
    return target


def remove_stored_avatar(path: str | None):
    if not path:
        return
    candidate = Path(path)
    try:
        if candidate.resolve().parent == (settings.storage_dir / "avatars").resolve():
            candidate.unlink(missing_ok=True)
    except OSError:
        pass


def stockfish_asset(variant: str | int | None, theme: str = "inferno") -> Path:
    value = str(variant if variant is not None else "full")
    if value not in STOCKFISH_VARIANTS:
        value = "full"
    safe_theme = theme if theme in AVATAR_THEMES else "inferno"
    themed = ASSET_DIR / safe_theme / f"stockfish-{value}.png"
    return themed if themed.is_file() else ASSET_DIR / f"stockfish-{value}.png"


def avatar_path_for(bot: Bot, theme: str = "inferno") -> Path:
    if bot.avatar_path and Path(bot.avatar_path).is_file():
        return Path(bot.avatar_path)
    if bot.engine_kind == "stockfish":
        return stockfish_asset(bot.stockfish_skill, theme)
    return ASSET_DIR / "default-bot.png"


def avatar_url(bot_id: int | None, name: str | None = None) -> str | None:
    if bot_id is not None:
        return f"/api/bots/{bot_id}/avatar"
    if name == "Stockfish":
        return "/api/avatars/stockfish/full"
    return None


def avatar_url_for_bot(bot: Bot) -> str:
    version = bot.avatar_sha256[:12] if bot.avatar_sha256 else (
        f"stockfish-{bot.stockfish_skill}" if bot.engine_kind == "stockfish" else "default")
    return f"/api/bots/{bot.id}/avatar?v={version}"


def avatar_style_for_bot(bot: Bot | None, name: str | None = None) -> str | None:
    if bot:
        return "mask" if bot.engine_kind == "stockfish" else (bot.avatar_style or "legacy")
    return "mask" if name == "Stockfish" else None
