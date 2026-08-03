from __future__ import annotations
import io
import json
import os
import resource
import subprocess
import threading
import secrets
import socket
import stat
import logging
from pathlib import Path
import chess
import chess.engine
import chess.pgn
from sqlalchemy import select, func, update
from .config import settings
from .db import SessionLocal
from .models import Bot, Game, RatingEvent, ArenaSetting, RatingRun, now


STOCKFISH_LEVELS = (1, 2, 3, 5, 8, 13, 20)
RATING_TIME_CONTROLS = (
    ("1+0", "1 sec + 0 sec increment"),
    ("2+0.02", "2 sec + 0.02 sec increment"),
    ("3+0.03", "3 sec + 0.03 sec increment"),
    ("5+0.05", "5 sec + 0.05 sec increment"),
    ("10+0.1", "10 sec + 0.1 sec increment"),
    ("15+0.1", "15 sec + 0.1 sec increment"),
    ("30+0.3", "30 sec + 0.3 sec increment"),
    ("60+0.6", "60 sec + 0.6 sec increment"),
    ("120+1", "120 sec + 1 sec increment"),
)
RATING_TIME_CONTROL_VALUES = frozenset(value for value, _ in RATING_TIME_CONTROLS)
DEFAULT_RATING_TIME_CONTROL = "10+0.1"
RATING_RUN_ACTIVE_STATUSES = ("queued", "running", "cancelling")
_rating_lock = threading.Lock()
logger = logging.getLogger(__name__)


