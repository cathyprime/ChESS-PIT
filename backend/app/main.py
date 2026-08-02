from __future__ import annotations
import hashlib
import hmac
import asyncio
import io
import json
import os
import re
import shutil
import threading
import math
from pathlib import Path
import chess
import chess.engine
import chess.pgn
from fastapi import FastAPI, Depends, HTTPException, Request, Response, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .config import settings
from .db import Base, engine, SessionLocal, get_db, migrate_existing_database
from .models import Bot, Game, RatingEvent, ArenaSetting
from .security import (read_session, require_admin, sign_session, credential_matches, new_token,
                       token_hash, is_admin, check_attempt_limit, record_failed_attempt)
from .security import session_cookie_name
from .runner import (qualify_bot, recount, analyse_game, get_setting, engine_argv, engine_options,
                     ensure_stockfish_bots, start_missing_rating_run, current_rating_run,
                     rating_run_json, resume_rating_run, sandbox_ready, audit_uploaded_bots)
from .live import live_manager, game_snapshot, moves_for_game, board_from_moves, export_pgn, parse_json, utcnow
from .history import bot_history_page
from .validation import normalize_bot_description
from .avatars import (MAX_AVATAR_BYTES, STOCKFISH_VARIANTS, avatar_path_for, avatar_style_for_bot, avatar_url, avatar_url_for_bot,
                      remove_stored_avatar, stockfish_asset, store_avatar, validate_avatar)


