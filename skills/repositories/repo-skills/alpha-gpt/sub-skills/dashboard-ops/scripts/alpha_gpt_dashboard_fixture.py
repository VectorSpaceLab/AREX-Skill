#!/usr/bin/env python3
"""Generate deterministic local fixture files for the AlphaGPT dashboard.

The fixture writes only local files in a user-selected output directory:
portfolio_state.json, best_meme_strategy.json, and strategy.log. It never opens
a database connection, imports Solana clients, contacts RPC endpoints, or uses
network access.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from textwrap import dedent

PORTFOLIO_STATE = {
    "FixtureToken111111111111111111111111111111111": {
        "token_address": "FixtureToken111111111111111111111111111111111",
        "symbol": "DOGGO",
        "entry_price": 0.00000120,
        "entry_time": 1730000000.0,
        "amount_held": 1_250_000.0,
        "initial_cost_sol": 1.50,
        "highest_price": 0.00000180,
        "is_moonbag": False,
    },
    "FixtureToken222222222222222222222222222222222": {
        "token_address": "FixtureToken222222222222222222222222222222222",
        "symbol": "CATMOON",
        "entry_price": 0.00000400,
        "entry_time": 1730003600.0,
        "amount_held": 300_000.0,
        "initial_cost_sol": 2.00,
        "highest_price": 0.00000320,
        "is_moonbag": True,
    },
}

# The training engine writes a bare JSON list, while the live runner also accepts
# an object with a formula field. Use the object form so humans can read fixture
# provenance; the dashboard only displays this JSON as metric help text.
BEST_MEME_STRATEGY = {
    "formula": [0, 6, 7],
    "score": 1.2345,
    "note": "deterministic dashboard fixture; not a trained trading strategy",
}

STRATEGY_LOG_LINES = [
    "2025-01-01 00:00:00.000 | INFO     | fixture | Dashboard fixture initialized\n",
    "2025-01-01 00:00:01.000 | INFO     | fixture | Loaded 2 sample positions\n",
    "2025-01-01 00:00:02.000 | WARNING  | fixture | Market DB not contacted by this fixture\n",
    "2025-01-01 00:00:03.000 | INFO     | fixture | STOP_SIGNAL not created automatically\n",
]

TARGETS = {
    "portfolio_state.json": PORTFOLIO_STATE,
    "best_meme_strategy.json": BEST_MEME_STRATEGY,
    "strategy.log": STRATEGY_LOG_LINES,
}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Write safe sample AlphaGPT dashboard state files into an output "
            "directory. No DB, RPC, Solana, or network access is performed."
        )
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help=(
            "Directory that should receive portfolio_state.json, "
            "best_meme_strategy.json, and strategy.log. Use the same directory "
            "as the dashboard process working directory when fixture-testing."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing target files. Without this flag, existing files are preserved.",
    )
    return parser.parse_args(argv)


def fail_if_existing(output_dir: Path, overwrite: bool) -> None:
    existing = [name for name in TARGETS if (output_dir / name).exists()]
    if existing and not overwrite:
        names = ", ".join(existing)
        raise FileExistsError(
            f"Refusing to overwrite existing fixture target(s): {names}. "
            "Re-run with --overwrite if replacement is intended."
        )


def write_fixture(output_dir: Path, overwrite: bool) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fail_if_existing(output_dir, overwrite)

    written: list[Path] = []
    for name, payload in TARGETS.items():
        path = output_dir / name
        if name.endswith(".json"):
            path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        else:
            path.write_text("".join(payload), encoding="utf-8")
        written.append(path)
    return written


def print_next_steps(output_dir: Path, written: list[Path]) -> None:
    rel_names = ", ".join(path.name for path in written)
    message = f"""
    Wrote AlphaGPT dashboard fixture files to: {output_dir}
    Files: {rel_names}

    Next steps:
      1. Launch the dashboard from the same working directory if you want it to
         read these local files: streamlit run dashboard/app.py
      2. Keep in mind that the live dashboard can still attempt read-only DB and
         RPC reads for the market scanner and wallet balance.
      3. The fixture does not create STOP_SIGNAL. Pressing the dashboard
         EMERGENCY STOP button writes STOP_SIGNAL with contents STOP.
    """
    print(dedent(message).strip())


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    output_dir = Path(args.output_dir).expanduser().resolve()
    try:
        written = write_fixture(output_dir, args.overwrite)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print_next_steps(output_dir, written)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
