#!/usr/bin/env python3
"""De-identify one synthetic code-mixed note and emit JSON.

The note, identifiers, and fallback recognizer are fabricated test data. By
default the script uses a no-download fixture loader so it stays offline.
Pass --real-model with --model-name to exercise a live checkpoint instead.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from openmed import deidentify, reidentify
from openmed.core.budget import RequestBudget

DEFAULT_MODEL_NAME = "OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1"
DEFAULT_DATE_SHIFT_SECRET = "synthetic-date-shift-secret"
SYNTHETIC_NOTE_ID = "synthetic-code-mixed-note"

SYNTHETIC_NOTE = (
    "Synthetic example only. Casey Example spoke with Asha Patel on 2026-08-12. "
    "Casey Example asked for a callback at 555-0100 and wrote from 42 Example Street, Boston. "
    "Email casey.example@example.test. दवा ठीक है."
)

SYNTHETIC_TERMS: tuple[tuple[str, str], ...] = (
    ("Casey Example", "PERSON"),
    ("Asha Patel", "PERSON"),
    ("2026-08-12", "DATE"),
    ("555-0100", "PHONE"),
    ("casey.example@example.test", "EMAIL"),
    ("42 Example Street", "ADDRESS"),
)


class _FixturePipeline:
    """No-download token-classification stand-in for the synthetic note."""

    tokenizer = None

    def __call__(self, inputs: Any, **_: Any) -> list[Any]:
        if isinstance(inputs, list):
            return [[] for _ in inputs]
        return []


class _FixtureLoader:
    """Loader compatible with ``deidentify(..., loader=...)``."""

    config = None

    def create_pipeline(self, *_: Any, **__: Any) -> Any:
        return _FixturePipeline()

    def get_max_sequence_length(self, *_: Any, **__: Any) -> None:
        return None


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-name",
        default=DEFAULT_MODEL_NAME,
        help="Real model name or local checkpoint to use with --real-model.",
    )
    parser.add_argument(
        "--real-model",
        action="store_true",
        help="Use the supplied model instead of the no-download fixture loader.",
    )
    parser.add_argument(
        "--method",
        default="mask",
        choices=(
            "mask",
            "aadhaar_mask",
            "remove",
            "replace",
            "hash",
            "shift_dates",
            "format_preserve",
        ),
        help="De-identification method to apply.",
    )
    parser.add_argument("--lang", default="en", help="PII routing language.")
    parser.add_argument(
        "--locale",
        help="Optional Faker locale override for surrogate generation.",
    )
    parser.add_argument(
        "--policy",
        help="Optional policy profile name to apply locally.",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.7,
        help="Minimum span confidence to keep.",
    )
    parser.add_argument(
        "--keep-year",
        action="store_true",
        help="Keep the year when date redaction allows it.",
    )
    parser.add_argument(
        "--keep-mapping",
        action="store_true",
        help="Return a reversible mapping for authorized re-identification.",
    )
    parser.add_argument(
        "--consistent",
        action="store_true",
        help="Reuse the same surrogate for repeated source values.",
    )
    parser.add_argument("--seed", type=int, help="Deterministic surrogate seed.")
    parser.add_argument(
        "--code-mixed",
        action="store_true",
        help="Enable code-mixed routing hints for mixed-script text.",
    )
    parser.add_argument(
        "--date-shift-days",
        type=int,
        help="Fixed date shift when method=shift_dates and no patient key is supplied.",
    )
    parser.add_argument(
        "--date-shift-max-days",
        type=int,
        help="Maximum absolute date shift for patient-keyed runs.",
    )
    parser.add_argument(
        "--patient-key",
        help="Stable patient token for patient-keyed date shifting.",
    )
    parser.add_argument(
        "--date-shift-secret",
        help="Secret material for patient-keyed date shifting.",
    )
    parser.add_argument(
        "--max-input-chars",
        type=int,
        help="Optional cooperative input-size budget.",
    )
    parser.add_argument(
        "--max-wall-time",
        type=float,
        help="Optional cooperative wall-time budget in seconds.",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Request an audit report in the JSON payload.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the JSON payload to a file instead of stdout.",
    )
    return parser


def build_custom_recognizer() -> dict[str, Any]:
    """Create deterministic synthetic terms for the offline fixture path."""

    return {
        "case_sensitive": False,
        "deny": {
            "terms": [
                {"term": term, "label": label}
                for term, label in SYNTHETIC_TERMS
            ]
        },
    }


def build_budget(args: argparse.Namespace) -> RequestBudget | None:
    """Build an optional cooperative budget from CLI arguments."""

    if args.max_input_chars is None and args.max_wall_time is None:
        return None
    return RequestBudget(
        max_input_chars=args.max_input_chars,
        max_wall_time=args.max_wall_time,
    )


def assert_synthetic_terms_redacted(deidentified_text: str) -> None:
    """Fail closed if any synthetic identifier survives redaction."""

    leaked = [term for term, _ in SYNTHETIC_TERMS if term in deidentified_text]
    if leaked:
        raise AssertionError(
            f"Synthetic identifiers were not redacted: {leaked!r}"
        )


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Redact the synthetic note and return a JSON-ready payload."""

    kwargs: dict[str, Any] = {
        "method": args.method,
        "model_name": args.model_name,
        "confidence_threshold": args.confidence_threshold,
        "keep_year": args.keep_year,
        "keep_mapping": args.keep_mapping,
        "consistent": args.consistent,
        "seed": args.seed,
        "lang": args.lang,
        "locale": args.locale,
        "policy": args.policy,
        "audit": args.audit,
        "code_mixed": args.code_mixed,
        "custom_recognizer": build_custom_recognizer(),
        "use_safety_sweep": True,
    }

    if args.method == "shift_dates":
        if args.date_shift_days is None and args.patient_key is None:
            kwargs["date_shift_days"] = 30
        elif args.date_shift_days is not None:
            kwargs["date_shift_days"] = args.date_shift_days
        if args.date_shift_max_days is not None:
            kwargs["date_shift_max_days"] = args.date_shift_max_days
        if args.patient_key is not None:
            kwargs["patient_key"] = args.patient_key
            kwargs["date_shift_secret"] = (
                args.date_shift_secret
                if args.date_shift_secret is not None
                else DEFAULT_DATE_SHIFT_SECRET
            )

    budget = build_budget(args)
    if budget is not None:
        kwargs["budget"] = budget

    if not args.real_model:
        kwargs["loader"] = _FixtureLoader()

    result = deidentify(SYNTHETIC_NOTE, **kwargs)
    assert_synthetic_terms_redacted(result.deidentified_text)

    payload: dict[str, Any] = {
        "note_id": SYNTHETIC_NOTE_ID,
        "synthetic": True,
        "mode": "real-model" if args.real_model else "fixture-loader",
        "request": {
            "method": args.method,
            "model_name": args.model_name,
            "lang": args.lang,
            "locale": args.locale,
            "policy": args.policy,
            "confidence_threshold": args.confidence_threshold,
            "keep_year": args.keep_year,
            "keep_mapping": args.keep_mapping,
            "consistent": args.consistent,
            "seed": args.seed,
            "code_mixed": args.code_mixed,
            "date_shift_days": args.date_shift_days,
            "date_shift_max_days": args.date_shift_max_days,
            "patient_key_set": args.patient_key is not None,
            "audit": args.audit,
            "max_input_chars": args.max_input_chars,
            "max_wall_time": args.max_wall_time,
        },
        "result": result.to_dict(),
    }

    if result.mapping is not None:
        payload["mapping"] = result.mapping
        payload["round_trip_ok"] = (
            reidentify(result.deidentified_text, result.mapping) == SYNTHETIC_NOTE
        )

    return payload


def main(argv: Sequence[str] | None = None) -> int:
    """Run the example and print JSON."""

    args = build_parser().parse_args(argv)
    payload = run(args)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
