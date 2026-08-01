from __future__ import annotations
import hashlib
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
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .config import settings
from .db import Base, engine, SessionLocal, get_db, migrate_existing_database
from .models import Bot, Game, RatingEvent, ArenaSetting
from .security import read_session, require_admin, sign_session, credential_matches, new_token, token_hash
from .runner import (qualify_bot, recount, analyse_game, get_setting, engine_argv, engine_options,
                     ensure_stockfish_bots, start_missing_rating_run, current_rating_run,
                     rating_run_json, resume_rating_run)
from .live import live_manager, game_snapshot, moves_for_game, board_from_moves, export_pgn, parse_json, utcnow
from .history import bot_history_page


Base.metadata.create_all(engine)
migrate_existing_database()
app = FastAPI(title="Chess Bot Fight Club", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def resume_live_games():
    ensure_stockfish_bots()
    resume_rating_run()
    live_manager.resume()


class Login(BaseModel): password: str
class Rename(BaseModel): name: str
class RatingChange(BaseModel): value: float; reason: str = "Admin adjustment"
class SettingsUpdate(BaseModel): games_per_pair: int; time_control: str; k_factor: float
class Exhibition(BaseModel): white: str; black: str; time_control: str = "10+0.1"
class HumanStart(BaseModel):
    bot: str
    human_color: str = "white"
    move_time_ms: int = 500
    stockfish_skill: int = 10
class HumanMove(BaseModel): uci: str


def cookie(response: Response, value: str):
    response.set_cookie("cbfc_session", value, httponly=True, secure=settings.secure_cookies,
                        samesite="lax", max_age=60 * 60 * 24 * 30)


@app.get("/api/health")
def health():
    return {"ok": True, "stockfish": Path(settings.stockfish_path).exists(),
            "fastchess": Path(settings.fastchess_path).exists(), "runner": settings.runner_mode}


@app.post("/api/auth/login")
def login(body: Login, response: Response, request: Request):
    if not credential_matches(body.password, settings.arena_password, settings.arena_password_hash): raise HTTPException(401, "Wrong password")
    old = read_session(request, required=False)
    owner = old.get("owner") or new_token()
    cookie(response, sign_session(owner, False))
    return {"authenticated": True, "admin": False}


@app.post("/api/auth/admin")
def admin_login(body: Login, response: Response, request: Request):
    if not credential_matches(body.password, settings.admin_password, settings.admin_password_hash): raise HTTPException(401, "Wrong admin password")
    old = read_session(request, required=False)
    cookie(response, sign_session(old.get("owner") or new_token(), True))
    return {"authenticated": True, "admin": True}


@app.get("/api/auth/session")
def session(request: Request):
    value = read_session(request)
    return {"authenticated": True, "admin": bool(value.get("admin"))}


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("cbfc_session"); return {"ok": True}


def bot_json(bot: Bot, owner: str | None = None):
    return {"id": bot.id, "name": bot.name, "status": bot.status, "rating": bot.rating,
            "wins": bot.wins, "draws": bot.draws, "losses": bot.losses,
            "qualificationDone": bot.qualification_done, "qualificationTotal": bot.qualification_total,
            "failureReason": bot.failure_reason, "owned": owner == bot.owner_id and bot.engine_kind == "uploaded",
            "system": bot.engine_kind == "stockfish", "engineKind": bot.engine_kind,
            "stockfishSkill": bot.stockfish_skill, "createdAt": bot.created_at}


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
async def upload_bot(request: Request, name: str = Form(...), binary: UploadFile = File(...), db: Session = Depends(get_db)):
    user = read_session(request)
    name = name.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,39}", name): raise HTTPException(400, "Invalid bot name")
    if db.scalar(select(Bot).where(func.lower(Bot.name) == name.lower())): raise HTTPException(409, "Bot name already exists")
    data = await binary.read(50 * 1024 * 1024 + 1)
    if len(data) > 50 * 1024 * 1024: raise HTTPException(413, "Binary exceeds 50 MB")
    if len(data) < 20 or data[:4] != b"\x7fELF" or data[4] != 2 or int.from_bytes(data[18:20], "little") != 62:
        raise HTTPException(400, "Upload must be a 64-bit x86-64 ELF executable")
    recovery = new_token()
    digest = hashlib.sha256(data).hexdigest()
    target = settings.storage_dir / "bots" / new_token()
    target.write_bytes(data); target.chmod(0o500)
    bot = Bot(name=name, binary_path=str(target), sha256=digest, owner_id=user["owner"], recovery_hash=token_hash(recovery))
    db.add(bot); db.commit(); db.refresh(bot)
    threading.Thread(target=qualify_bot, args=(bot.id,), daemon=True).start()
    return {"bot": bot_json(bot, user["owner"]), "recoveryToken": recovery}


