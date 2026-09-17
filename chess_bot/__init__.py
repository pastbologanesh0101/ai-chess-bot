"""AI Chess Bot - a from-scratch minimax/alpha-beta chess engine.

Board representation and move legality are delegated to the `python-chess`
library. Everything that makes this an "AI" -- the search algorithm, move
ordering, and evaluation function -- is implemented in this package.
"""

from .evaluation import evaluate
from .search import ChessEngine, SearchStats, order_moves

__all__ = ["evaluate", "ChessEngine", "SearchStats", "order_moves"]
