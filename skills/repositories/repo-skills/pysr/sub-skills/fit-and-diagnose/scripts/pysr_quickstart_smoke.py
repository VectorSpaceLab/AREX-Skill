#!/usr/bin/env python3
"""Small, safe PySR quickstart smoke helper.

Default mode is dry-run/help-oriented and does not import PySR. Supply
``--run-fit`` to import PySR and run a tiny bounded fit.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run or execute a tiny PySR fit that exercises fit, equations_, "
            "predict, sympy, and latex. PySR is imported only with --run-fit."
        )
    )
    parser.add_argument(
        "--run-fit",
        action="store_true",
        help="Import PySR and run the tiny bounded smoke fit. Default is dry-run only.",
    )
    parser.add_argument(
        "--niterations",
        type=int,
        default=1,
        help="Outer PySR iterations for the smoke fit. Keep small for validation. Default: 1.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=20.0,
        help="Wall-clock timeout passed to PySRRegressor. Default: 20 seconds.",
    )
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=None,
        help=(
            "Optional directory for PySR output files. If omitted, the smoke run uses "
            "temporary equation files where possible."
        ),
    )
    return parser


def dry_run_summary(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "mode": "dry-run",
        "will_import_pysr": False,
        "run_fit": False,
        "niterations": args.niterations,
        "timeout_seconds": args.timeout_seconds,
        "output_directory": str(args.output_directory) if args.output_directory else None,
        "next_step": "Re-run with --run-fit to execute the tiny bounded PySR smoke fit.",
    }


def run_fit(args: argparse.Namespace) -> dict[str, Any]:
    if args.niterations <= 0:
        raise ValueError("--niterations must be positive")
    if args.timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be positive")

    # PySR and NumPy are intentionally imported only in execution mode.
    import numpy as np
    from pysr import PySRRegressor

    rng = np.random.default_rng(0)
    X = rng.normal(size=(48, 2)).astype("float32")
    y = X[:, 0].astype("float32")

    output_directory = args.output_directory
    if output_directory is not None:
        output_directory.mkdir(parents=True, exist_ok=True)

    model = PySRRegressor(
        binary_operators=["+", "-", "*"],
        unary_operators=[],
        niterations=args.niterations,
        populations=4,
        population_size=20,
        ncycles_per_iteration=10,
        tournament_selection_n=8,
        maxsize=7,
        model_selection="best",
        early_stop_condition="stop_if(loss, complexity) = loss < 1e-8 && complexity == 1",
        timeout_in_seconds=args.timeout_seconds,
        parallelism="serial",
        deterministic=True,
        random_state=0,
        progress=False,
        verbosity=0,
        input_stream="devnull",
        temp_equation_file=output_directory is None,
        output_directory=str(output_directory) if output_directory is not None else None,
        run_id="pysr_quickstart_smoke" if output_directory is not None else None,
    )
    model.fit(X, y, variable_names=["signal", "distractor"])

    equations = model.equations_
    if equations is None or len(equations) == 0:
        raise RuntimeError("PySR fit completed without any equations_")

    y_pred = model.predict(X[:5])
    if not np.all(np.isfinite(y_pred)):
        raise RuntimeError("PySR predict returned non-finite values")

    best = model.get_best()
    summary = {
        "mode": "fit",
        "will_import_pysr": True,
        "run_fit": True,
        "niterations": args.niterations,
        "timeout_seconds": args.timeout_seconds,
        "n_equations": int(len(equations)),
        "best_equation": str(best.get("equation", "")),
        "best_loss": float(best.get("loss", float("nan"))),
        "prediction_preview": [float(v) for v in np.asarray(y_pred).reshape(-1)[:5]],
        "sympy": str(model.sympy()),
        "latex": str(model.latex()),
        "output_directory": str(output_directory) if output_directory is not None else None,
    }
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        summary = run_fit(args) if args.run_fit else dry_run_summary(args)
    except Exception as exc:  # pragma: no cover - used as command-line guard
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, sort_keys=True), file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, **summary}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
