import json
import unittest

import chess

from app.live import board_from_moves, export_pgn, game_snapshot
from app.models import Game


class LiveGameTests(unittest.TestCase):
    def make_game(self):
        return Game(
            id=42,
            mode="human",
            status="running",
            white_name="Human",
            black_name="Fixture",
            result="*",
            time_control="movetime 500",
            current_fen=chess.STARTING_FEN,
            moves_json="[]",
            engine_config_json=json.dumps({"humanColor": "white", "moveTimeMs": 500}),
            creator_owner_id="owner",
        )

    def test_snapshot_exposes_play_state_without_engine_path(self):
        game = self.make_game()
        snapshot = game_snapshot(game, "owner")
        self.assertEqual(snapshot["humanColor"], "white")
        self.assertTrue(snapshot["canAbort"])
        self.assertIsNone(snapshot["whiteAvatarUrl"])
        self.assertIsNone(snapshot["blackAvatarUrl"])
        self.assertNotIn("enginePath", snapshot)

    def test_move_round_trip_to_pgn(self):
        game = self.make_game()
        board = chess.Board()
        moves = []
        for uci in ("e2e4", "e7e5", "g1f3"):
            move = board.parse_uci(uci)
            san = board.san(move)
            board.push(move)
            moves.append({"uci": uci, "san": san, "fen": board.fen(), "elapsedMs": 10})
        replay = board_from_moves(moves)
        self.assertEqual(replay.fen(), board.fen())
        self.assertIn("1. e4 e5 2. Nf3", export_pgn(game, moves, board))


if __name__ == "__main__":
    unittest.main()
