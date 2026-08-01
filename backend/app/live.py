from __future__ import annotations

import io
import json
import threading
import time
from datetime import datetime, timezone

import chess
import chess.engine
import chess.pgn
from sqlalchemy import select

from .config import settings
from .db import SessionLocal
from .models import Game
from .runner import engine_argv


START_FEN = chess.STARTING_FEN


def utcnow():
    return datetime.now(timezone.utc)


def parse_json(value: str | None, default):
    try:
        return json.loads(value) if value else default
    except (TypeError, json.JSONDecodeError):
        return default


def moves_for_game(game: Game) -> list[dict]:
    stored = parse_json(game.moves_json, [])
    if stored:
        return stored
    if not game.pgn:
        return []
    parsed = chess.pgn.read_game(io.StringIO(game.pgn))
    if not parsed:
        return []
    board, moves = parsed.board(), []
    for move in parsed.mainline_moves():
        san = board.san(move)
        board.push(move)
        moves.append({"uci": move.uci(), "san": san, "fen": board.fen(), "elapsedMs": None})
    return moves


def board_from_moves(moves: list[dict]) -> chess.Board:
    board = chess.Board()
    for item in moves:
        board.push_uci(item["uci"])
    return board


def export_pgn(game: Game, moves: list[dict], board: chess.Board) -> str:
    record = chess.pgn.Game()
    record.headers.update({
        "Event": "Chess Bot Fight Club",
        "White": game.white_name,
        "Black": game.black_name,
        "Result": game.result,
        "TimeControl": game.time_control,
    })
    node, replay = record, chess.Board()
    for item in moves:
        move = replay.parse_uci(item["uci"])
        node = node.add_variation(move)
        replay.push(move)
    return record.accept(chess.pgn.StringExporter(headers=True, variations=False, comments=False))


def game_snapshot(game: Game, owner_id: str | None = None, admin: bool = False) -> dict:
    moves = moves_for_game(game)
    analysis = parse_json(game.analysis_json, [])
    fen = game.current_fen or (moves[-1]["fen"] if moves else START_FEN)
    config = parse_json(game.engine_config_json, {})
    return {
        "id": game.id,
        "mode": game.mode,
        "status": game.status or ("running" if game.result == "*" else "completed"),
        "whiteName": game.white_name,
        "blackName": game.black_name,
        "whiteBotId": game.white_bot_id,
        "blackBotId": game.black_bot_id,
        "result": game.result,
        "termination": game.termination,
        "timeControl": game.time_control,
        "fen": fen,
        "turn": "white" if chess.Board(fen).turn else "black",
        "moves": moves,
        "analysis": analysis,
        "whiteClockMs": game.white_clock_ms,
        "blackClockMs": game.black_clock_ms,
        "error": game.error,
        "canAbort": admin or bool(owner_id and owner_id == game.creator_owner_id),
        "humanColor": config.get("humanColor"),
        "moveTimeMs": config.get("moveTimeMs"),
        "stockfishSkill": config.get("stockfishSkill"),
        "createdAt": game.created_at.isoformat() if game.created_at else None,
    }


class LiveGameManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._controllers: set[int] = set()
        self._human_turns: set[int] = set()
        self._analysis: set[int] = set()
        self._analysis_slot = threading.Semaphore(1)
        self._viewers: dict[int, int] = {}
        self._focus: dict[int, int] = {}

    def viewer_joined(self, game_id: int):
        with self._lock:
            self._viewers[game_id] = self._viewers.get(game_id, 0) + 1
        self.ensure_analysis(game_id)

    def viewer_left(self, game_id: int):
        with self._lock:
            self._viewers[game_id] = max(0, self._viewers.get(game_id, 1) - 1)

    def set_focus(self, game_id: int, ply: int):
        with self._lock:
            self._focus[game_id] = max(0, ply)
        self.ensure_analysis(game_id)

    def has_viewers(self, game_id: int) -> bool:
        with self._lock:
            return self._viewers.get(game_id, 0) > 0

    def start_showdown(self, game_id: int):
        with self._lock:
            if game_id in self._controllers:
                return
            self._controllers.add(game_id)
        threading.Thread(target=self._showdown_guard, args=(game_id,), daemon=True).start()

    def _showdown_guard(self, game_id: int):
        try:
            self._run_showdown(game_id)
        finally:
            with self._lock:
                self._controllers.discard(game_id)

    def _run_showdown(self, game_id: int):
        white_engine = black_engine = None
        try:
            with SessionLocal() as db:
                game = db.get(Game, game_id)
                if not game or game.status not in ("queued", "running"):
                    return
                config = parse_json(game.engine_config_json, {})
                moves = moves_for_game(game)
                board = board_from_moves(moves)
                base, increment = (float(part) for part in game.time_control.split("+", 1))
                white_ms = game.white_clock_ms if game.white_clock_ms is not None else int(base * 1000)
                black_ms = game.black_clock_ms if game.black_clock_ms is not None else int(base * 1000)
                game.status, game.started_at = "running", game.started_at or utcnow()
                game.current_fen = board.fen()
                game.moves_json = json.dumps(moves)
                game.white_clock_ms, game.black_clock_ms = white_ms, black_ms
                db.commit()
            white_engine = chess.engine.SimpleEngine.popen_uci(self._engine_command(config["white"]))
            black_engine = chess.engine.SimpleEngine.popen_uci(self._engine_command(config["black"]))
            while not board.is_game_over(claim_draw=True):
                with SessionLocal() as db:
                    game = db.get(Game, game_id)
                    if not game or game.status == "aborted":
                        return
                engine = white_engine if board.turn else black_engine
                started = time.monotonic()
                try:
                    result = engine.play(board, chess.engine.Limit(
                        white_clock=max(0.001, white_ms / 1000),
                        black_clock=max(0.001, black_ms / 1000),
                        white_inc=increment,
                        black_inc=increment,
                    ))
                except (chess.engine.EngineError, chess.engine.EngineTerminatedError) as exc:
                    with SessionLocal() as db:
                        game = db.get(Game, game_id)
                        game.result = "0-1" if board.turn else "1-0"
                        game.termination = "engine failure"
                        game.status, game.error, game.completed_at = "completed", str(exc), utcnow()
                        game.pgn = export_pgn(game, moves, board)
                        db.commit()
                    return
                elapsed_ms = max(1, int((time.monotonic() - started) * 1000))
                if result.move not in board.legal_moves:
                    raise RuntimeError("Engine returned an illegal move")
                mover_white = board.turn
                if mover_white:
                    white_ms = white_ms - elapsed_ms + int(increment * 1000)
                else:
                    black_ms = black_ms - elapsed_ms + int(increment * 1000)
                if (mover_white and white_ms < 0) or (not mover_white and black_ms < 0):
                    with SessionLocal() as db:
                        game = db.get(Game, game_id)
                        game.result = "0-1" if mover_white else "1-0"
                        game.termination = "time forfeit"
                        game.status, game.completed_at = "completed", utcnow()
                        db.commit()
                    return
                san = board.san(result.move)
                board.push(result.move)
                moves.append({"uci": result.move.uci(), "san": san, "fen": board.fen(), "elapsedMs": elapsed_ms})
                time.sleep(max(0, (700 - elapsed_ms) / 1000))
                with SessionLocal() as db:
                    game = db.get(Game, game_id)
                    if not game or game.status == "aborted":
                        return
                    game.moves_json = json.dumps(moves)
                    game.current_fen = board.fen()
                    game.white_clock_ms, game.black_clock_ms = max(0, white_ms), max(0, black_ms)
                    game.pgn = export_pgn(game, moves, board)
                    db.commit()
                if self.has_viewers(game_id):
                    self.ensure_analysis(game_id)
            with SessionLocal() as db:
                game = db.get(Game, game_id)
                game.result = board.result(claim_draw=True)
                game.termination = board.outcome(claim_draw=True).termination.name.lower().replace("_", " ")
                game.status, game.completed_at = "completed", utcnow()
                game.pgn = export_pgn(game, moves, board)
                db.commit()
        except Exception as exc:
            with SessionLocal() as db:
                game = db.get(Game, game_id)
                if game and game.status != "aborted":
                    game.status, game.error, game.completed_at = "failed", str(exc), utcnow()
                    db.commit()
        finally:
            for engine in (white_engine, black_engine):
                if engine:
                    try:
                        engine.quit()
                    except Exception:
                        pass

    def _engine_command(self, config: dict):
        path = config["path"]
        return [path] if config.get("trusted") else engine_argv(path)

    def start_human_engine_turn(self, game_id: int):
        with self._lock:
            if game_id in self._human_turns:
                return
            self._human_turns.add(game_id)
        threading.Thread(target=self._human_guard, args=(game_id,), daemon=True).start()

    def _human_guard(self, game_id: int):
        try:
            self._run_human_turn(game_id)
        finally:
            with self._lock:
                self._human_turns.discard(game_id)

    def _run_human_turn(self, game_id: int):
        engine = None
        try:
            with SessionLocal() as db:
                game = db.get(Game, game_id)
                if not game or game.status != "running":
                    return
                config = parse_json(game.engine_config_json, {})
                moves = moves_for_game(game)
                board = board_from_moves(moves)
                human_white = config["humanColor"] == "white"
                if board.turn == human_white:
                    return
                opponent = config["opponent"]
            engine = chess.engine.SimpleEngine.popen_uci(self._engine_command(opponent))
            if opponent.get("stockfish"):
                engine.configure({"Skill Level": int(config.get("stockfishSkill", 10))})
            result = engine.play(board, chess.engine.Limit(time=max(.1, config["moveTimeMs"] / 1000)))
            if result.move not in board.legal_moves:
                raise RuntimeError("Engine returned an illegal move")
            san = board.san(result.move)
            board.push(result.move)
            moves.append({"uci": result.move.uci(), "san": san, "fen": board.fen(), "elapsedMs": None})
            with SessionLocal() as db:
                game = db.get(Game, game_id)
                game.moves_json, game.current_fen = json.dumps(moves), board.fen()
                if board.is_game_over(claim_draw=True):
                    game.result = board.result(claim_draw=True)
                    game.termination = board.outcome(claim_draw=True).termination.name.lower().replace("_", " ")
                    game.status, game.completed_at = "completed", utcnow()
                game.pgn = export_pgn(game, moves, board)
                db.commit()
            self.ensure_analysis(game_id)
        except Exception as exc:
            with SessionLocal() as db:
                game = db.get(Game, game_id)
                if game:
                    config = parse_json(game.engine_config_json, {})
                    game.result = "1-0" if config.get("humanColor") == "white" else "0-1"
                    game.status, game.termination = "completed", "engine failure"
                    game.error, game.completed_at = str(exc), utcnow()
                    db.commit()
        finally:
            if engine:
                try:
                    engine.quit()
                except Exception:
                    pass

    def ensure_analysis(self, game_id: int):
        if not self.has_viewers(game_id):
            return
        with self._lock:
            if game_id in self._analysis:
                return
            self._analysis.add(game_id)
        threading.Thread(target=self._analysis_guard, args=(game_id,), daemon=True).start()

    def _analysis_guard(self, game_id: int):
        try:
            self._analyse_while_viewed(game_id)
        finally:
            with self._lock:
                self._analysis.discard(game_id)

    def _analyse_while_viewed(self, game_id: int):
        engine = None
        try:
            engine = chess.engine.SimpleEngine.popen_uci(settings.stockfish_path)
            while self.has_viewers(game_id):
                with SessionLocal() as db:
                    game = db.get(Game, game_id)
                    if not game:
                        return
                    moves = moves_for_game(game)
                    analysis = parse_json(game.analysis_json, [])
                    if len(analysis) < len(moves):
                        analysis.extend([None] * (len(moves) - len(analysis)))
                    missing = [index for index in range(len(moves)) if analysis[index] is None]
                    if not missing:
                        time.sleep(.2)
                        continue
                    focus = self._focus.get(game_id, len(moves) - 1)
                    index = min(missing, key=lambda value: abs(value - focus))
                    fen = moves[index]["fen"]
                    live = game.status == "running" and index == len(moves) - 1
                board = chess.Board(fen)
                with self._analysis_slot:
                    info = engine.analyse(board, chess.engine.Limit(time=.15) if live else chess.engine.Limit(depth=12))
                score = info["score"].pov(chess.WHITE)
                pv_board, pv_san = board.copy(), []
                for move in info.get("pv", [])[:8]:
                    if move not in pv_board.legal_moves:
                        break
                    pv_san.append(pv_board.san(move)); pv_board.push(move)
                entry = {
                    "eval": round((score.score(mate_score=100000) or 0) / 100, 2),
                    "mate": score.mate(),
                    "best": info.get("pv", [None])[0].uci() if info.get("pv") else None,
                    "pv": pv_san,
                    "depth": info.get("depth"),
                }
                with SessionLocal() as db:
                    game = db.get(Game, game_id)
                    current = parse_json(game.analysis_json, [])
                    if len(current) < len(moves):
                        current.extend([None] * (len(moves) - len(current)))
                    current[index] = entry
                    game.analysis_json = json.dumps(current)
                    db.commit()
        finally:
            if engine:
                try:
                    engine.quit()
                except Exception:
                    pass

    def resume(self):
        with SessionLocal() as db:
            games = list(db.scalars(select(Game).where(Game.mode == "exhibition", Game.status.in_(["queued", "running"]))))
            human_games = list(db.scalars(select(Game).where(Game.mode == "human", Game.status == "running")))
        for game in games:
            self.start_showdown(game.id)
        for game in human_games:
            config = parse_json(game.engine_config_json, {})
            if not config:
                continue
            board = board_from_moves(moves_for_game(game))
            human_white = config.get("humanColor") == "white"
            if board.turn != human_white:
                self.start_human_engine_turn(game.id)


live_manager = LiveGameManager()