def _limits():
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
    resource.setrlimit(resource.RLIMIT_FSIZE, (20 * 1024 * 1024, 20 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def sandbox_ready() -> bool:
    if settings.runner_mode != "socket":
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(1)
            client.connect(settings.runner_socket)
            client.sendall(b'{"version":1,"op":"health"}\n')
            return b'"ok":true' in client.recv(256)
    except OSError:
        return False


def engine_argv(path: str, sha256: str = "", trusted: bool = False,
                purpose: str = "live") -> list[str]:
    if trusted:
        return [path]
    if settings.runner_mode != "socket":
        raise RuntimeError("Uploaded-engine sandbox is unavailable")
    key = Path(path).name
    if not sha256:
        raise RuntimeError("Uploaded engine has no verified digest")
    return [settings.runner_wrapper, purpose, key, sha256]


def engine_options(path: str, name: str, trusted: bool = False, sha256: str = "",
                   purpose: str = "rated",
                   uci_options: dict[str, str | int] | None = None) -> list[str]:
    argv = engine_argv(path, sha256, trusted, purpose)
    values = ["-engine", f"cmd={argv[0]}", f"name={name}"]
    values.extend(f"arg={arg}" for arg in argv[1:])
    values.extend(f"option.{key}={value}" for key, value in (uci_options or {}).items())
    return values


def options_for_bot(bot: Bot) -> list[str]:
    if bot.engine_kind == "stockfish":
        return engine_options(settings.stockfish_path, bot.name, trusted=True,
                              uci_options={"Skill Level": int(bot.stockfish_skill or 0)})
    return engine_options(bot.binary_path, bot.name, sha256=bot.sha256)


def stockfish_description(skill: int) -> str:
    descriptions = {
        1: "Stockfish benchmark at Skill Level 1: a restrained tactical baseline.",
        2: "Low-strength Stockfish benchmark for early ladder testing.",
        3: "Developing Stockfish benchmark with basic tactical pressure.",
        5: "Mid-low Stockfish benchmark balancing tactics and safety.",
        8: "Intermediate Stockfish benchmark with sharper calculation.",
        13: "Strong Stockfish benchmark with consistent tactical depth.",
        20: "High-strength Stockfish benchmark with relentless calculation.",
    }
    return descriptions.get(skill, f"Stockfish benchmark at Skill Level {skill}.")


def rating_time_controls() -> list[dict[str, str]]:
    return [{"value": value, "label": label} for value, label in RATING_TIME_CONTROLS]


def normalize_rating_time_control(value: str) -> str:
    return value if value in RATING_TIME_CONTROL_VALUES else DEFAULT_RATING_TIME_CONTROL


def ensure_stockfish_bots():
    """Create or refresh the locked rated Stockfish competitors."""
    path = Path(settings.stockfish_path)
    available = path.is_file()
    digest = "0" * 64
    if available:
        import hashlib
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with SessionLocal() as db:
        for skill in STOCKFISH_LEVELS:
            bot = db.scalar(select(Bot).where(Bot.engine_kind == "stockfish",
                                              Bot.stockfish_skill == skill))
            if not bot:
                name = f"Stockfish Level {skill}"
                collision = db.scalar(select(Bot).where(func.lower(Bot.name) == name.lower()))
                if collision:
                    name = f"Stockfish Skill {skill}"
                bot = Bot(name=name, binary_path=str(path), sha256=digest, owner_id="system",
                          recovery_hash="", engine_kind="stockfish", stockfish_skill=skill)
                db.add(bot)
            bot.binary_path = str(path)
            bot.sha256 = digest
            if not bot.description:
                bot.description = stockfish_description(skill)
            bot.status = "active" if available else "unavailable"
            bot.failure_reason = None if available else "Stockfish binary is unavailable"
        db.commit()


def audit_uploaded_bots():
    """Backfill sizes and quarantine storage rows that cannot be trusted."""
    root = (settings.storage_dir / "bots").resolve()
    with SessionLocal() as db:
        for bot in db.scalars(select(Bot).where(Bot.engine_kind == "uploaded", Bot.status != "retired")):
            path = Path(bot.binary_path)
            try:
                info = path.lstat()
                valid_path = path.parent.resolve() == root and not path.is_symlink() and stat.S_ISREG(info.st_mode)
                if not valid_path or info.st_size > 50 * 1024 * 1024:
                    raise ValueError("unsafe stored binary")
                import hashlib
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                if digest != bot.sha256:
                    raise ValueError("stored binary digest mismatch")
                bot.binary_size = info.st_size
                path.chmod(0o540)
            except (OSError, ValueError):
                bot.status = "rejected"
                bot.failure_reason = "Stored executable failed the security audit"
                bot.binary_size = 0
        db.commit()


def validate_uci(path: str, sha256: str) -> tuple[bool, str | None]:
    try:
        proc = subprocess.Popen(engine_argv(path, sha256, purpose="validate"), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, preexec_fn=_limits)
        out, _ = proc.communicate("uci\nquit\n", timeout=10)
        if "uciok" not in out:
            return False, "Executable did not complete the UCI handshake"
        return True, None
    except subprocess.TimeoutExpired:
        proc.kill()
        return False, "UCI handshake timed out"
    except Exception as exc:
        logger.warning("Sandboxed UCI validation failed", exc_info=exc)
        return False, "Sandboxed executable could not complete validation"


def qualify_bot(bot_id: int):
    with _rating_lock:
        with SessionLocal() as db:
            bot = db.get(Bot, bot_id)
            if not bot:
                return
            ok, reason = validate_uci(bot.binary_path, bot.sha256)
            if not ok:
                bot.status, bot.failure_reason = "rejected", reason
                db.commit()
                return
            opponents = list(db.scalars(select(Bot).where(Bot.status == "active", Bot.id != bot.id)))
            count = int(get_setting(db, "games_per_pair", "2"))
            bot.status = "qualifying"
            bot.qualification_total = len(opponents) * count
            bot.qualification_done = 0
            db.commit()
        try:
            for opponent in opponents:
                played = run_pairing(bot_id, opponent.id, count)
                with SessionLocal() as db:
                    bot = db.get(Bot, bot_id)
                    if bot:
                        bot.qualification_done += played
                        db.commit()
        except Exception as exc:
            logger.exception("Sandboxed qualification failed for bot %s", bot_id)
            with SessionLocal() as db:
                bot = db.get(Bot, bot_id)
                if bot:
                    bot.status, bot.failure_reason = "rejected", "Sandboxed qualification match failed"
                    db.commit()
            return
        with SessionLocal() as db:
            bot = db.get(Bot, bot_id)
            if bot and bot.status == "qualifying":
                bot.status = "active"
                db.commit()
                recount(db)


def run_pairing(first_id: int, second_id: int, count: int | None = None) -> int:
    with SessionLocal() as db:
        first, second = db.get(Bot, first_id), db.get(Bot, second_id)
        if not first or not second or first.status not in ("active", "qualifying") or second.status != "active":
            raise RuntimeError("A rated competitor is no longer active")
        count = count or int(get_setting(db, "games_per_pair", "2"))
        if count % 2:
            count += 1
        tc = normalize_rating_time_control(get_setting(db, "time_control", DEFAULT_RATING_TIME_CONTROL))
        out_path = settings.storage_dir / "matches" / f"pair-{first_id}-{second_id}-{secrets.token_hex(8)}.pgn"
        command = [settings.fastchess_path, *options_for_bot(first), *options_for_bot(second), "-each", f"tc={tc}",
                   "proto=uci", "-rounds", str(max(1, count // 2)), "-repeat", "-games", "2",
                   "-concurrency", "1", "-pgnout", f"file={out_path}", "-recover"]
    subprocess.run(command, timeout=max(120, count * 120), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
    return import_pgn(out_path, "rated", first.id, second.id, tc)


def import_pgn(path: Path, mode: str, first_id: int | None, second_id: int | None, tc: str):
    count = 0
    with path.open(errors="replace") as handle, SessionLocal() as db:
        while game := chess.pgn.read_game(handle):
            text = io.StringIO()
            print(game, file=text, end="\n\n")
            white = game.headers.get("White", "Unknown")
            black = game.headers.get("Black", "Unknown")
            a, b = db.get(Bot, first_id) if first_id else None, db.get(Bot, second_id) if second_id else None
            white_id = a.id if a and white == a.name else b.id if b and white == b.name else None
            black_id = a.id if a and black == a.name else b.id if b and black == b.name else None
            record = Game(mode=mode, white_bot_id=white_id, black_bot_id=black_id, white_name=white,
                          black_name=black, result=game.headers.get("Result", "*"),
                          termination=game.headers.get("Termination"), pgn=text.getvalue(), time_control=tc)
            db.add(record)
            count += 1
        db.commit()
    return count


def recount(db):
    bots = list(db.scalars(select(Bot).where(Bot.status == "active")))
    before = {bot.id: bot.rating for bot in bots}
    ratings = {b.id: 1500.0 for b in bots}
    records = {b.id: [0, 0, 0] for b in bots}
    events = [(g.created_at, "game", g) for g in db.scalars(select(Game).where(
        Game.mode == "rated", Game.status == "completed", Game.deleted == False))]
    events += [(e.created_at, "set", e) for e in db.scalars(select(RatingEvent))]
    k = float(get_setting(db, "k_factor", "32"))
    for _, kind, item in sorted(events, key=lambda x: (x[0], x[2].id)):
        if kind == "set":
            if item.bot_id in ratings: ratings[item.bot_id] = item.value
            continue
        if item.white_bot_id not in ratings or item.black_bot_id not in ratings or item.result not in ("1-0", "0-1", "1/2-1/2"):
            continue
        w, b = item.white_bot_id, item.black_bot_id
        sw = 1.0 if item.result == "1-0" else 0.0 if item.result == "0-1" else 0.5
        ew = 1 / (1 + 10 ** ((ratings[b] - ratings[w]) / 400))
        ratings[w] += k * (sw - ew); ratings[b] += k * ((1 - sw) - (1 - ew))
        if sw == 1: records[w][0] += 1; records[b][2] += 1
        elif sw == 0: records[b][0] += 1; records[w][2] += 1
        else: records[w][1] += 1; records[b][1] += 1
    for bot in bots:
        bot.rating = round(ratings[bot.id], 1)
        bot.wins, bot.draws, bot.losses = records[bot.id]
    db.commit()
    return {
        "gamesProcessed": sum(sum(value) for value in records.values()) // 2,
        "competitorsUpdated": len(bots),
        "changes": [
            {"botId": bot.id, "name": bot.name, "before": before[bot.id], "after": bot.rating}
            for bot in bots if before[bot.id] != bot.rating
        ],
    }


def _valid_rated_count(db, first_id: int, second_id: int) -> int:
    return int(db.scalar(select(func.count(Game.id)).where(
        Game.mode == "rated", Game.status == "completed", Game.deleted == False,
        Game.result.in_(("1-0", "0-1", "1/2-1/2")),
        ((Game.white_bot_id == first_id) & (Game.black_bot_id == second_id)) |
        ((Game.white_bot_id == second_id) & (Game.black_bot_id == first_id)),
    )) or 0)


def missing_pairings(db) -> list[tuple[int, int, int, str]]:
    bots = list(db.scalars(select(Bot).where(Bot.status == "active").order_by(Bot.id)))
    desired = int(get_setting(db, "games_per_pair", "2"))
    missing = []
    for index, first in enumerate(bots):
        for second in bots[index + 1:]:
            deficit = max(0, desired - _valid_rated_count(db, first.id, second.id))
            if deficit:
                game_count = deficit if deficit % 2 == 0 else deficit + 1
                missing.append((first.id, second.id, game_count, f"{first.name} vs {second.name}"))
    return missing


def rating_run_json(run: RatingRun | None) -> dict:
    if not run:
        return {"status": "idle", "totalPairings": 0, "completedPairings": 0,
                "totalGames": 0, "completedGames": 0, "currentPairing": None, "error": None}
    return {"id": run.id, "status": run.status, "totalPairings": run.total_pairings,
            "completedPairings": run.completed_pairings, "totalGames": run.total_games,
            "completedGames": run.completed_games, "currentPairing": run.current_pairing,
            "error": run.error, "createdAt": run.created_at, "completedAt": run.completed_at}


def current_rating_run(db) -> RatingRun | None:
    return db.scalar(select(RatingRun).order_by(RatingRun.id.desc()).limit(1))


def start_missing_rating_run() -> RatingRun:
    with SessionLocal() as db:
        current = current_rating_run(db)
        if current and current.status in RATING_RUN_ACTIVE_STATUSES:
            return current
        run = RatingRun(status="queued")
        db.add(run); db.commit(); db.refresh(run)
        run_id = run.id
    threading.Thread(target=_rating_run_worker, args=(run_id,), daemon=True).start()
    with SessionLocal() as db:
        return db.get(RatingRun, run_id)


def _mark_rating_run_cancelled(run: RatingRun):
    run.status = "cancelled"
    run.current_pairing = None
    run.completed_at = now()


def cancel_current_rating_run() -> RatingRun | None:
    with SessionLocal() as db:
        run = current_rating_run(db)
        if not run or run.status not in RATING_RUN_ACTIVE_STATUSES:
            return None
        if run.status == "queued":
            changed = db.execute(
                update(RatingRun)
                .where(RatingRun.id == run.id, RatingRun.status == "queued")
                .values(status="cancelled", current_pairing=None, completed_at=now())
            )
        elif run.status == "running":
            changed = db.execute(
                update(RatingRun)
                .where(RatingRun.id == run.id, RatingRun.status == "running")
                .values(status="cancelling", error=None)
            )
        else:
            db.refresh(run)
            return run
        if changed.rowcount != 1:
            db.rollback()
            latest = current_rating_run(db)
            return latest if latest and latest.status == "cancelling" else None
        db.commit()
        return db.get(RatingRun, run.id)


def _rating_run_worker(run_id: int):
    with _rating_lock:
        try:
            with SessionLocal() as db:
                run = db.get(RatingRun, run_id)
                if not run:
                    return
                if run.status == "cancelling":
                    _mark_rating_run_cancelled(run)
                    db.commit()
                    return
                if run.status not in ("queued", "running"):
                    return
                tasks = missing_pairings(db)
                changed = db.execute(
                    update(RatingRun)
                    .where(RatingRun.id == run_id, RatingRun.status.in_(("queued", "running")))
                    .values(
                        status="running",
                        completed_pairings=0,
                        completed_games=0,
                        total_pairings=len(tasks),
                        total_games=sum(task[2] for task in tasks),
                    )
                )
                if changed.rowcount != 1:
                    db.rollback()
                    return
                db.commit()
            for first_id, second_id, count, label in tasks:
                with SessionLocal() as db:
                    run = db.get(RatingRun, run_id)
                    if not run:
                        return
                    if run.status in ("cancelling", "cancelled"):
                        if run.status == "cancelling":
                            _mark_rating_run_cancelled(run)
                            db.commit()
                        return
                    run.current_pairing = label
                    db.commit()
                played = run_pairing(first_id, second_id, count)
                with SessionLocal() as db:
                    run = db.get(RatingRun, run_id)
                    if not run:
                        return
                    run.completed_pairings += 1
                    run.completed_games += played
                    recount(db)
                    db.refresh(run)
                    if run.status == "cancelling":
                        _mark_rating_run_cancelled(run)
                        db.commit()
                        return
                    db.commit()
            with SessionLocal() as db:
                run = db.get(RatingRun, run_id)
                if not run:
                    return
                changed = db.execute(
                    update(RatingRun)
                    .where(RatingRun.id == run_id, RatingRun.status == "running")
                    .values(status="completed", current_pairing=None, completed_at=now())
                )
                if changed.rowcount == 1:
                    db.commit()
                    return
                db.rollback()
                db.refresh(run)
                if run.status == "cancelling":
                    _mark_rating_run_cancelled(run)
                db.commit()
        except Exception as exc:
            logger.exception("Rating run %s failed", run_id)
            with SessionLocal() as db:
                run = db.get(RatingRun, run_id)
                if run:
                    if run.status == "cancelling":
                        _mark_rating_run_cancelled(run)
                    else:
                        run.status, run.error, run.completed_at = "failed", "Sandboxed rating match failed", now()
                    db.commit()


def resume_rating_run():
    with SessionLocal() as db:
        run = current_rating_run(db)
        if not run:
            return
        if run.status == "cancelling":
            _mark_rating_run_cancelled(run)
            db.commit()
            return
        if run.status not in ("queued", "running"):
            return
        run.status = "queued"
        run.error = None
        db.commit()
        run_id = run.id
    threading.Thread(target=_rating_run_worker, args=(run_id,), daemon=True).start()


def get_setting(db, key: str, default: str) -> str:
    row = db.get(ArenaSetting, key)
    return row.value if row else default


def analyse_game(game_id: int):
    if not Path(settings.stockfish_path).exists(): return
    with SessionLocal() as db:
        record = db.get(Game, game_id)
        if not record or record.analysis_json or not record.pgn: return
        pgn = chess.pgn.read_game(io.StringIO(record.pgn))
        if not pgn: return
        board, data = pgn.board(), []
        try:
            engine = chess.engine.SimpleEngine.popen_uci(settings.stockfish_path)
            for move in pgn.mainline_moves():
                before = engine.analyse(board, chess.engine.Limit(depth=12))
                best = before.get("pv", [None])[0]
                pov_before = before["score"].pov(board.turn).score(mate_score=100000) or 0
                san = board.san(move); mover = "white" if board.turn else "black"
                board.push(move)
                after = engine.analyse(board, chess.engine.Limit(depth=12))
                pov_after = -(after["score"].pov(board.turn).score(mate_score=100000) or 0)
                loss = max(0, pov_before - pov_after)
                label = "blunder" if loss >= 200 else "mistake" if loss >= 100 else "inaccuracy" if loss >= 50 else None
                data.append({"fen": board.fen(), "san": san, "uci": move.uci(), "mover": mover,
                             "eval": round((after["score"].pov(chess.WHITE).score(mate_score=100000) or 0) / 100, 2),
                             "loss": loss, "label": label, "best": best.uci() if best else None})
            engine.quit()
            record.analysis_json = json.dumps(data)
            db.commit()
        except Exception:
            return


def analyse_unanalysed():
    with SessionLocal() as db:
        ids = list(db.scalars(select(Game.id).where(Game.analysis_json == None, Game.deleted == False)))
    for game_id in ids: analyse_game(game_id)
