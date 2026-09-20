#!/usr/bin/env python3
"""AI Chess Bot -- text CLI.

Play a game against the bot from the terminal, or watch the bot play a
quick demo game against itself.

Examples
--------
    python play.py                 # play White vs the bot (depth 3)
    python play.py --depth 4       # stronger (slower) bot
    python play.py --color black   # play as Black
    python play.py --self-play     # watch the bot play itself, depth 2
"""

import argparse
import sys
import time

import chess

from chess_bot import __version__
from chess_bot.evaluation import evaluate
from chess_bot.search import ChessEngine


def render(board: chess.Board) -> str:
    """Unicode board with file/rank labels."""
    lines = []
    for rank in range(7, -1, -1):
        row = [str(rank + 1)]
        for file in range(8):
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            row.append(piece.unicode_symbol() if piece else ".")
        lines.append(" ".join(row))
    lines.append("  a b c d e f g h")
    return "\n".join(lines)


def parse_move(board: chess.Board, text: str) -> chess.Move:
    text = text.strip()
    try:
        return board.parse_san(text)
    except ValueError:
        pass
    move = chess.Move.from_uci(text)
    if move not in board.legal_moves:
        raise ValueError(f"illegal move: {text}")
    return move


def print_result(board: chess.Board) -> None:
    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"
        print(f"Checkmate -- {winner} wins.")
    elif board.is_stalemate():
        print("Stalemate -- draw.")
    elif board.is_insufficient_material():
        print("Draw -- insufficient material.")
    elif board.can_claim_draw():
        print("Draw claimable (repetition / 50-move rule).")
    else:
        print("Game over.")


def human_vs_bot(depth: int, human_color: chess.Color) -> None:
    board = chess.Board()
    engine = ChessEngine(depth=depth)

    print("AI Chess Bot -- you are", "White" if human_color == chess.WHITE else "Black")
    print("Enter moves in algebraic notation (e.g. e4, Nf3, O-O) or UCI (e2e4).")
    print("Type 'quit' to exit.\n")

    while not board.is_game_over():
        print(render(board))
        print()
        if board.turn == human_color:
            move_text = input("Your move: ").strip()
            if move_text.lower() in {"quit", "exit"}:
                print("Bye.")
                return
            try:
                move = parse_move(board, move_text)
            except ValueError as exc:
                print(f"  {exc}\n")
                continue
            board.push(move)
        else:
            print("Bot is thinking...")
            start = time.time()
            move, score = engine.choose_move(board)
            elapsed = time.time() - start
            if move is None:
                break
            san = board.san(move)
            board.push(move)
            print(f"Bot plays: {san}  (eval={score/100:+.2f}, "
                  f"nodes={engine.stats.nodes_visited}, {elapsed:.2f}s)\n")

    print(render(board))
    print()
    print_result(board)


def self_play(depth: int, max_moves: int = 60) -> None:
    board = chess.Board()
    engine = ChessEngine(depth=depth)

    print(f"AI Chess Bot -- self-play demo game (depth={depth})\n")
    move_number = 1
    while not board.is_game_over() and move_number <= max_moves:
        move, score = engine.choose_move(board)
        if move is None:
            break
        san = board.san(move)
        side = "White" if board.turn == chess.WHITE else "Black"
        board.push(move)
        print(f"{move_number:3d}. {side:5s} {san:8s} eval={score/100:+.2f} "
              f"nodes={engine.stats.nodes_visited}")
        if board.turn == chess.WHITE:
            move_number += 1

    print()
    print(render(board))
    print()
    if board.is_game_over():
        print_result(board)
    else:
        print(f"Stopped after {max_moves} moves. Final eval: {evaluate(board)/100:+.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Play chess against a minimax/alpha-beta AI bot.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument("--depth", type=int, default=3, help="search depth (default: 3)")
    parser.add_argument("--color", choices=["white", "black"], default="white",
                         help="which color the human plays (default: white)")
    parser.add_argument("--self-play", action="store_true",
                         help="watch the bot play a quick demo game against itself")
    parser.add_argument("--max-moves", type=int, default=60,
                         help="move cap for --self-play (default: 60)")
    args = parser.parse_args()

    if args.depth < 1:
        parser.error("--depth must be >= 1")

    if args.max_moves < 1:
        parser.error("--max-moves must be >= 1")

    if args.self_play:
        self_play(args.depth, args.max_moves)
    else:
        human_color = chess.WHITE if args.color == "white" else chess.BLACK
        try:
            human_vs_bot(args.depth, human_color)
        except (KeyboardInterrupt, EOFError):
            print("\nBye.")
            sys.exit(0)


if __name__ == "__main__":
    main()
