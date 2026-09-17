# AI Chess Bot

[![tests](https://github.com/pastbologanesh0101/ai-chess-bot/actions/workflows/tests.yml/badge.svg)](https://github.com/pastbologanesh0101/ai-chess-bot/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A small, from-scratch chess **engine** with an AI opponent: minimax search
with alpha-beta pruning and a hand-written evaluation function, playable
from the terminal.

Board representation and legal move generation come from the
[`python-chess`](https://python-chess.readthedocs.io/) library — that part
is standard practice and not worth reinventing. Everything that makes this
an *AI*, namely the **search algorithm** and the **evaluation function**,
is implemented from scratch in [`chess_bot/`](chess_bot/).

This is a chess *engine*, not a two-player game UI — there's no shared
board/GUI project here, just a bot that decides its own moves.

## How it works

### Search: minimax + alpha-beta (`chess_bot/search.py`)

`ChessEngine.choose_move(board, depth)` runs a classic minimax search over
the game tree:

- At each node, White maximizes the evaluation and Black minimizes it.
- **Alpha-beta pruning** cuts off branches that can't affect the final
  decision: once a branch is proven "at least as bad as" an
  already-found alternative for the opponent, the rest of it is skipped.
- Search **depth is configurable** (`--depth N` on the CLI, or the
  `depth=` constructor argument) — depth 2-3 plies is fast, depth 4-5 is
  noticeably stronger and slower.
- **Move ordering** (`order_moves`) tries the most promising moves first —
  captures ranked by MVV-LVA (Most Valuable Victim, Least Valuable
  Attacker), then promotions, then checks, then everything else. Trying
  strong moves first lets alpha-beta prune far more of the tree, since a
  good move found early raises alpha/lowers beta sooner.
  `tests/test_engine.py::test_alpha_beta_with_ordering_visits_fewer_nodes`
  asserts this quantitatively: for the same position and depth, search
  with ordering enabled visits strictly fewer nodes than the same search
  with ordering disabled.
- Checkmate and stalemate are treated as **terminal states**: the search
  stops there and takes the evaluation function's terminal score rather
  than recursing further.

### Evaluation (`chess_bot/evaluation.py`)

`evaluate(board)` is a hand-written static evaluator, always scored from
White's perspective (positive = good for White, negative = good for
Black), combining:

1. **Material balance** — standard centipawn piece values
   (P=100, N=320, B=330, R=500, Q=900).
2. **Piece-square tables** — classic simplified per-square positional
   bonuses for each piece type (e.g. knights are penalized on the rim and
   rewarded in the center; pawns are rewarded for advancing; the king
   gets a "stay safe" table in the middlegame and a "get active" table in
   the endgame). These are plain 64-entry data tables, looked up per
   piece/square/color.
3. **Mobility** — the number of legal moves available to the side to
   move, as a small positional bonus.
4. **King safety** — a basic pawn-shield heuristic: bonus for own pawns
   directly in front of the king, penalty for the king sitting on a file
   with no pawn cover. This term is disabled once the position reaches
   an endgame (few pieces left / queens traded), where king activity
   matters more than shelter.
5. **Terminal detection** — checkmate is scored as a very large
   positive/negative value (dominating every other term), and stalemate
   / insufficient material / other forced draws are scored exactly `0`,
   rather than being blended into the positional terms above.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Play White against the bot (default depth 3):

```bash
python play.py
```

Play Black, and crank up the search depth:

```bash
python play.py --color black --depth 4
```

Watch the bot play a quick demo game against itself (no input needed):

```bash
python play.py --self-play --depth 2
```

Moves are entered in either algebraic notation (`e4`, `Nf3`, `O-O`) or
UCI (`e2e4`). Type `quit` to exit a human game early.

### Example: self-play demo output

```
$ python play.py --self-play --depth 2 --max-moves 6
AI Chess Bot -- self-play demo game (depth=2)

  1. White Nf3      eval=+0.44 nodes=84
  1. Black Nf6      eval=+0.06 nodes=112
  2. White Nc3      eval=+0.48 nodes=112
  2. Black Nc6      eval=-0.18 nodes=93
  3. White e3       eval=+0.42 nodes=232
  ...
```

## Tests

```bash
python -m pytest tests/ -v
```

16 unit tests cover, among other things:

- material-advantage positions scoring correctly for the stronger side,
- minimax finding a crafted mate-in-1 at low depth,
- move ordering quantitatively reducing nodes visited under alpha-beta,
- the engine never returning an illegal move across a handful of fuzzed
  positions,
- checkmate/stalemate terminal detection and scoring,
- increasing search depth completing without crashing or timing out.

All tests run in well under a second and are also run in CI (see
[`.github/workflows/tests.yml`](.github/workflows/tests.yml)) on Python
3.11 and 3.12.

## Project layout

```
ai-chess-bot/
├── chess_bot/
│   ├── evaluation.py   # material + PST + mobility + king safety + terminal states
│   └── search.py       # minimax, alpha-beta pruning, move ordering
├── play.py             # text CLI: human-vs-bot and self-play demo
├── tests/
│   └── test_engine.py  # 16 unit tests
└── .github/workflows/tests.yml
```

## License

MIT — see [LICENSE](LICENSE).
