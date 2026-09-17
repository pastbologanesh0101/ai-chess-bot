"""Minimax search with alpha-beta pruning and capture-first move ordering.

This is the "brain" of the engine: it walks the game tree produced by
`python-chess`'s legal-move generator, scores leaves with
`chess_bot.evaluation.evaluate`, and returns the best move it can find
within a configurable depth.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import chess

from .evaluation import PIECE_VALUES, evaluate

INFINITY = float("inf")


@dataclass
class SearchStats:
    """Bookkeeping returned alongside a search, mainly for testing/tuning."""

    nodes_visited: int = 0

    def reset(self) -> None:
        self.nodes_visited = 0


def _mvv_lva_score(board: chess.Board, move: chess.Move) -> int:
    """Most-Valuable-Victim / Least-Valuable-Attacker capture score."""
    victim_square = move.to_square
    victim = board.piece_at(victim_square)
    if victim is None and board.is_en_passant(move):
        victim_value = PIECE_VALUES[chess.PAWN]
    elif victim is not None:
        victim_value = PIECE_VALUES[victim.piece_type]
    else:
        victim_value = 0

    attacker = board.piece_at(move.from_square)
    attacker_value = PIECE_VALUES[attacker.piece_type] if attacker else 0

    return victim_value * 10 - attacker_value


def order_moves(board: chess.Board, moves: List[chess.Move]) -> List[chess.Move]:
    """Order moves to make alpha-beta pruning more effective.

    Captures are tried first (ranked by MVV-LVA), then promotions, then
    checks, then everything else. Good move ordering lets alpha-beta cut
    off far more branches than searching moves in arbitrary order.
    """

    def key(move: chess.Move) -> Tuple[int, int, int]:
        is_capture = board.is_capture(move)
        capture_score = _mvv_lva_score(board, move) if is_capture else 0
        promotion_score = 800 if move.promotion else 0
        check_score = 50 if board.gives_check(move) else 0
        return (int(is_capture), capture_score + promotion_score + check_score, 0)

    return sorted(moves, key=key, reverse=True)


class ChessEngine:
    """A minimax + alpha-beta search engine with configurable depth."""

    def __init__(self, depth: int = 3, use_move_ordering: bool = True):
        if depth < 1:
            raise ValueError("depth must be >= 1")
        self.depth = depth
        self.use_move_ordering = use_move_ordering
        self.stats = SearchStats()

    def choose_move(
        self, board: chess.Board, depth: Optional[int] = None
    ) -> Tuple[Optional[chess.Move], int]:
        """Return `(best_move, score)` for `board` from the side to move.

        `best_move` is always a legal move in `board` (or `None` if the
        game is already over). `score` is the White-perspective evaluation
        of the resulting position, per `chess_bot.evaluation.evaluate`.
        """
        search_depth = depth if depth is not None else self.depth
        self.stats.reset()

        maximizing = board.turn == chess.WHITE
        score, best_move = self._minimax(
            board, search_depth, -INFINITY, INFINITY, maximizing
        )

        if best_move is None:
            legal = list(board.legal_moves)
            best_move = legal[0] if legal else None
            if best_move is None:
                score = evaluate(board)

        return best_move, score

    def _minimax(
        self,
        board: chess.Board,
        depth: int,
        alpha: float,
        beta: float,
        maximizing: bool,
    ) -> Tuple[float, Optional[chess.Move]]:
        self.stats.nodes_visited += 1

        if depth == 0 or board.is_game_over():
            return evaluate(board), None

        moves = list(board.legal_moves)
        if self.use_move_ordering:
            moves = order_moves(board, moves)

        best_move: Optional[chess.Move] = None

        if maximizing:
            value = -INFINITY
            for move in moves:
                board.push(move)
                score, _ = self._minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                if score > value:
                    value = score
                    best_move = move
                alpha = max(alpha, value)
                if alpha >= beta:
                    break  # beta cutoff
            return value, best_move
        else:
            value = INFINITY
            for move in moves:
                board.push(move)
                score, _ = self._minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                if score < value:
                    value = score
                    best_move = move
                beta = min(beta, value)
                if alpha >= beta:
                    break  # alpha cutoff
            return value, best_move


def perft_nodes(board: chess.Board, depth: int, use_move_ordering: bool) -> int:
    """Run a full-width minimax (no move chosen, just node count) for testing.

    Used to demonstrate that move ordering reduces the number of nodes
    alpha-beta needs to visit versus searching moves in arbitrary order.
    """
    engine = ChessEngine(depth=depth, use_move_ordering=use_move_ordering)
    engine.choose_move(board.copy(), depth=depth)
    return engine.stats.nodes_visited