Base.metadata.create_all(engine)
migrate_existing_database()
app = FastAPI(title="ChESSPIT", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def security_boundary(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if request.headers.get("origin") != settings.frontend_origin:
            return Response("Invalid request origin", status_code=403)
    length = request.headers.get("content-length")
    if length:
        try:
            if int(length) > 51 * 1024 * 1024:
                return Response("Request too large", status_code=413)
        except ValueError:
            return Response("Invalid content length", status_code=400)
    if request.method == "POST" and request.url.path == "/api/bots":
        try:
            read_session(request)
        except HTTPException:
            return Response("Arena login required", status_code=401)
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return response


@app.on_event("startup")
def resume_live_games():
    audit_uploaded_bots()
    ensure_stockfish_bots()
    resume_rating_run()
    live_manager.resume()


class Login(BaseModel): password: str = Field(min_length=1, max_length=1024)
class Rename(BaseModel):
    name: str | None = None
    description: str | None = None
class RatingChange(BaseModel):
    value: float
    reason: str = Field(default="Admin adjustment", min_length=1, max_length=200)
class SettingsUpdate(BaseModel): games_per_pair: int; time_control: str; k_factor: float
class Exhibition(BaseModel): white: str; black: str; time_control: str = "10+0.1"
class HumanStart(BaseModel):
    bot: str
    human_color: str = "white"
    move_time_ms: int = 500
    stockfish_skill: int = 10
class HumanMove(BaseModel): uci: str


def cookie(response: Response, value: str):
    response.set_cookie(session_cookie_name(), value, httponly=True, secure=settings.secure_cookies,
                        samesite="lax", max_age=60 * 60 * 24 * 30, path="/")


@app.get("/api/health")
def health():
    return {"ok": True, "stockfish": Path(settings.stockfish_path).exists(),
            "fastchess": Path(settings.fastchess_path).exists(),
            "sandbox": "ready" if sandbox_ready() else "unavailable"}


@app.post("/api/auth/login")
def login(body: Login, response: Response, request: Request):
    check_attempt_limit(request, "arena-login")
    if not credential_matches(body.password, settings.arena_password, settings.arena_password_hash):
        record_failed_attempt(request, "arena-login"); raise HTTPException(401, "Wrong password")
    old = read_session(request, required=False)
    owner = old.get("owner") or new_token()
    cookie(response, sign_session(owner, False))
    return {"authenticated": True, "admin": False}


@app.post("/api/auth/admin")
def admin_login(body: Login, response: Response, request: Request):
    check_attempt_limit(request, "admin-login")
    if not credential_matches(body.password, settings.admin_password, settings.admin_password_hash):
        record_failed_attempt(request, "admin-login"); raise HTTPException(401, "Wrong admin password")
    old = read_session(request, required=False)
    cookie(response, sign_session(old.get("owner") or new_token(), True))
    return {"authenticated": True, "admin": True}


@app.get("/api/auth/session")
def session(request: Request):
    value = read_session(request)
    return {"authenticated": True, "admin": is_admin(value)}


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(session_cookie_name(), path="/", secure=settings.secure_cookies,
                           httponly=True, samesite="lax"); return {"ok": True}


def bot_json(bot: Bot, owner: str | None = None):
    return {"id": bot.id, "name": bot.name, "description": bot.description or "", "status": bot.status, "rating": bot.rating,
            "wins": bot.wins, "draws": bot.draws, "losses": bot.losses,
            "qualificationDone": bot.qualification_done, "qualificationTotal": bot.qualification_total,
            "failureReason": bot.failure_reason, "owned": owner == bot.owner_id and bot.engine_kind == "uploaded",
            "system": bot.engine_kind == "stockfish", "engineKind": bot.engine_kind,
            "stockfishSkill": bot.stockfish_skill, "avatarUrl": avatar_url_for_bot(bot),
            "avatarStyle": avatar_style_for_bot(bot),
            "createdAt": bot.created_at}


def png_response(path: Path):
    return FileResponse(path, media_type="image/png",
                        headers={"Cache-Control": "private, max-age=0, must-revalidate"})


@app.get("/api/avatars/stockfish/{variant}")
def stockfish_avatar(variant: str, request: Request, theme: str = "inferno"):
    read_session(request)
    if variant not in STOCKFISH_VARIANTS: raise HTTPException(404, "Avatar not found")
    return png_response(stockfish_asset(variant, theme))


@app.get("/api/bots/{bot_id}/avatar")
def bot_avatar(bot_id: int, request: Request, theme: str = "inferno", db: Session = Depends(get_db)):
    read_session(request)
    bot = db.get(Bot, bot_id)
    if not bot: raise HTTPException(404, "Bot not found")
    return png_response(avatar_path_for(bot, theme))


@app.get("/api/bots")
def bots(request: Request, db: Session = Depends(get_db)):
    user = read_session(request)
    rows = list(db.scalars(select(Bot).where(Bot.status != "retired").order_by(Bot.rating.desc(), Bot.name)))
    return [bot_json(x, user["owner"]) for x in rows]


@app.get("/api/bots/{bot_id}/games")
def bot_games(bot_id: int, request: Request, offset: int = 0, limit: int = 50,
              db: Session = Depends(get_db)):
    user = read_session(request)
    if offset < 0: raise HTTPException(400, "Offset cannot be negative")
    if limit < 1 or limit > 100: raise HTTPException(400, "Limit must be from 1 to 100")
    bot = db.get(Bot, bot_id)
    if not bot: raise HTTPException(404, "Bot not found")
    page = bot_history_page(db, bot, offset, limit)
    return {"bot": bot_json(bot, user["owner"]), **page}


@app.post("/api/bots")
async def upload_bot(request: Request, name: str = Form(...), description: str = Form(...), binary: UploadFile = File(...),
                     avatar: UploadFile = File(...), db: Session = Depends(get_db)):
    user = read_session(request)
    check_attempt_limit(request, "bot-upload", limit=10, window=3600)
    record_failed_attempt(request, "bot-upload")
    if not sandbox_ready(): raise HTTPException(503, "Uploaded-engine sandbox is unavailable")
    name = name.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,39}", name): raise HTTPException(400, "Invalid bot name")
    try:
        description = normalize_bot_description(description)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    if db.scalar(select(Bot).where(func.lower(Bot.name) == name.lower())): raise HTTPException(409, "Bot name already exists")
    owner_count = int(db.scalar(select(func.count(Bot.id)).where(
        Bot.owner_id == user["owner"], Bot.engine_kind == "uploaded", Bot.status != "retired")) or 0)
    total_count = int(db.scalar(select(func.count(Bot.id)).where(
        Bot.engine_kind == "uploaded", Bot.status != "retired")) or 0)
    total_bytes = int(db.scalar(select(func.coalesce(func.sum(Bot.binary_size), 0)).where(
        Bot.engine_kind == "uploaded", Bot.status != "retired")) or 0)
    if owner_count >= settings.max_bots_per_owner: raise HTTPException(429, "Bot quota reached")
    if total_count >= settings.max_bots_total: raise HTTPException(503, "Arena bot capacity reached")
    data = await binary.read(50 * 1024 * 1024 + 1)
    if len(data) > 50 * 1024 * 1024: raise HTTPException(413, "Binary exceeds 50 MB")
    if total_bytes + len(data) > settings.max_bot_storage_bytes: raise HTTPException(503, "Arena storage capacity reached")
    if len(data) < 20 or data[:4] != b"\x7fELF" or data[4] != 2 or int.from_bytes(data[18:20], "little") != 62:
        raise HTTPException(400, "Upload must be a 64-bit x86-64 ELF executable")
    try:
        avatar_data, avatar_digest = validate_avatar(await avatar.read(MAX_AVATAR_BYTES + 1))
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    recovery = new_token()
    digest = hashlib.sha256(data).hexdigest()
    target = settings.storage_dir / "bots" / new_token()
    target.write_bytes(data); target.chmod(0o540)
    avatar_target = store_avatar(avatar_data)
    bot = Bot(name=name, description=description, binary_path=str(target), sha256=digest,
              binary_size=len(data), owner_id=user["owner"],
              recovery_hash=token_hash(recovery), avatar_path=str(avatar_target),
              avatar_sha256=avatar_digest, avatar_style="mask")
    try:
        db.add(bot); db.commit(); db.refresh(bot)
    except Exception:
        target.unlink(missing_ok=True); remove_stored_avatar(str(avatar_target)); raise
    threading.Thread(target=qualify_bot, args=(bot.id,), daemon=True).start()
    return {"bot": bot_json(bot, user["owner"]), "recoveryToken": recovery}


def owned(bot: Bot, user: dict):
    if bot.engine_kind == "stockfish": raise HTTPException(403, "System competitors are locked")
    if bot.owner_id != user.get("owner") and not is_admin(user): raise HTTPException(403, "You do not own this bot")


def remove_bot_binary(bot: Bot) -> None:
    root = (settings.storage_dir / "bots").resolve()
    candidate = Path(bot.binary_path)
    try:
        if candidate.parent.resolve() == root and candidate.name == candidate.resolve().name:
            candidate.unlink(missing_ok=True)
    except OSError:
        pass


@app.put("/api/bots/{bot_id}/avatar")
async def replace_bot_avatar(bot_id: int, request: Request, avatar: UploadFile = File(...),
                             db: Session = Depends(get_db)):
    user, bot = read_session(request), db.get(Bot, bot_id)
    if not bot: raise HTTPException(404, "Bot not found")
    owned(bot, user)
    try:
        data, digest = validate_avatar(await avatar.read(MAX_AVATAR_BYTES + 1))
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    old_path = bot.avatar_path
    target = store_avatar(data)
    bot.avatar_path, bot.avatar_sha256, bot.avatar_style = str(target), digest, "mask"
    try:
        db.commit()
    except Exception:
        remove_stored_avatar(str(target)); raise
    remove_stored_avatar(old_path)
    return bot_json(bot, user["owner"])


@app.patch("/api/bots/{bot_id}")
def rename_bot(bot_id: int, body: Rename, request: Request, db: Session = Depends(get_db)):
    user, bot = read_session(request), db.get(Bot, bot_id)
    if not bot: raise HTTPException(404, "Bot not found")
    owned(bot, user)
    if body.name is None and body.description is None:
        raise HTTPException(400, "Provide a name or description to update")
    if body.name is not None:
        name = body.name.strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,39}", name): raise HTTPException(400, "Invalid bot name")
        duplicate = db.scalar(select(Bot).where(func.lower(Bot.name) == name.lower(), Bot.id != bot.id))
        if duplicate: raise HTTPException(409, "Bot name already exists")
        bot.name = name
    if body.description is not None:
        try:
            bot.description = normalize_bot_description(body.description)
        except ValueError as exc:
            raise HTTPException(400, str(exc))
    db.commit(); return bot_json(bot, user["owner"])


