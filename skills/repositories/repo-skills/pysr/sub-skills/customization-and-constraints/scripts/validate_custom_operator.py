#!/usr/bin/env python3
"""Validate a custom PySR operator or loss draft.

This is a static checker. It does not import PySR, start Julia, or run a search.
It accepts either:
  1. a JSON config file / JSON string via --config, or
  2. CLI fields such as --name, --arity, --definition, --sympy-mapping.

Examples
--------
python validate_custom_operator.py \
  --name inv \
  --arity 1 \
  --definition 'inv(x) = 1 / x' \
  --sympy-mapping 'inv=1/x' \
  --domain-notes 'valid on nonzero inputs'

python validate_custom_operator.py --config operator.json
python validate_custom_operator.py --config '{"name":"inv","arity":1,"definition":"inv(x) = 1/x"}'
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

RESERVED_NAMES = {
    "+",
    "-",
    "*",
    "/",
    "^",
    "pow",
    "sin",
    "cos",
    "tan",
    "exp",
    "log",
    "sqrt",
    "inv",
    "square",
    "cube",
    "cbrt",
    "abs",
    "sign",
}

RISKY_DOMAIN_WORDS = (
    "negative",
    "nonnegative",
    "sqrt",
    "log",
    "divide",
    "division",
    "denominator",
    "pole",
    "zero",
    "overflow",
    "underflow",
    "domain",
)

BARE_FLOAT_RE = re.compile(r"(?<![\w.])(?:\d+\.\d*|\d*\.\d+)(?:[eE][+-]?\d+)?(?![fF]\d+)")
SCIENTIFIC_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?[eE][+-]?\d+(?![fF]\d+)")
ARG_LIST_RE = re.compile(r"\(([^)]*)\)")


def _load_jsonish(value: str) -> Any:
    path = Path(value)
    if value != "-" and path.exists():
        return json.loads(path.read_text())
    if value == "-":
        return json.load(sys.stdin)
    return json.loads(value)


def _parse_key_value_items(items: list[str], *, label: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"{label} entries must look like KEY=VALUE, got: {item!r}")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"{label} key cannot be empty: {item!r}")
        result[key] = value
    return result


def _merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if value is not None:
            merged[key] = value
    return merged


def _normalize_mapping(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return {str(k): str(v) for k, v in value.items()}
    if isinstance(value, list):
        normalized: dict[str, str] = {}
        for item in value:
            if isinstance(item, dict):
                if len(item) != 1:
                    raise ValueError("Each sympy mapping object must contain exactly one key")
                key, mapping_value = next(iter(item.items()))
                normalized[str(key)] = str(mapping_value)
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                normalized[str(item[0])] = str(item[1])
            else:
                raise ValueError(
                    "sympy_mapping lists must contain {key: value} objects or [key, value] pairs"
                )
        return normalized
    raise ValueError("sympy_mapping must be a mapping or list of key/value pairs")


def _extract_signature_args(signature: str) -> list[str]:
    signature = signature.strip()
    match = ARG_LIST_RE.search(signature)
    if not match:
        return []
    raw = match.group(1).strip()
    if not raw:
        return []
    return [arg.strip() for arg in raw.split(",") if arg.strip()]


def _looks_like_typed_nan_guard(definition: str) -> bool:
    lowered = definition.lower()
    if "nan" not in lowered:
        return False
    if "convert(typeof" in lowered or "t(nan)" in lowered:
        return True
    if re.search(r"\b[a-z_][a-z0-9_]*\(nan\)", lowered):
        return True
    return False


def _has_bare_float_literals(definition: str) -> bool:
    return bool(BARE_FLOAT_RE.search(definition) or SCIENTIFIC_RE.search(definition))


def _contains_risky_domain_notes(notes: str) -> bool:
    lowered = notes.lower()
    return any(word in lowered for word in RISKY_DOMAIN_WORDS)


def _validate_loss_signature(loss_kind: str, signature: str | None) -> list[str]:
    if not signature:
        return ["No explicit loss signature supplied; only a heuristic check was possible."]

    args = _extract_signature_args(signature)
    if loss_kind == "elementwise":
        if len(args) not in {2, 3}:
            return [
                "elementwise_loss should accept 2 arguments, or 3 when weights are used."
            ]
        return [f"elementwise_loss signature looks plausible with {len(args)} arguments."]

    if loss_kind == "loss_function":
        if len(args) < 3:
            return ["loss_function should look like (tree, dataset, options)."]
        return ["loss_function signature looks plausible."]

    if loss_kind == "loss_function_expression":
        if len(args) < 3:
            return ["loss_function_expression should look like (expression, dataset, options)."]
        return ["loss_function_expression signature looks plausible."]

    return [f"Unknown loss_kind {loss_kind!r}; unable to validate signature."]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Static checklist for a custom PySR operator, mapping, or loss draft.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  validate_custom_operator.py --name inv --arity 1 --definition 'inv(x) = 1/x' \\\n"
            "    --sympy-mapping 'inv=1/x' --domain-notes 'valid on nonzero inputs'\n"
            "  validate_custom_operator.py --config operator.json\n"
            "  validate_custom_operator.py --config '{\"name\":\"inv\",\"arity\":1,\"definition\":\"inv(x) = 1/x\"}'"
        ),
    )
    parser.add_argument("--config", help="JSON file path, inline JSON string, or '-' for stdin JSON.")
    parser.add_argument("--name", help="Operator name.")
    parser.add_argument("--arity", type=int, help="Operator arity.")
    parser.add_argument("--definition", help="Full Julia operator definition string.")
    parser.add_argument(
        "--sympy-mapping",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Static SymPy mapping description. Repeatable.",
    )
    parser.add_argument(
        "--domain-notes",
        help="Short note describing the operator domain or invalid-input behavior.",
    )
    parser.add_argument(
        "--precision",
        type=int,
        choices=(16, 32, 64),
        default=None,
        help="PySR precision to assume when checking float literals.",
    )
    parser.add_argument(
        "--loss-kind",
        choices=("elementwise", "loss_function", "loss_function_expression"),
        help="Optional loss mode to validate alongside the operator draft.",
    )
    parser.add_argument(
        "--loss-signature",
        help="Optional loss signature string or Julia snippet.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures.",
    )
    return parser


def _print_section(title: str, lines: list[tuple[str, str]]) -> None:
    print(title)
    for status, message in lines:
        print(f"  [{status}] {message}")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    config: dict[str, Any] = {}
    if args.config:
        config = _load_jsonish(args.config)
        if not isinstance(config, dict):
            raise SystemExit("--config must decode to a JSON object.")

    override = {
        "name": args.name,
        "arity": args.arity,
        "definition": args.definition,
        "domain_notes": args.domain_notes,
        "precision": args.precision,
        "loss_kind": args.loss_kind,
        "loss_signature": args.loss_signature,
    }
    config = _merge_config(config, override)

    sympy_mapping = _normalize_mapping(config.get("sympy_mapping"))
    cli_mapping = _parse_key_value_items(args.sympy_mapping, label="--sympy-mapping")
    sympy_mapping.update(cli_mapping)
    if sympy_mapping:
        config["sympy_mapping"] = sympy_mapping

    findings: list[tuple[str, str]] = []
    warnings_seen = 0
    failures = 0

    name = str(config.get("name") or "").strip()
    arity = config.get("arity")
    definition = str(config.get("definition") or "").strip()
    domain_notes = str(config.get("domain_notes") or "").strip()
    precision = int(config.get("precision") or 32)
    loss_kind = str(config.get("loss_kind") or "").strip()
    loss_signature = config.get("loss_signature")

    if not name:
        findings.append(("FAIL", "Missing operator name."))
        failures += 1
    elif not re.match(r"^[A-Za-z0-9_]+$", name):
        findings.append(("FAIL", "Operator name must use only letters, numbers, and underscores."))
        failures += 1
    else:
        findings.append(("PASS", f"Operator name looks valid: {name}."))
        if name in RESERVED_NAMES:
            findings.append(("WARN", f"Name {name!r} overlaps a common built-in operator name."))
            warnings_seen += 1

    if arity is None:
        findings.append(("WARN", "No arity supplied; cannot check constructor path."))
        warnings_seen += 1
    else:
        try:
            arity_int = int(arity)
        except (TypeError, ValueError):
            findings.append(("FAIL", f"Arity must be an integer, got {arity!r}."))
            failures += 1
            arity_int = -1
        else:
            if arity_int < 1:
                findings.append(("FAIL", "Arity must be at least 1."))
                failures += 1
            else:
                findings.append(("PASS", f"Arity is {arity_int}."))
                if arity_int > 2:
                    findings.append(
                        ("WARN", "Arity 3+ requires the `operators={arity: [...]}` constructor path."),
                    )
                    warnings_seen += 1
        arity = arity_int

    if not definition:
        findings.append(("FAIL", "Missing operator definition."))
        failures += 1
    else:
        findings.append(("PASS", "Operator definition supplied."))
        if name and name not in definition:
            findings.append(("WARN", "Definition does not obviously mention the operator name."))
            warnings_seen += 1
        if precision == 32 and _has_bare_float_literals(definition):
            findings.append(
                ("WARN", "Bare decimal or scientific literals detected; use Float32-safe forms such as `2.5f0` or `T(2.5)`."),
            )
            warnings_seen += 1
        if _contains_risky_domain_notes(domain_notes) and not _looks_like_typed_nan_guard(definition):
            findings.append(
                ("WARN", "Domain notes look restrictive, but no typed NaN guard was detected in the definition."),
            )
            warnings_seen += 1
        elif _looks_like_typed_nan_guard(definition):
            findings.append(("PASS", "Typed NaN guard detected."))

    if not sympy_mapping:
        findings.append(("FAIL", "Missing SymPy mapping for the custom operator."))
        failures += 1
    else:
        findings.append(("PASS", f"SymPy mapping supplied for: {', '.join(sorted(sympy_mapping))}."))
        if name and name not in sympy_mapping:
            findings.append(("WARN", "SymPy mapping does not use the same key as the operator name."))
            warnings_seen += 1

    if domain_notes:
        findings.append(("PASS", f"Domain notes supplied: {domain_notes}"))
    else:
        findings.append(("WARN", "No domain notes supplied; document invalid-input behavior before use."))
        warnings_seen += 1

    if loss_kind:
        findings.append(("PASS", f"Loss mode noted: {loss_kind}."))
        for item in _validate_loss_signature(loss_kind, loss_signature):
            if item.startswith("Unknown"):
                findings.append(("WARN", item))
                warnings_seen += 1
            elif item.startswith("elementwise_loss should") or item.startswith("loss_function should") or item.startswith("loss_function_expression should"):
                findings.append(("FAIL", item))
                failures += 1
            else:
                findings.append(("PASS", item))
    elif loss_signature:
        findings.append(("WARN", "A loss signature was supplied without a loss mode."))
        warnings_seen += 1

    constraints = config.get("constraints")
    if isinstance(constraints, dict) and name and name in constraints and arity not in (None, -1):
        constraint_value = constraints[name]
        if isinstance(constraint_value, (list, tuple)):
            if len(constraint_value) != arity:
                findings.append(
                    ("FAIL", f"Constraint length {len(constraint_value)} does not match arity {arity}."),
                )
                failures += 1
            else:
                findings.append(("PASS", "Constraint length matches arity."))
        else:
            if int(arity) > 1:
                findings.append(
                    ("WARN", "Scalar constraints are usually reserved for unary operators; check the intended shape."),
                )
                warnings_seen += 1

    _print_section("Checklist", findings)
    print()
    print("Summary")
    print(f"  failures: {failures}")
    print(f"  warnings: {warnings_seen}")

    if failures > 0:
        return 1
    if args.strict and warnings_seen > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
