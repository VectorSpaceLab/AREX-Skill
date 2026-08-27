#!/usr/bin/env python3
"""Run a tiny evaluate computation smoke test.

The helper is intentionally small and deterministic. By default it computes the
accuracy metric on four examples. It can also load a named or local module and
accept JSON inputs for modules with standard predictions/references features.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _json_value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError(f"invalid JSON: {error}") from error


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute a tiny evaluate module smoke result.")
    parser.add_argument("--module", default="accuracy", help="module name or local module path accepted by evaluate.load")
    parser.add_argument("--module-type", default=None, help="optional module_type passed to evaluate.load")
    parser.add_argument("--config-name", default=None, help="optional config_name passed to evaluate.load")
    parser.add_argument(
        "--predictions",
        type=_json_value,
        default=[0, 1, 1, 0],
        help="JSON array for standard predictions; default: [0, 1, 1, 0]",
    )
    parser.add_argument(
        "--references",
        type=_json_value,
        default=[0, 1, 0, 1],
        help="JSON array for standard references; default: [0, 1, 0, 1]",
    )
    parser.add_argument(
        "--compute-kwargs",
        type=_json_value,
        default={},
        help="JSON object of extra keyword arguments for compute; default: {}",
    )
    parser.add_argument("--cache-dir", default=None, help="optional cache directory for temporary evaluate files")
    parser.add_argument("--keep-in-memory", action="store_true", help="store temporary data in memory for this smoke run")
    parser.add_argument("--save-json", default=None, help="optional output file for the result JSON")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if not isinstance(args.compute_kwargs, dict):
        print("--compute-kwargs must be a JSON object", file=sys.stderr)
        return 2

    try:
        import evaluate
    except Exception as error:  # pragma: no cover - depends on caller environment
        print(f"failed to import evaluate: {error}", file=sys.stderr)
        return 1

    load_kwargs = {
        "module_type": args.module_type,
        "config_name": args.config_name,
        "cache_dir": args.cache_dir,
        "keep_in_memory": args.keep_in_memory,
    }
    load_kwargs = {key: value for key, value in load_kwargs.items() if value is not None and value is not False}

    try:
        module = evaluate.load(args.module, **load_kwargs)
        result = module.compute(
            predictions=args.predictions,
            references=args.references,
            **args.compute_kwargs,
        )
    except Exception as error:
        print(f"compute smoke failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1

    print(json.dumps(result, sort_keys=True))
    if args.save_json:
        output_path = Path(args.save_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