def owned(bot: Bot, user: dict):
    if bot.engine_kind == "stockfish": raise HTTPException(403, "System competitors are locked")
    if bot.owner_id != user.get("owner") and not user.get("admin"): raise HTTPException(403, "You do not own this bot")


@app.patch("/api/bots/{bot_id}")
def rename_bot(bot_id: int, body: Rename, request: Request, db: Session = Depends(get_db)):
    user, bot = read_session(request), db.get(Bot, bot_id)
    if not bot: raise HTTPException(404, "Bot not found")
    owned(bot, user); name = body.name.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _.-]{0,39}", name): raise HTTPException(400, "Invalid bot name")
    duplicate = db.scalar(select(Bot).where(func.lower(Bot.name) == name.lower(), Bot.id != bot.id))
    if duplicate: raise HTTPException(409, "Bot name already exists")
    bot.name = name; db.commit(); return bot_json(bot, user["owner"])


@app.delete("/api/bots/{bot_id}")
def retire_bot(bot_id: int, request: Request, db: Session = Depends(get_db)):
    user, bot = read_session(request), db.get(Bot, bot_id)
    if not bot: raise HTTPException(404, "Bot not found")
    owned(bot, user); bot.status = "retired"; db.commit(); recount(db); return {"ok": True}


@app.post("/api/bots/{bot_id}/claim")
def claim_bot(bot_id: int, body: Login, request: Request, db: Session = Depends(get_db)):
    user, bot = read_session(request), db.get(Bot, bot_id)
    if not bot or token_hash(body.password) != bot.recovery_hash: raise HTTPException(404, "Invalid recovery token")
    bot.owner_id = user["owner"]; db.commit(); return {"ok": True}


def game_json(g: Game, detail=False):
    value = {"id": g.id, "mode": g.mode, "whiteName": g.white_name, "blackName": g.black_name,
             "result": g.result, "termination": g.termination, "timeControl": g.time_control,
             "status": g.status, "analysed": bool(g.analysis_json), "createdAt": g.created_at}
    if detail:
        value.update(game_snapshot(g))
        value["pgn"] = g.pgn
    return value


@app.get("/api/games")
def games(request: Request, db: Session = Depends(get_db)):
    read_session(request)
    return [game_json(g) for g in db.scalars(select(Game).where(Game.deleted == False).order_by(Game.id.desc()).limit(200))]


@app.get("/api/games/{game_id}")
def game(game_id: int, request: Request, db: Session = Depends(get_db)):
    user = read_session(request); row = db.get(Game, game_id)
    if not row or row.deleted: raise HTTPException(404, "Game not found")
    value = game_snapshot(row, user.get("owner"), bool(user.get("admin")))
    value["pgn"] = row.pgn
    return value


@app.post("/api/games/{game_id}/analyse")
def analyse(game_id: int, request: Request):
    read_session(request)
    return {"queued": False, "detail": "Open the game page to run viewer-scoped analysis"}


def resolve_engine(value: str, db: Session):
    if value == "stockfish":
        return {"path": settings.stockfish_path, "name": "Stockfish", "botId": None,
                "trusted": True, "stockfish": True}
    bot = db.get(Bot, int(value))
    if not bot or bot.status != "active": raise HTTPException(400, "Bot is not active")
    if bot.engine_kind == "stockfish":
        return {"path": settings.stockfish_path, "name": bot.name, "botId": bot.id,
                "trusted": True, "stockfish": True, "stockfishSkill": bot.stockfish_skill}
    return {"path": bot.binary_path, "name": bot.name, "botId": bot.id,
            "trusted": False, "stockfish": False}


@app.post("/api/exhibitions")
def exhibition(body: Exhibition, request: Request, response: Response, db: Session = Depends(get_db)):
    user = read_session(request)
    if not re.fullmatch(r"\d+(?:\.\d+)?\+\d+(?:\.\d+)?", body.time_control):
        raise HTTPException(400, "Invalid time control")
    white, black = resolve_engine(body.white, db), resolve_engine(body.black, db)
    base = float(body.time_control.split("+", 1)[0])
    row = Game(mode="exhibition", white_bot_id=white["botId"], black_bot_id=black["botId"],
               white_name=white["name"], black_name=black["name"], result="*", status="queued",
               current_fen=chess.STARTING_FEN, moves_json="[]", time_control=body.time_control,
               white_clock_ms=int(base * 1000), black_clock_ms=int(base * 1000),
               engine_config_json=json.dumps({"white": white, "black": black}),
               creator_owner_id=user["owner"])
    db.add(row); db.commit(); db.refresh(row)
    live_manager.start_showdown(row.id)
    response.status_code = 202
    return game_snapshot(row, user["owner"], bool(user.get("admin")))


