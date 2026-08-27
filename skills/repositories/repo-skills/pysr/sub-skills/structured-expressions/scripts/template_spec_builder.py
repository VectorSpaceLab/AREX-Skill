#!/usr/bin/env python3
"""Validate a PySR TemplateExpressionSpec construction plan.

This helper is intentionally search-free:

- it parses template plans from CLI flags or JSON
- it prints a normalized construction plan
- it validates basic shape/indexing rules
- it can optionally check the constructor with PySR if requested

It never fits a model and never launches a search.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TemplatePlan:
    combine: str
    expressions: list[str]
    variable_names: list[str]
    parameters: dict[str, int] = field(default_factory=dict)
    guesses: Any = None
    vector_valued: bool = False
    category_column: str | None = None
    zero_based_categories: bool = False
    notes: list[str] = field(default_factory=list)


def _parse_json_text(text: str, source: str) -> dict[str, Any]:
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{source} is not valid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise ValueError(f"{source} must decode to a JSON object")
    return obj


def _load_json_file(path: Path) -> dict[str, Any]:
    return _parse_json_text(path.read_text(encoding="utf-8"), str(path))


def _parse_kv_pairs(items: list[str] | None, *, source: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"{source} entries must use NAME=VALUE form: {item!r}")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"{source} entry has an empty name: {item!r}")
        result[key] = value
    return result


def _coerce_positive_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive integer, not a boolean")
    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and value.strip().isdigit():
        number = int(value.strip())
    else:
        raise ValueError(f"{label} must be a positive integer")
    if number <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return number


def _normalize_sequence(value: Any, *, label: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list of strings")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{label} entries must be non-empty strings")
        items.append(item)
    return items


def _normalize_guesses(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return [value]
    if not isinstance(value, list):
        raise ValueError(
            "guesses must be a dict, a list of dicts, or a nested list of dicts"
        )
    return value


def _build_plan(args: argparse.Namespace) -> TemplatePlan:
    payload: dict[str, Any] = {}

    if args.json_file is not None:
        payload.update(_load_json_file(args.json_file))
    if args.plan_json is not None:
        payload.update(_parse_json_text(args.plan_json, "--json"))

    if args.combine is not None:
        payload["combine"] = args.combine
    if args.expressions:
        payload["expressions"] = list(args.expressions)
    if args.variable_names:
        payload["variable_names"] = list(args.variable_names)
    if args.parameter:
        payload["parameters"] = _parse_kv_pairs(args.parameter, source="--parameter")
    if args.guess:
        payload["guesses"] = [
            _parse_kv_pairs(args.guess, source="--guess")
        ]
    if args.vector_valued:
        payload["vector_valued"] = True
    if args.category_column is not None:
        payload["category_column"] = args.category_column
    if args.zero_based_categories:
        payload["zero_based_categories"] = True
    if args.note:
        payload.setdefault("notes", [])
        payload["notes"].extend(args.note)

    combine = payload.get("combine")
    if not isinstance(combine, str) or not combine.strip():
        raise ValueError("combine must be a non-empty string")

    expressions = _normalize_sequence(payload.get("expressions"), label="expressions")
    variable_names = _normalize_sequence(
        payload.get("variable_names"), label="variable_names"
    )
    if not expressions:
        raise ValueError("expressions must contain at least one placeholder")
    if not variable_names:
        raise ValueError("variable_names must contain at least one variable name")

    parameters_raw = payload.get("parameters") or {}
    if not isinstance(parameters_raw, dict):
        raise ValueError("parameters must be a JSON object or NAME=VALUE pairs")
    parameters: dict[str, int] = {}
    for key, value in parameters_raw.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("parameters keys must be non-empty strings")
        parameters[key] = _coerce_positive_int(value, label=f"parameters['{key}']")

    guesses = _normalize_guesses(payload.get("guesses"))

    notes = _normalize_sequence(payload.get("notes"), label="notes")
    category_column = payload.get("category_column")
    if category_column is not None and (not isinstance(category_column, str) or not category_column.strip()):
        raise ValueError("category_column must be a non-empty string")

    zero_based_categories = bool(payload.get("zero_based_categories", False))
    vector_valued = bool(payload.get("vector_valued", False))

    return TemplatePlan(
        combine=combine,
        expressions=expressions,
        variable_names=variable_names,
        parameters=parameters,
        guesses=guesses,
        vector_valued=vector_valued,
        category_column=category_column,
        zero_based_categories=zero_based_categories,
        notes=notes,
    )


def _validate_plan(plan: TemplatePlan) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if len(set(plan.expressions)) != len(plan.expressions):
        warnings.append("expressions contains duplicate placeholder names")
    if len(set(plan.variable_names)) != len(plan.variable_names):
        warnings.append("variable_names contains duplicate entries")

    overlap = sorted(set(plan.expressions) & set(plan.variable_names))
    if overlap:
        warnings.append(
            "expressions and variable_names overlap: " + ", ".join(overlap)
        )

    for name, size in plan.parameters.items():
        if name in plan.expressions:
            warnings.append(
                f"parameter name {name!r} also appears in expressions; keep them distinct"
            )
        if size <= 0:
            errors.append(f"parameter {name!r} must have a positive length")

    if isinstance(plan.guesses, list):
        if len(plan.guesses) == 0:
            warnings.append("guesses is an empty list; the search will start without seeds")
        for idx, item in enumerate(plan.guesses):
            if isinstance(item, dict):
                for key, value in item.items():
                    if key not in plan.expressions:
                        warnings.append(
                            f"guess {idx} uses placeholder {key!r}, which is not listed in expressions"
                        )
                    if not isinstance(value, str) or not value.strip():
                        errors.append(
                            f"guess {idx} placeholder {key!r} must map to a non-empty string"
                        )
            elif isinstance(item, list):
                if not item:
                    warnings.append(f"guess list {idx} is empty")
                for jdx, inner in enumerate(item):
                    if not isinstance(inner, dict):
                        errors.append(
                            "template guesses must be dicts or lists of dicts"
                        )
                        continue
                    for key, value in inner.items():
                        if key not in plan.expressions:
                            warnings.append(
                                f"guess {idx}[{jdx}] uses placeholder {key!r}, which is not listed in expressions"
                            )
                        if not isinstance(value, str) or not value.strip():
                            errors.append(
                                f"guess {idx}[{jdx}] placeholder {key!r} must map to a non-empty string"
                            )
            else:
                errors.append(
                    "template guesses must be a dict, a list of dicts, or a nested list of dicts"
                )
                break
    elif plan.guesses is not None:
        errors.append(
            "template guesses must be a dict, a list of dicts, or a nested list of dicts"
        )

    if plan.zero_based_categories and plan.category_column is None:
        warnings.append(
            "zero_based_categories is set, but category_column is missing"
        )
    if plan.category_column is not None:
        warnings.append(
            "category_column uses Julia-side 1-based indexing inside the template"
        )
    if plan.vector_valued:
        warnings.append(
            "vector_valued templates should usually move the extra targets into X and use a dummy y"
        )

    if "D(" in plan.combine:
        warnings.append("combine uses D(...); confirm the argument index is correct")
    if "[" in plan.combine and plan.parameters:
        warnings.append(
            "combine contains bracket indexing; confirm the parameter vectors are declared with the right lengths"
        )

    return errors, warnings


def _constructor_preview(plan: TemplatePlan) -> str:
    lines = ["TemplateExpressionSpec("]
    lines.append(f"    combine={plan.combine!r},")
    lines.append(f"    expressions={plan.expressions!r},")
    lines.append(f"    variable_names={plan.variable_names!r},")
    if plan.parameters:
        lines.append(f"    parameters={plan.parameters!r},")
    lines.append(")")
    return "\n".join(lines)


def _guess_preview(plan: TemplatePlan) -> str | None:
    if plan.guesses is None:
        return None
    return json.dumps(plan.guesses, indent=2, sort_keys=True)


def _recommendations(plan: TemplatePlan) -> list[str]:
    recs: list[str] = []
    if plan.category_column is not None:
        recs.append("Shift zero-based category labels by +1 before fit.")
    if plan.vector_valued:
        recs.append(
            "Use dummy y and an elementwise loss that returns the template residual."
        )
    if "D(" in plan.combine:
        recs.append("`D(f, i)` counts arguments from 1, not 0.")
    if plan.guesses is not None:
        recs.append("Template guesses should map placeholder names to `#1`, `#2`, ... argument slots.")
    if plan.parameters:
        recs.append("Parameter vectors are 1-based inside the Julia template body.")
    recs.append(
        "Template expressions do not expose sympy/latex/jax/pytorch export methods."
    )
    return recs


def _try_constructor_check(plan: TemplatePlan, enabled: bool) -> dict[str, Any] | None:
    if not enabled:
        return None

    try:
        from pysr import TemplateExpressionSpec
    except Exception as exc:  # pragma: no cover - environment dependent
        return {
            "status": "skipped",
            "reason": f"PySR import unavailable: {exc}",
        }

    try:
        spec = TemplateExpressionSpec(
            combine=plan.combine,
            expressions=plan.expressions,
            variable_names=plan.variable_names,
            parameters=plan.parameters or None,
        )
        macro_str = getattr(spec, "_template_macro_str", None)
        macro_preview = macro_str().strip() if callable(macro_str) else None
        return {
            "status": "ok",
            "macro_preview": macro_preview,
        }
    except Exception as exc:  # pragma: no cover - environment dependent
        return {
            "status": "error",
            "reason": str(exc),
        }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a PySR TemplateExpressionSpec construction plan without running a search.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  template_spec_builder.py --combine 'sin(f(x1, x2)) + g(x3)' \\\n"
            "    --expression f --expression g --variable-name x1 --variable-name x2 --variable-name x3\n\n"
            "  template_spec_builder.py --json '{\"combine\": \"f(x)\", \"expressions\": [\"f\"], \"variable_names\": [\"x\"]}'\n\n"
            "  template_spec_builder.py --combine 'p[class] * f(x1, x2)' \\\n"
            "    --expression f --variable-name x1 --variable-name x2 --variable-name class \\\n"
            "    --parameter p=3 --category-column class --zero-based-categories"
        ),
    )
    parser.add_argument("--json", dest="plan_json", help="Inline JSON object describing the plan.")
    parser.add_argument("--json-file", type=Path, help="Path to a JSON file describing the plan.")
    parser.add_argument("--combine", help="Julia combine string.")
    parser.add_argument(
        "--expression",
        action="append",
        dest="expressions",
        help="Template placeholder name. Repeat to add multiple expressions.",
    )
    parser.add_argument(
        "--variable-name",
        action="append",
        dest="variable_names",
        help="Variable name. Repeat to set the template variable order.",
    )
    parser.add_argument(
        "--parameter",
        action="append",
        help="Parameter declaration NAME=LEN. Repeat to add indexed parameter vectors.",
    )
    parser.add_argument(
        "--guess",
        action="append",
        help="Template guess NAME=EXPR. Repeat to build one template-guess dictionary.",
    )
    parser.add_argument(
        "--note",
        action="append",
        help="Optional planning note to include in the output.",
    )
    parser.add_argument(
        "--vector-valued",
        action="store_true",
        help="Annotate a residual-style vector-valued template plan.",
    )
    parser.add_argument(
        "--category-column",
        help="Name of the category column in X, if any.",
    )
    parser.add_argument(
        "--zero-based-categories",
        action="store_true",
        help="Flag source categories as zero-based so the plan prints the +1 reminder.",
    )
    parser.add_argument(
        "--check-template",
        action="store_true",
        help="Optionally import PySR and validate the constructor without fitting.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        plan = _build_plan(args)
        errors, warnings = _validate_plan(plan)
    except ValueError as exc:
        payload = {
            "status": "error",
            "errors": [str(exc)],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2

    constructor_validation = _try_constructor_check(plan, args.check_template)
    if constructor_validation and constructor_validation.get("status") == "error":
        errors.append(constructor_validation["reason"])

    payload = {
        "status": "ok" if not errors else "error",
        "plan": asdict(plan),
        "template_spec_preview": _constructor_preview(plan),
        "template_guesses_preview": _guess_preview(plan),
        "warnings": warnings,
        "errors": errors,
        "recommendations": _recommendations(plan),
        "constructor_validation": constructor_validation,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