@app.delete("/api/bots/{bot_id}")
def retire_bot(bot_id: int, request: Request, db: Session = Depends(get_db)):
    user, bot = read_session(request), db.get(Bot, bot_id)
    if not bot: raise HTTPException(404, "Bot not found")
    owned(bot, user)
    for game in db.scalars(select(Game).where(
            Game.status.in_(("queued", "running")),
            (Game.white_bot_id == bot.id) | (Game.black_bot_id == bot.id))):
        game.status, game.termination, game.completed_at = "aborted", "bot retired", utcnow()
    bot.status = "retired"; remove_bot_binary(bot); bot.binary_size = 0
    db.commit(); recount(db); return {"ok": True}


@app.post("/api/bots/{bot_id}/claim")
def claim_bot(bot_id: int, body: Login, request: Request, db: Session = Depends(get_db)):
    check_attempt_limit(request, "bot-claim")
    user, bot = read_session(request), db.get(Bot, bot_id)
    if not bot or not hmac.compare_digest(token_hash(body.password), bot.recovery_hash):
        record_failed_attempt(request, "bot-claim"); raise HTTPException(404, "Invalid recovery token")
    bot.owner_id = user["owner"]; db.commit(); return {"ok": True}


def game_json(g: Game, db: Session, detail=False):
    white_bot = db.get(Bot, g.white_bot_id) if g.white_bot_id else None
    black_bot = db.get(Bot, g.black_bot_id) if g.black_bot_id else None
    value = {"id": g.id, "mode": g.mode, "whiteName": g.white_name, "blackName": g.black_name,
             "whiteBotId": g.white_bot_id, "blackBotId": g.black_bot_id,
             "whiteAvatarUrl": avatar_url(g.white_bot_id, g.white_name),
             "blackAvatarUrl": avatar_url(g.black_bot_id, g.black_name),
             "whiteAvatarStyle": avatar_style_for_bot(white_bot, g.white_name),
             "blackAvatarStyle": avatar_style_for_bot(black_bot, g.black_name),
             "result": g.result, "termination": g.termination, "timeControl": g.time_control,
             "status": g.status, "analysed": bool(g.analysis_json), "createdAt": g.created_at}
    if detail:
        value.update(game_snapshot(g, db=db))
        value["pgn"] = g.pgn
    return value


