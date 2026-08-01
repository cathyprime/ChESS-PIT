from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, Text, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def now():
    return datetime.now(timezone.utc)


class Bot(Base):
    __tablename__ = "bots"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    binary_path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    owner_id: Mapped[str] = mapped_column(String(64), index=True)
    recovery_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="validating", index=True)
    rating: Mapped[float] = mapped_column(Float, default=1500.0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    draws: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    qualification_total: Mapped[int] = mapped_column(Integer, default=0)
    qualification_done: Mapped[int] = mapped_column(Integer, default=0)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    engine_kind: Mapped[str] = mapped_column(String(20), default="uploaded", index=True)
    stockfish_skill: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Game(Base):
    __tablename__ = "games"
    id: Mapped[int] = mapped_column(primary_key=True)
    mode: Mapped[str] = mapped_column(String(20), index=True)
    white_bot_id: Mapped[int | None] = mapped_column(ForeignKey("bots.id"), nullable=True)
    black_bot_id: Mapped[int | None] = mapped_column(ForeignKey("bots.id"), nullable=True)
    white_name: Mapped[str] = mapped_column(String(80))
    black_name: Mapped[str] = mapped_column(String(80))
    result: Mapped[str] = mapped_column(String(10), default="*")
    termination: Mapped[str | None] = mapped_column(String(120), nullable=True)
    pgn: Mapped[str] = mapped_column(Text, default="")
    analysis_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    state_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="completed", index=True)
    current_fen: Mapped[str | None] = mapped_column(Text, nullable=True)
    moves_json: Mapped[str] = mapped_column(Text, default="[]")
    white_clock_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    black_clock_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engine_config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    creator_owner_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    time_control: Mapped[str] = mapped_column(String(30), default="10+0.1")
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RatingEvent(Base):
    __tablename__ = "rating_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey("bots.id"))
    value: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String(200), default="Admin adjustment")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ArenaSetting(Base):
    __tablename__ = "arena_settings"
    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(String(200))


class RatingRun(Base):
    __tablename__ = "rating_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    total_pairings: Mapped[int] = mapped_column(Integer, default=0)
    completed_pairings: Mapped[int] = mapped_column(Integer, default=0)
    total_games: Mapped[int] = mapped_column(Integer, default=0)
    completed_games: Mapped[int] = mapped_column(Integer, default=0)
    current_pairing: Mapped[str | None] = mapped_column(String(180), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
