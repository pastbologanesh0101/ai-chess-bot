"""Unit tests for the AI Chess Bot engine (evaluation + search).

Run with:
    python -m pytest tests/ -v
or:
    python -m unittest discover -s tests -v

Search depths are kept low (1-3 ply) throughout so the whole suite runs in
well under a minute.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import chess

from chess_bot.evaluation import MATE_SCORE, evaluate
from chess_bot.search import ChessEngine, order_moves

# A hand-crafted back-rank mate-in-1: 1. Ra8# is forced checkmate.
BACK_RANK_MATE_IN_ONE_FEN = "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1"

# Classic stalemate: Black to move, no legal moves, not in check.
STALEMATE_FEN = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"

# A handful of varied "real" positions to fuzz-test legality across.
SAMPLE_FENS = [
    chess.STARTING_FEN,
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
    "rnbqkb1r/pp1ppppp/5n2/2p5/4P3/2N5/PPPP1PPP/R1BQKBNR w KQkq c6 0 3",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 2",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2",
]


class EvaluationMaterialTests(unittest.TestCase):
    def test_white_material_advantage_scores_higher(self):
        # White has an extra queen compared to Black; otherwise equal.
        base = chess.Board(
            "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        )  # black has no queen
        score = evaluate(base)
        self.assertGreater(score, 500, "extra queen should be worth well over 500cp")

    def test_black_material_advantage_scores_lower(self):
        # Black has an extra queen compared to White; otherwise equal.
        base = chess.Board(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNB1KBNR w KQkq - 0 1"
        )  # white has no queen
        score = evaluate(base)
        self.assertLess(score, -500, "being down a queen should score well under -500cp")

    def test_starting_position_is_roughly_balanced(self):
        score = evaluate(chess.Board())
        self.assertLess(abs(score), 50, "symmetric starting position should be ~0")

    def test_clearly_winning_material_position_favors_correct_side(self):
        # White has queen + rook extra.
        board = chess.Board("4k3/8/8/8/8/8/8/R2QK3 w - - 0 1")
        white_up = evaluate(board)
        board2 = chess.Board("r2qk3/8/8/8/8/8/8/4K3 w - - 0 1")
        black_up = evaluate(board2)
        self.assertGreater(white_up, 1000)
        self.assertLess(black_up, -1000)


class TerminalStateTests(unittest.TestCase):
    def test_checkmate_against_white_scores_extreme_negative(self):
        # Fool's-mate-style position: White has just been checkmated (White to move, mated).
        board = chess.Board(
            "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
        )
        self.assertTrue(board.is_checkmate())
        self.assertEqual(evaluate(board), -MATE_SCORE)

    def test_checkmate_against_black_scores_extreme_positive(self):
        board = chess.Board(BACK_RANK_MATE_IN_ONE_FEN)
        board.push_san("Ra8#")
        self.assertTrue(board.is_checkmate())
        self.assertEqual(evaluate(board), MATE_SCORE)

    def test_stalemate_scores_zero(self):
        board = chess.Board(STALEMATE_FEN)
        self.assertTrue(board.is_stalemate())
        self.assertEqual(evaluate(board), 0)


class SearchCorrectnessTests(unittest.TestCase):
    def test_minimax_finds_mate_in_one(self):
        board = chess.Board(BACK_RANK_MATE_IN_ONE_FEN)
        engine = ChessEngine(depth=2)
        move, score = engine.choose_move(board)
        self.assertEqual(board.san(move), "Ra8#")
        self.assertEqual(score, MATE_SCORE)

        board.push(move)
        self.assertTrue(board.is_checkmate())

    def test_engine_never_returns_illegal_move(self):
        for fen in SAMPLE_FENS:
            for depth in (1, 2):
                board = chess.Board(fen)
                engine = ChessEngine(depth=depth)
                move, _ = engine.choose_move(board)
                self.assertIsNotNone(move, f"engine returned no move for {fen}")
                self.assertIn(
                    move,
                    board.legal_moves,
                    f"illegal move {move} chosen for fen={fen} depth={depth}",
                )

    def test_engine_detects_game_over_and_returns_none(self):
        board = chess.Board(STALEMATE_FEN)
        engine = ChessEngine(depth=2)
        move, score = engine.choose_move(board)
        self.assertIsNone(move)
        self.assertEqual(score, 0)

    def test_increasing_depth_does_not_crash(self):
        board = chess.Board()
        for depth in (1, 2, 3):
            engine = ChessEngine(depth=depth)
            move, score = engine.choose_move(board)
            self.assertIn(move, board.legal_moves)
            self.assertIsInstance(score, (int, float))

    def test_invalid_depth_rejected(self):
        with self.assertRaises(ValueError):
            ChessEngine(depth=0)


class MoveOrderingTests(unittest.TestCase):
    def test_captures_are_ordered_first(self):
        # Position where White can capture a hanging knight on d5.
        board = chess.Board(
            "rnbqkbnr/ppp2ppp/8/3np3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 4"
        )
        moves = list(board.legal_moves)
        ordered = order_moves(board, moves)
        first_move = ordered[0]
        self.assertTrue(
            board.is_capture(first_move),
            f"expected a capture first, got {first_move}",
        )

    def test_alpha_beta_with_ordering_visits_fewer_nodes(self):
        board = chess.Board(
            "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
        )
        depth = 3

        ordered_engine = ChessEngine(depth=depth, use_move_ordering=True)
        ordered_engine.choose_move(board.copy())
        nodes_ordered = ordered_engine.stats.nodes_visited

        unordered_engine = ChessEngine(depth=depth, use_move_ordering=False)
        unordered_engine.choose_move(board.copy())
        nodes_unordered = unordered_engine.stats.nodes_visited

        self.assertLess(
            nodes_ordered,
            nodes_unordered,
            f"move ordering should reduce nodes visited "
            f"(ordered={nodes_ordered}, unordered={nodes_unordered})",
        )


class MiscHeuristicTests(unittest.TestCase):
    def test_knight_centralization_scores_higher_than_corner(self):
        # Extra pawn included so the position isn't flagged as drawn/
        # insufficient material (a lone knight can't force mate).
        center = chess.Board("4k3/8/8/3N4/8/8/7P/4K3 w - - 0 1")
        corner = chess.Board("4k3/8/8/8/8/8/7P/N3K3 w - - 0 1")
        self.assertGreater(evaluate(center), evaluate(corner))

    def test_self_play_runs_a_few_plies_without_error(self):
        board = chess.Board()
        engine = ChessEngine(depth=2)
        for _ in range(6):
            if board.is_game_over():
                break
            move, _ = engine.choose_move(board)
            self.assertIn(move, board.legal_moves)
            board.push(move)
        self.assertGreaterEqual(board.fullmove_number, 1)


if __name__ == "__main__":
    unittest.main()
