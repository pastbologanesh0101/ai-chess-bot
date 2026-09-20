# Changelog

All notable changes to this project are documented in this file.

## [0.1.0] - Initial release

The first working version of the AI Chess Bot engine.

### Added
- `chess_bot/search.py`: minimax search with alpha-beta pruning,
  configurable depth, and MVV-LVA-based move ordering (captures, then
  promotions, then checks, then quiet moves) to make pruning more
  effective.
- `chess_bot/evaluation.py`: a hand-written static evaluation function
  combining material balance, piece-square tables, mobility, a pawn-
  shield king-safety heuristic, and hard terminal scoring for
  checkmate/stalemate/draws.
- `play.py`: a text CLI supporting human-vs-bot games (either color, SAN
  or UCI move input) and a self-play demo mode.
- Board representation and legal move generation delegated to
  `python-chess`, keeping this project's own code scoped to the search
  algorithm and evaluation function.
- 16 unit tests covering material scoring, terminal state detection,
  mate-in-1 search correctness, move-ordering effectiveness (node-count
  comparison under alpha-beta), illegal-move fuzzing across sample
  positions, and depth scaling.
- GitHub Actions CI running the test suite on Python 3.11 and 3.12.
- MIT license and a README documenting the search/evaluation design and
  usage.
