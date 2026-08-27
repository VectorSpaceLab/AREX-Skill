#!/usr/bin/env python3
"""Safe LinearRNA import and toy API checker."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any


VALID_BASES = set("ACGU")
VALID_CONSTRAINT_CHARS = set("?.()")
VALID_PAIRS = {"AU", "UA", "CG", "GC", "GU", "UG"}


class CheckError(Exception):
    """Expected checker failure with a stable exit code."""

    def __init__(self, category: str, message: str, code: int) -> None:
        super().__init__(message)
        self.category = category
        self.code = code


def normalize_sequence(sequence: str) -> str:
    normalized = "".join(sequence.split()).upper().replace("T", "U")
    if not normalized:
        raise CheckError("validation", "RNA sequence is empty after whitespace removal.", 2)
    invalid = sorted(set(normalized) - VALID_BASES)
    if invalid:
        raise CheckError(
            "validation",
            "RNA sequence contains unsupported base(s): {}. Use only A, C, G, U, or T-as-U.".format(
                ", ".join(invalid)
            ),
            2,
        )
    return normalized


def validate_beam_size(beam_size: int) -> int:
    if beam_size < 0:
        raise CheckError("validation", "--beam-size must be >= 0; use 0 to disable beam pruning.", 2)
    return beam_size


def validate_bp_cutoff(bp_cutoff: float) -> float:
    if not 0.0 <= bp_cutoff <= 1.0:
        raise CheckError("validation", "--bp-cutoff must be between 0.0 and 1.0.", 2)
    return bp_cutoff


def validate_constraint(sequence: str, constraint: str | None) -> str | None:
    if constraint is None:
        return None
    cleaned = "".join(constraint.split())
    if len(cleaned) != len(sequence):
        raise CheckError(
            "validation",
            "Constraint length {} does not match normalized sequence length {}.".format(
                len(cleaned), len(sequence)
            ),
            2,
        )
    invalid = sorted(set(cleaned) - VALID_CONSTRAINT_CHARS)
    if invalid:
        raise CheckError(
            "validation",
            "Constraint contains unsupported character(s): {}. Use only ?, ., (, ).".format(
                ", ".join(invalid)
            ),
            2,
        )

    stack: list[int] = []
    pairs: list[tuple[int, int]] = []
    for index, char in enumerate(cleaned):
        if char == "(":
            stack.append(index)
        elif char == ")":
            if not stack:
                raise CheckError(
                    "validation",
                    "Constraint has an unmatched ')' at 1-based position {}.".format(index + 1),
                    2,
                )
            left = stack.pop()
            pair = sequence[left] + sequence[index]
            if pair not in VALID_PAIRS:
                raise CheckError(
                    "validation",
                    "Constraint forces non-canonical pair {}-{} ({}) at 1-based positions {} and {}.".format(
                        sequence[left], sequence[index], pair, left + 1, index + 1
                    ),
                    2,
                )
            pairs.append((left + 1, index + 1))
    if stack:
        raise CheckError(
            "validation",
            "Constraint has unmatched '(' at 1-based position(s): {}.".format(
                ", ".join(str(index + 1) for index in stack)
            ),
            2,
        )
    return cleaned


def add_repo_paths(repo_root: str | None) -> list[str]:
    if not repo_root:
        return []
    root = Path(repo_root).expanduser().resolve()
    candidates = [
        root,
        root / "build",
        root / "build" / "pahelix" / "toolkit",
        root / "build" / "c" / "pahelix" / "toolkit" / "linear_rna",
        root / "build" / "c" / "pahelix" / "toolkit" / "linear_rna" / "linear_rna",
    ]
    added: list[str] = []
    for candidate in candidates:
        path = str(candidate)
        if candidate.exists() and path not in sys.path:
            sys.path.insert(0, path)
            added.append(path)
    return added


def import_linear_rna(repo_root: str | None) -> tuple[Any, str, list[str]]:
    added_paths = add_repo_paths(repo_root)
    attempts = [
        "pahelix.toolkit.linear_rna",
        "pahelix.toolkit.linear_rna.linear_rna",
        "c.pahelix.toolkit.linear_rna.linear_rna",
        "linear_rna",
    ]
    errors: dict[str, str] = {}
    for module_name in attempts:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - preserve import diagnostics for users.
            errors[module_name] = "{}: {}".format(type(exc).__name__, exc)
            continue
        missing = [name for name in ("linear_fold_c", "linear_fold_v", "linear_partition_c", "linear_partition_v") if not hasattr(module, name)]
        if missing:
            errors[module_name] = "imported module is missing API(s): {}".format(", ".join(missing))
            continue
        return module, module_name, added_paths

    raise CheckError(
        "import",
        "Could not import a LinearRNA extension with the required APIs. Attempts: {}".format(
            json.dumps(errors, sort_keys=True)
        ),
        3,
    )


def as_jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return [as_jsonable(item) for item in value]
    if isinstance(value, list):
        return [as_jsonable(item) for item in value]
    return value


def run_api(module: Any, args: argparse.Namespace, sequence: str, constraint: str | None) -> dict[str, Any]:
    model_suffix = args.model
    no_sharp_turn = not args.allow_sharp_turn
    if args.partition:
        if constraint is not None:
            raise CheckError("validation", "LinearPartition does not accept --constraint; omit one of them.", 2)
        function_name = "linear_partition_{}".format(model_suffix)
        function = getattr(module, function_name)
        score, pairs = function(
            sequence,
            beam_size=args.beam_size,
            bp_cutoff=args.bp_cutoff,
            no_sharp_turn=no_sharp_turn,
        )
        return {
            "mode": "partition",
            "function": function_name,
            "score": score,
            "pair_count": len(pairs),
            "pairs": as_jsonable(list(pairs)),
        }

    function_name = "linear_fold_{}".format(model_suffix)
    function = getattr(module, function_name)
    structure, score = function(
        sequence,
        beam_size=args.beam_size,
        use_constraints=constraint is not None,
        constraint=constraint or "",
        no_sharp_turn=no_sharp_turn,
    )
    if not structure:
        raise CheckError(
            "api",
            "LinearFold returned an empty structure with score 0; validate constraints or try a less restrictive fold.",
            4,
        )
    if len(structure) != len(sequence):
        raise CheckError(
            "api",
            "LinearFold returned structure length {} for sequence length {}.".format(
                len(structure), len(sequence)
            ),
            4,
        )
    return {
        "mode": "fold",
        "function": function_name,
        "structure": structure,
        "score": score,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate LinearRNA inputs, import the extension, and run a tiny LinearFold or LinearPartition check."
    )
    parser.add_argument("--sequence", required=True, help="RNA sequence; whitespace is removed and T is normalized to U.")
    parser.add_argument("--partition", action="store_true", help="Run LinearPartition instead of LinearFold.")
    parser.add_argument("--constraint", help="LinearFold constraint string using ?, ., (, and ).")
    parser.add_argument("--bp-cutoff", type=float, default=0.0, help="LinearPartition base-pair probability cutoff in [0, 1].")
    parser.add_argument("--repo-root", help="Optional package/build root to add to sys.path before import.")
    parser.add_argument("--beam-size", type=int, default=100, help="Beam size; 0 disables beam pruning.")
    parser.add_argument("--model", choices=("c", "v"), default="c", help="Use c for learned parameters or v for thermodynamic parameters.")
    parser.add_argument("--allow-sharp-turn", action="store_true", help="Pass no_sharp_turn=False to the extension.")
    parser.add_argument("--import-only", action="store_true", help="Validate inputs and import extension without running an API call.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        sequence = normalize_sequence(args.sequence)
        args.beam_size = validate_beam_size(args.beam_size)
        args.bp_cutoff = validate_bp_cutoff(args.bp_cutoff)
        constraint = validate_constraint(sequence, args.constraint)
        if args.partition and constraint is not None:
            raise CheckError("validation", "LinearPartition does not accept --constraint; omit one of them.", 2)
        module, module_name, added_paths = import_linear_rna(args.repo_root)
        result: dict[str, Any] = {
            "ok": True,
            "module": module_name,
            "normalized_sequence": sequence,
            "sequence_length": len(sequence),
            "model": args.model,
            "beam_size": args.beam_size,
            "no_sharp_turn": not args.allow_sharp_turn,
            "added_repo_paths": len(added_paths),
        }
        if constraint is not None:
            result["constraint"] = constraint
        if args.import_only:
            result["mode"] = "import-only"
            result["api_available"] = [
                "linear_fold_c",
                "linear_fold_v",
                "linear_partition_c",
                "linear_partition_v",
            ]
        else:
            result.update(run_api(module, args, sequence, constraint))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except CheckError as exc:
        payload = {"ok": False, "category": exc.category, "error": str(exc)}
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        return exc.code
    except Exception as exc:  # noqa: BLE001 - top-level CLI diagnostic.
        payload = {"ok": False, "category": "unexpected", "error": "{}: {}".format(type(exc).__name__, exc)}
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
