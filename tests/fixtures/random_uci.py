#!/usr/bin/env python3
import sys
import chess

board = chess.Board()
for raw in sys.stdin:
    parts = raw.strip().split()
    if not parts:
        continue
    if parts[0] == "uci":
        print("id name ChESSPIT Random Fixture\nid author ChESSPIT\nuciok", flush=True)
    elif parts[0] == "isready":
        print("readyok", flush=True)
    elif parts[0] == "ucinewgame":
        board.reset()
    elif parts[0] == "position":
        board.reset()
        if "fen" in parts:
            start = parts.index("fen") + 1
            end = parts.index("moves") if "moves" in parts else len(parts)
            board.set_fen(" ".join(parts[start:end]))
        if "moves" in parts:
            for move in parts[parts.index("moves") + 1:]:
                board.push_uci(move)
    elif parts[0] == "go":
        move = next(iter(board.legal_moves), None)
        print(f"bestmove {move.uci() if move else '(none)'}", flush=True)
    elif parts[0] == "quit":
        break