@app.get("/api/games")
def games(request: Request, db: Session = Depends(get_db)):
    read_session(request)
    return [game_json(g, db) for g in db.scalars(select(Game).where(Game.deleted == False).order_by(Game.id.desc()).limit(200))]


@app.get("/api/games/{game_id}")
def game(game_id: int, request: Request, db: Session = Depends(get_db)):
    user = read_session(request); row = db.get(Game, game_id)
    if not row or row.deleted: raise HTTPException(404, "Game not found")
    value = game_snapshot(row, user.get("owner"), is_admin(user), db)
    value["pgn"] = row.pgn
    return value


@app.post("/api/games/{game_id}/analyse")
def analyse(game_id: int, request: Request):
    read_session(request)
    return {"queued": False, "detail": "Open the game page to run viewer-scoped analysis"}


def resolve_engine(value: str, db: Session):
    if value == "stockfish":
        return {"kind": "stockfish", "name": "Stockfish", "botId": None,
                "stockfish": True}
    try:
        bot_id = int(value)
    except (TypeError, ValueError):
        raise HTTPException(400, "Invalid engine")
    bot = db.get(Bot, bot_id)
    if not bot or bot.status != "active": raise HTTPException(400, "Bot is not active")
    if bot.engine_kind == "stockfish":
        return {"kind": "stockfish", "name": bot.name, "botId": bot.id,
                "stockfish": True, "stockfishSkill": bot.stockfish_skill}
    if not sandbox_ready(): raise HTTPException(503, "Uploaded-engine sandbox is unavailable")
    return {"kind": "uploaded", "name": bot.name, "botId": bot.id, "stockfish": False}


def parsed_time_control(value: str) -> tuple[float, float]:
    if not re.fullmatch(r"\d+(?:\.\d+)?\+\d+(?:\.\d+)?", value):
        raise HTTPException(400, "Invalid time control")
    base, increment = (float(part) for part in value.split("+", 1))
    if not (math.isfinite(base) and math.isfinite(increment) and .1 <= base <= 300 and 0 <= increment <= 60):
        raise HTTPException(400, "Time control is outside allowed limits")
    return base, increment


def enforce_game_capacity(db: Session):
    active = int(db.scalar(select(func.count(Game.id)).where(
        Game.mode.in_(("exhibition", "human")), Game.status.in_(("queued", "running")))) or 0)
    if active >= settings.max_active_user_games:
        raise HTTPException(429, "Active game capacity reached")


@app.post("/api/exhibitions")
def exhibition(body: Exhibition, request: Request, response: Response, db: Session = Depends(get_db)):
    user = read_session(request)
    enforce_game_capacity(db)
    base, _ = parsed_time_control(body.time_control)
    white, black = resolve_engine(body.white, db), resolve_engine(body.black, db)
    row = Game(mode="exhibition", white_bot_id=white["botId"], black_bot_id=black["botId"],
               white_name=white["name"], black_name=black["name"], result="*", status="queued",
               current_fen=chess.STARTING_FEN, moves_json="[]", time_control=body.time_control,
               white_clock_ms=int(base * 1000), black_clock_ms=int(base * 1000),
               engine_config_json=json.dumps({"white": white, "black": black}),
               creator_owner_id=user["owner"])
    db.add(row); db.commit(); db.refresh(row)
    live_manager.start_showdown(row.id)
    response.status_code = 202
    return game_snapshot(row, user["owner"], is_admin(user), db)