@app.post("/api/human-games")
def human_start(body: HumanStart, request: Request, db: Session = Depends(get_db)):
    user = read_session(request)
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
    return game_snapshot(row, user["owner"], bool(user.get("admin")))


@app.post("/api/human-games/{game_id}/move")
def human_move(game_id: int, body: HumanMove, request: Request, db: Session = Depends(get_db)):
    user = read_session(request); row = db.get(Game, game_id)
    if not row or row.mode != "human" or row.status != "running": raise HTTPException(400, "Game is not active")
    config = parse_json(row.engine_config_json, {})
    if row.creator_owner_id != user.get("owner") and not user.get("admin"):
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
    return game_snapshot(row, user["owner"], bool(user.get("admin")))


@app.post("/api/human-games/{game_id}/resign")
def resign_human(game_id: int, request: Request, db: Session = Depends(get_db)):
    user = read_session(request); row = db.get(Game, game_id)
    if not row or row.mode != "human" or row.status != "running": raise HTTPException(400, "Game is not active")
    if row.creator_owner_id != user.get("owner") and not user.get("admin"): raise HTTPException(403, "Only the player can resign")
    config = parse_json(row.engine_config_json, {})
    row.result = "0-1" if config.get("humanColor") == "white" else "1-0"
    row.status, row.termination, row.completed_at = "completed", "resignation", utcnow()
    db.commit(); return game_snapshot(row, user["owner"], bool(user.get("admin")))


@app.post("/api/games/{game_id}/abort")
def abort_game(game_id: int, request: Request, db: Session = Depends(get_db)):
    user = read_session(request); row = db.get(Game, game_id)
    if not row: raise HTTPException(404, "Game not found")
    if row.creator_owner_id != user.get("owner") and not user.get("admin"): raise HTTPException(403, "Not allowed")
    if row.status not in ("queued", "running"): raise HTTPException(400, "Game has already finished")
    row.status, row.termination, row.completed_at = "aborted", "aborted", utcnow()
    db.commit(); return game_snapshot(row, user["owner"], bool(user.get("admin")))


@app.websocket("/api/games/{game_id}/stream")
async def game_stream(websocket: WebSocket, game_id: int):
    try:
        user = read_session(websocket)
    except HTTPException:
        await websocket.close(code=4401); return
    with SessionLocal() as db:
        if not db.get(Game, game_id):
            await websocket.close(code=4404); return
    await websocket.accept()
    live_manager.viewer_joined(game_id)
    last = None
    try:
        while True:
            with SessionLocal() as db:
                row = db.get(Game, game_id)
                payload = game_snapshot(row, user.get("owner"), bool(user.get("admin")))
            encoded = json.dumps(payload, sort_keys=True)
            if encoded != last:
                await websocket.send_json({"type": "snapshot", "game": payload})
                last = encoded
            try:
                message = await asyncio.wait_for(websocket.receive_json(), timeout=.25)
                if message.get("type") == "focus_ply":
                    live_manager.set_focus(game_id, int(message.get("ply", 0)))
            except asyncio.TimeoutError:
                live_manager.ensure_analysis(game_id)
    except WebSocketDisconnect:
        pass
    finally:
        live_manager.viewer_left(game_id)


@app.get("/api/admin/settings")
def admin_settings(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    return {"gamesPerPair": int(get_setting(db, "games_per_pair", "2")), "timeControl": get_setting(db, "time_control", "10+0.1"), "kFactor": float(get_setting(db, "k_factor", "32"))}


@app.put("/api/admin/settings")
def update_settings(body: SettingsUpdate, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    if body.games_per_pair < 2 or body.games_per_pair > 100 or body.games_per_pair % 2: raise HTTPException(400, "Games must be even, from 2 to 100")
    if not re.fullmatch(r"\d+(?:\.\d+)?\+\d+(?:\.\d+)?", body.time_control): raise HTTPException(400, "Use a time control such as 10+0.1")
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
    bot.status = "retired"; Path(bot.binary_path).unlink(missing_ok=True); db.commit(); recount(db); return {"ok": True}
