# Contributing

Thanks for your interest in improving the AI Chess Bot engine. This is a
from-scratch minimax/alpha-beta engine (board representation and legal
move generation come from `python-chess`; the search and evaluation are
implemented here), so contributions that touch `chess_bot/search.py` or
`chess_bot/evaluation.py` should be backed by tests that demonstrate
correctness, not just "it looks stronger."

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
```

## Running the tests

```bash
python -m pytest tests/ -v
```

The suite runs in well under a minute (search depths in tests are kept
to 1-3 ply on purpose). All tests must pass before a change is merged;
CI runs the same command on every push and pull request.

## Code style

- Type hints on function signatures, matching the existing style in
  `chess_bot/`.
- Keep the search algorithm (`search.py`) and the evaluation function
  (`evaluation.py`) cleanly separated — search should never need to know
  *why* a position scored the way it did, only the resulting number.
- New evaluation heuristics should come with a test that isolates the
  heuristic (see `MiscHeuristicTests` in `tests/test_engine.py` for the
  pattern: construct two positions that differ only in the property
  you're testing, and assert the score moves in the right direction).
- No hard-coded "opening book" moves — this project's whole point is
  search + evaluation, not memorized lines.

## Submitting changes

1. Fork the repo and create a branch for your change.
2. Add or update tests for any behavior change, including edge cases
   (forced moves, stalemate/checkmate positions, depth boundaries).
3. Run the full test suite locally and make sure it's green.
4. Open a pull request describing what changed and why, including any
   before/after node-count or evaluation numbers if the change affects
   search performance.