@app.post("/api/human-games")
def human_start(body: HumanStart, request: Request, db: Session = Depends(get_db)):
    user = read_session(request)
    enforce_game_capacity(db)
    if body.human_color not in ("white", "black", "random"):
        raise HTTPException(400, "Invalid color")
    if body.move_time_ms not in (100, 500, 1000, 3000):
        raise HTTPException(400, "Invalid thinking time")
    if not 0 <= body.stockfish_skill <= 20:
        raise HTTPException(400, "Stockfish skill must be from 0 to 20")
    opponent = resolve_engine(body.bot, db)
    import secrets
    color = ("white" if secrets.randbelow(2) == 0 else "black") if body.human_color == "random" else body.human_color
    human_white = color == "white"
    row = Game(mode="human", white_bot_id=None if human_white else opponent["botId"],
               black_bot_id=opponent["botId"] if human_white else None,
               white_name="Human" if human_white else opponent["name"],
               black_name=opponent["name"] if human_white else "Human", pgn="", result="*",
               status="running", current_fen=chess.STARTING_FEN, moves_json="[]",
               time_control=f"movetime {body.move_time_ms}", creator_owner_id=user["owner"], started_at=utcnow(),
               engine_config_json=json.dumps({"opponent": opponent, "humanColor": color,
                                              "moveTimeMs": body.move_time_ms,
                                              "stockfishSkill": body.stockfish_skill}))
    db.add(row); db.commit(); db.refresh(row)
    if not human_white: live_manager.start_human_engine_turn(row.id)
    return game_snapshot(row, user["owner"], is_admin(user), db)


@app.post("/api/human-games/{game_id}/move")
def human_move(game_id: int, body: HumanMove, request: Request, db: Session = Depends(get_db)):
    user = read_session(request); row = db.get(Game, game_id)
    if not row or row.mode != "human" or row.status != "running": raise HTTPException(400, "Game is not active")
    config = parse_json(row.engine_config_json, {})
    if row.creator_owner_id != user.get("owner") and not is_admin(user):
        raise HTTPException(403, "Only the player can move")
    moves = moves_for_game(row); board = board_from_moves(moves)
    try: move = board.parse_uci(body.uci)
    except ValueError: raise HTTPException(400, "Illegal move")
    human_turn = (board.turn and config["humanColor"] == "white") or (not board.turn and config["humanColor"] == "black")
    if not human_turn: raise HTTPException(400, "It is not the human turn")
    san = board.san(move); board.push(move)
    moves.append({"uci": move.uci(), "san": san, "fen": board.fen(), "elapsedMs": None})
    row.moves_json, row.current_fen = json.dumps(moves), board.fen()
    if board.is_game_over(claim_draw=True):
        row.result, row.status, row.completed_at = board.result(claim_draw=True), "completed", utcnow()
        row.termination = board.outcome(claim_draw=True).termination.name.lower().replace("_", " ")
    row.pgn = export_pgn(row, moves, board); db.commit()
    if row.status == "running": live_manager.start_human_engine_turn(row.id)
    live_manager.ensure_analysis(row.id)
    return game_snapshot(row, user["owner"], is_admin(user), db)


@app.post("/api/human-games/{game_id}/resign")
def resign_human(game_id: int, request: Request, db: Session = Depends(get_db)):
    user = read_session(request); row = db.get(Game, game_id)
    if not row or row.mode != "human" or row.status != "running": raise HTTPException(400, "Game is not active")
    if row.creator_owner_id != user.get("owner") and not is_admin(user): raise HTTPException(403, "Only the player can resign")
    config = parse_json(row.engine_config_json, {})
    row.result = "0-1" if config.get("humanColor") == "white" else "1-0"
    row.status, row.termination, row.completed_at = "completed", "resignation", utcnow()
    db.commit(); return game_snapshot(row, user["owner"], is_admin(user), db)


@app.post("/api/games/{game_id}/abort")
def abort_game(game_id: int, request: Request, db: Session = Depends(get_db)):
    user = read_session(request); row = db.get(Game, game_id)
    if not row: raise HTTPException(404, "Game not found")
    if row.creator_owner_id != user.get("owner") and not is_admin(user): raise HTTPException(403, "Not allowed")
    if row.status not in ("queued", "running"): raise HTTPException(400, "Game has already finished")
    row.status, row.termination, row.completed_at = "aborted", "aborted", utcnow()
    db.commit(); return game_snapshot(row, user["owner"], is_admin(user), db)


