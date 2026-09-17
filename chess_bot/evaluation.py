"""Hand-written static evaluation function for the AI Chess Bot engine.

The evaluation is a linear combination of five terms, all computed
directly from a `chess.Board` (from python-chess, used purely for board
representation / move legality -- none of the scoring logic below comes
from that library):

1. Material balance      -- standard piece values.
2. Piece-square tables    -- classic simplified positional bonuses per
                              piece type and square.
3. Mobility               -- number of legal moves available to the side
                              to move.
4. King safety            -- a basic pawn-shield heuristic.
5. Terminal detection      -- checkmate / stalemate / draw are scored as
                              hard terminal values rather than blended in.

The score is always returned from White's point of view: positive means
White is better, negative means Black is better, 0 is roughly balanced.
"""

import chess

# ---------------------------------------------------------------------------
# 1. Material values (centipawns). The king is excluded from material sums
#    since checkmate is handled separately as a terminal state.
# ---------------------------------------------------------------------------
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# ---------------------------------------------------------------------------
# 2. Piece-square tables.
#
# Each table has 64 entries indexed the same way as `chess.SQUARES`, i.e.
# index 0 = a1, index 7 = h1, index 8 = a2, ... index 63 = h8 (files a->h
# within a rank, ranks 1->8 bottom to top). That means the tables below are
# written for White sitting at the bottom of the board, rank 1 first.
#
# For Black, we look up the same table but at the vertically mirrored
# square (`chess.square_mirror`), which reuses the same "advance toward the
# far side" shape without needing a second, hand-mirrored table.
# ---------------------------------------------------------------------------

PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, -20, -20, 10, 10,  5,
    5, -5, -10,  0,  0, -10, -5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5,  5, 10, 25, 25, 10,  5,  5,
   10, 10, 20, 30, 30, 20, 10, 10,
   50, 50, 50, 50, 50, 50, 50, 50,
    0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -40, -20,   0,   5,   5,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]

BISHOP_TABLE = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,  10,  10,   5,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]

ROOK_TABLE = [
     0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

QUEEN_TABLE = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10,   0,   0,  0,  0,   0,   0, -10,
    -10,   0,   5,  5,  5,   5,   0, -10,
     -5,   0,   5,  5,  5,   5,   0,  -5,
      0,   0,   5,  5,  5,   5,   0,  -5,
    -10,   5,   5,  5,  5,   5,   0, -10,
    -10,   0,   5,  0,  0,   0,   0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20,
]

KING_TABLE_MIDDLEGAME = [
    20,  30,  10,   0,   0,  10,  30,  20,
    20,  20,   0,   0,   0,   0,  20,  20,
   -10, -20, -20, -20, -20, -20, -20, -10,
   -20, -30, -30, -40, -40, -30, -30, -20,
   -30, -40, -40, -50, -50, -40, -40, -30,
   -30, -40, -40, -50, -50, -40, -40, -30,
   -30, -40, -40, -50, -50, -40, -40, -30,
   -30, -40, -40, -50, -50, -40, -40, -30,
]

KING_TABLE_ENDGAME = [
    -50, -30, -30, -30, -30, -30, -30, -50,
    -30, -30,   0,   0,   0,   0, -30, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  30,  40,  40,  30, -10, -30,
    -30, -10,  20,  30,  30,  20, -10, -30,
    -30, -20, -10,   0,   0, -10, -20, -30,
    -50, -40, -30, -20, -20, -30, -40, -50,
]

PIECE_SQUARE_TABLES = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
}

# Weight applied to mobility (per legal move available to the side to move).
MOBILITY_WEIGHT = 2

# Weight applied to the king-safety pawn-shield heuristic.
KING_SAFETY_WEIGHT = 1

# Score used for a "White has been checkmated" / "Black has been
# checkmated" terminal position. Large enough to dominate any positional
# term.
MATE_SCORE = 1_000_000


def _is_endgame(board: chess.Board) -> bool:
    """Very small heuristic: endgame once queens are off, or material is low."""
    queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(
        board.pieces(chess.QUEEN, chess.BLACK)
    )
    minor_or_major = 0
    for piece_type in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
        minor_or_major += len(board.pieces(piece_type, chess.WHITE))
        minor_or_major += len(board.pieces(piece_type, chess.BLACK))
    return queens == 0 or minor_or_major <= 6


def _piece_square_value(piece: chess.Piece, square: int, endgame: bool) -> int:
    if piece.piece_type == chess.KING:
        table = KING_TABLE_ENDGAME if endgame else KING_TABLE_MIDDLEGAME
    else:
        table = PIECE_SQUARE_TABLES[piece.piece_type]
    idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
    return table[idx]


def _material_and_pst(board: chess.Board) -> int:
    endgame = _is_endgame(board)
    total = 0
    for square, piece in board.piece_map().items():
        sign = 1 if piece.color == chess.WHITE else -1
        value = PIECE_VALUES[piece.piece_type]
        value += _piece_square_value(piece, square, endgame)
        total += sign * value
    return total


def _mobility(board: chess.Board) -> int:
    """Legal moves available to the side to move, signed for White.

    Only the side to move is counted (rather than also probing the
    opponent's mobility via a null move), which keeps this cheap and avoids
    null-move edge cases while still rewarding active positions.
    """
    n_moves = board.legal_moves.count()
    return n_moves * MOBILITY_WEIGHT if board.turn == chess.WHITE else -n_moves * MOBILITY_WEIGHT


def _king_safety_for(board: chess.Board, color: bool) -> int:
    """Basic pawn-shield heuristic: bonus for own pawns in front of the king."""
    king_square = board.king(color)
    if king_square is None:
        return 0
    file = chess.square_file(king_square)
    rank = chess.square_rank(king_square)
    forward = 1 if color == chess.WHITE else -1

    shield = 0
    for df in (-1, 0, 1):
        f = file + df
        r = rank + forward
        if 0 <= f <= 7 and 0 <= r <= 7:
            square = chess.square(f, r)
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.PAWN and piece.color == color:
                shield += 1

    open_file_penalty = 0
    own_pawns_on_file = any(
        chess.square_file(sq) == file for sq in board.pieces(chess.PAWN, color)
    )
    if not own_pawns_on_file:
        open_file_penalty = 2  # king on a (semi-)open file is riskier

    return shield * 10 - open_file_penalty * 5


def _king_safety(board: chess.Board) -> int:
    if _is_endgame(board):
        return 0  # king safety matters much less once the board empties out
    return _king_safety_for(board, chess.WHITE) - _king_safety_for(board, chess.BLACK)


def evaluate(board: chess.Board) -> int:
    """Static evaluation of `board`, from White's perspective.

    Positive = good for White, negative = good for Black. Checkmate,
    stalemate, and other drawn terminal states are detected first and
    scored as hard terminal values rather than blended with the
    positional terms.
    """
    if board.is_checkmate():
        # The side to move has been checkmated, i.e. it lost.
        return -MATE_SCORE if board.turn == chess.WHITE else MATE_SCORE

    if (
        board.is_stalemate()
        or board.is_insufficient_material()
        or board.is_seventyfive_moves()
        or board.is_fivefold_repetition()
    ):
        return 0

    score = 0
    score += _material_and_pst(board)
    score += _mobility(board)
    score += _king_safety(board)
    return score
