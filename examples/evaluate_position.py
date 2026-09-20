#!/usr/bin/env python3
"""Example: use the engine as a library to analyze a single FEN position.

This is not a full game -- it's the kind of thing you'd reach for to
sanity-check the evaluation function or find the engine's suggested move
in one specific position, without playing an interactive game.

Usage:
    python examples/evaluate_position.py
    python examples/evaluate_position.py --fen "<some FEN>" --depth 4
"""

import argparse
import os
import sys

import chess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chess_bot.evaluation import evaluate
from chess_bot.search import ChessEngine

# A well-known tactical puzzle position (White to move, mate in 2).
DEFAULT_FEN = "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fen", default=DEFAULT_FEN, help="FEN of the position to analyze")
    parser.add_argument("--depth", type=int, default=4, help="search depth (default: 4)")
    args = parser.parse_args()

    board = chess.Board(args.fen)
    print(f"Position:\n{board}\n")
    print(f"Static evaluation (no search): {evaluate(board) / 100:+.2f}")

    engine = ChessEngine(depth=args.depth)
    move, score = engine.choose_move(board)

    if move is None:
        print("No legal moves -- game is already over.")
        return

    print(
        f"Best move at depth {args.depth}: {board.san(move)} "
        f"(eval={score / 100:+.2f}, nodes visited={engine.stats.nodes_visited})"
    )


if __name__ == "__main__":
    main()