@app.websocket("/api/games/{game_id}/stream")
async def game_stream(websocket: WebSocket, game_id: int):
    if websocket.headers.get("origin") != settings.frontend_origin:
        await websocket.close(code=4403); return
    try:
        user = read_session(websocket)
    except HTTPException:
        await websocket.close(code=4401); return
    with SessionLocal() as db:
        if not db.get(Game, game_id):
            await websocket.close(code=4404); return
    owner_id = str(user.get("owner", ""))
    if not live_manager.viewer_joined(game_id, owner_id):
        await websocket.close(code=4429); return
    await websocket.accept()
    last = None
    try:
        while True:
            with SessionLocal() as db:
                row = db.get(Game, game_id)
                payload = game_snapshot(row, user.get("owner"), is_admin(user), db)
            encoded = json.dumps(payload, sort_keys=True)
            if encoded != last:
                await websocket.send_json({"type": "snapshot", "game": payload})
                last = encoded
            try:
                message = await asyncio.wait_for(websocket.receive_json(), timeout=.25)
                if message.get("type") == "focus_ply":
                    requested = int(message.get("ply", 0))
                    with SessionLocal() as db:
                        maximum = len(moves_for_game(db.get(Game, game_id)))
                    live_manager.set_focus(game_id, min(maximum, max(0, requested)))
            except asyncio.TimeoutError:
                live_manager.ensure_analysis(game_id)
    except WebSocketDisconnect:
        pass
    finally:
        live_manager.viewer_left(game_id, owner_id)


@app.get("/api/admin/settings")
def admin_settings(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    return {"gamesPerPair": int(get_setting(db, "games_per_pair", "2")), "timeControl": get_setting(db, "time_control", "10+0.1"), "kFactor": float(get_setting(db, "k_factor", "32"))}


@app.put("/api/admin/settings")
def update_settings(body: SettingsUpdate, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    if body.games_per_pair < 2 or body.games_per_pair > 100 or body.games_per_pair % 2: raise HTTPException(400, "Games must be even, from 2 to 100")
    parsed_time_control(body.time_control)
    if not math.isfinite(body.k_factor) or body.k_factor < 1 or body.k_factor > 128:
        raise HTTPException(400, "K-factor must be from 1 to 128")
    for key, value in (("games_per_pair", body.games_per_pair), ("time_control", body.time_control), ("k_factor", body.k_factor)):
        row = db.get(ArenaSetting, key)
        if row: row.value = str(value)
        else: db.add(ArenaSetting(key=key, value=str(value)))
    db.commit(); return {"ok": True}


@app.post("/api/admin/bots/{bot_id}/rating")
def set_rating(bot_id: int, body: RatingChange, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    if not math.isfinite(body.value) or body.value < 0 or body.value > 10000:
        raise HTTPException(400, "Rating must be finite and from 0 to 10000")
    if not db.get(Bot, bot_id): raise HTTPException(404, "Bot not found")
    db.add(RatingEvent(bot_id=bot_id, value=body.value, reason=body.reason)); db.commit(); recount(db); return {"ok": True}


@app.post("/api/admin/recount")
def force_recount(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    return {"ok": True, **recount(db)}


@app.post("/api/admin/rating-runs/missing", status_code=202)
def run_missing_ratings(request: Request):
    require_admin(request)
    return rating_run_json(start_missing_rating_run())


@app.get("/api/admin/rating-runs/current")
def rating_run_status(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    return rating_run_json(current_rating_run(db))


@app.delete("/api/admin/games/{game_id}")
def delete_game(game_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request); row = db.get(Game, game_id)
    if not row: raise HTTPException(404, "Game not found")
    row.deleted = True; db.commit(); recount(db); return {"ok": True}


@app.delete("/api/admin/bots/{bot_id}")
def purge_bot(bot_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request); bot = db.get(Bot, bot_id)
    if not bot: raise HTTPException(404, "Bot not found")
    if bot.engine_kind == "stockfish": raise HTTPException(403, "System competitors cannot be deleted")
    bot.status = "retired"; remove_bot_binary(bot); bot.binary_size = 0; remove_stored_avatar(bot.avatar_path)
    bot.avatar_path = None; db.commit(); recount(db); return {"ok": True}
