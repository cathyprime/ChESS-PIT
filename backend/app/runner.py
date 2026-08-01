from __future__ import annotations
import io
import json
import os
import resource
import subprocess
import threading
from pathlib import Path
import chess
import chess.engine
import chess.pgn
from sqlalchemy import select
from .config import settings
from .db import SessionLocal
from .models import Bot, Game, RatingEvent, ArenaSetting


def _limits():
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
    resource.setrlimit(resource.RLIMIT_FSIZE, (20 * 1024 * 1024, 20 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def engine_argv(path: str) -> list[str]:
    if settings.runner_mode == "local":
        return [path]
    return [settings.runner_wrapper, path]


def engine_options(path: str, name: str) -> list[str]:
    argv = engine_argv(path)
    values = ["-engine", f"cmd={argv[0]}", f"name={name}"]
    values.extend(f"arg={arg}" for arg in argv[1:])
    return values


def validate_uci(path: str) -> tuple[bool, str | None]:
    try:
        proc = subprocess.Popen(engine_argv(path), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, preexec_fn=_limits)
        out, _ = proc.communicate("uci\nquit\n", timeout=10)
        if "uciok" not in out:
            return False, "Executable did not complete the UCI handshake"
        return True, None
    except subprocess.TimeoutExpired:
        proc.kill()
        return False, "UCI handshake timed out"
    except Exception as exc:
        return False, f"Could not run executable: {exc}"


def qualify_bot(bot_id: int):
    with SessionLocal() as db:
        bot = db.get(Bot, bot_id)
        if not bot:
            return
        ok, reason = validate_uci(bot.binary_path)
        if not ok:
            bot.status, bot.failure_reason = "rejected", reason
            db.commit()
            return
        opponents = list(db.scalars(select(Bot).where(Bot.status == "active", Bot.id != bot.id)))
        bot.status = "qualifying"
        bot.qualification_total = len(opponents) * int(get_setting(db, "games_per_pair", "2"))
        db.commit()
    for opponent in opponents:
        run_pairing(bot_id, opponent.id)
    with SessionLocal() as db:
        bot = db.get(Bot, bot_id)
        if bot and bot.status == "qualifying":
            bot.status = "active"
            db.commit()
            recount(db)


def run_pairing(new_id: int, opponent_id: int):
    with SessionLocal() as db:
        first, second = db.get(Bot, new_id), db.get(Bot, opponent_id)
        if not first or not second or second.status != "active":
            return
        count = int(get_setting(db, "games_per_pair", "2"))
        tc = get_setting(db, "time_control", "10+0.1")
        out_path = settings.storage_dir / "matches" / f"pair-{new_id}-{opponent_id}.pgn"
        command = [settings.fastchess_path, *engine_options(first.binary_path, first.name),
                   *engine_options(second.binary_path, second.name), "-each", f"tc={tc}",
                   "proto=uci", "-rounds", str(max(1, count // 2)), "-repeat", "-games", "2",
                   "-concurrency", "1", "-pgnout", f"file={out_path}", "-recover"]
    try:
        subprocess.run(command, timeout=max(120, count * 120), check=True, capture_output=True, text=True)
        import_pgn(out_path, "rated", first.id, second.id, tc)
    except Exception as exc:
        with SessionLocal() as db:
            bot = db.get(Bot, new_id)
            if bot:
                bot.status, bot.failure_reason = "rejected", f"Match runner failed: {exc}"
                db.commit()


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
        bot = db.get(Bot, first_id) if first_id else None
        if bot:
            bot.qualification_done += count
        db.commit()


def recount(db):
    bots = list(db.scalars(select(Bot).where(Bot.status == "active")))
    ratings = {b.id: 1500.0 for b in bots}
    records = {b.id: [0, 0, 0] for b in bots}
    events = [(g.created_at, "game", g) for g in db.scalars(select(Game).where(Game.mode == "rated", Game.deleted == False))]
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
