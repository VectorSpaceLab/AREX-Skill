#!/usr/bin/env python3
"""Safe Snips NLU engine API smoke helper.

The helper accepts an explicit dataset JSON path and query, fits a
SnipsNLUEngine, runs parse/get_intents/get_slots, and optionally proves
persist/load to a fresh directory. It prints a single JSON report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _positive_int(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def _parse_intent_filters(values: Optional[Iterable[str]]) -> Optional[List[str]]:
    filters: List[str] = []
    for value in values or []:
        for item in value.split(","):
            item = item.strip()
            if item:
                filters.append(item)
    return filters or None


def _emit(payload: Dict[str, Any], exit_code: int) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


def _exception_payload(stage: str, exc: BaseException) -> Dict[str, Any]:
    return {
        "ok": False,
        "stage": stage,
        "error": {
            "type": type(exc).__name__,
            "message": str(exc),
        },
    }


def _load_dataset(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("dataset JSON root must be an object")
    return data


def _top_intent_from_parse(parse_result: Any) -> Optional[str]:
    if isinstance(parse_result, list):
        if not parse_result:
            return None
        first = parse_result[0]
    else:
        first = parse_result
    if not isinstance(first, dict):
        return None
    intent = first.get("intent") or {}
    if not isinstance(intent, dict):
        return None
    return intent.get("intentName")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Fit SnipsNLUEngine on an explicit dataset JSON, parse a query, "
            "and print a JSON smoke report."
        )
    )
    parser.add_argument(
        "--dataset",
        required=True,
        type=Path,
        help="Path to a Snips dataset JSON file. No embedded sample path is used.",
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Input text to parse after fitting the engine.",
    )
    parser.add_argument(
        "--intent-filter",
        action="append",
        default=[],
        help=(
            "Allowed intent name. May be repeated or comma-separated. The "
            "implicit None intent remains eligible."
        ),
    )
    parser.add_argument(
        "--top-n",
        type=_positive_int,
        default=None,
        help="Return at most N ranked parse hypotheses instead of one result.",
    )
    parser.add_argument(
        "--persist-dir",
        type=Path,
        default=None,
        help=(
            "Optional fresh directory where the fitted engine is persisted and "
            "loaded back. Existing paths are refused."
        ),
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Integer random seed passed to SnipsNLUEngine (default: 42).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    intent_filters = _parse_intent_filters(args.intent_filter)

    try:
        dataset = _load_dataset(args.dataset)
    except Exception as exc:  # pylint: disable=broad-except
        payload = _exception_payload("load_dataset", exc)
        payload["next_steps"] = [
            "Pass --dataset pointing to a readable Snips dataset JSON file.",
            "For YAML or schema authoring, use the dataset-and-resources sub-skill first.",
        ]
        return _emit(payload, 2)

    try:
        from snips_nlu import SnipsNLUEngine
        from snips_nlu.exceptions import (  # type: ignore
            IncompatibleModelError,
            IntentNotFoundError,
            InvalidInputError,
            LoadingError,
            NotTrained,
            PersistingError,
        )
        from snips_nlu.resources import MissingResource  # type: ignore
    except Exception as exc:  # pylint: disable=broad-except
        payload = _exception_payload("import_snips_nlu", exc)
        payload["next_steps"] = [
            "Run this helper in an environment where snips-nlu is installed.",
            "For snips-nlu 0.20.x, a Python 3.8 CPU environment is the safest choice.",
        ]
        return _emit(payload, 3)

    known_api_errors = (
        IncompatibleModelError,
        IntentNotFoundError,
        InvalidInputError,
        LoadingError,
        MissingResource,
        NotTrained,
        PersistingError,
    )

    try:
        engine = SnipsNLUEngine(random_state=args.random_state)
        engine.fit(dataset)
        parse_result = engine.parse(
            args.query,
            intents=intent_filters,
            top_n=args.top_n,
        )
        intents = engine.get_intents(args.query)
        top_intent = _top_intent_from_parse(parse_result)
        slots = engine.get_slots(args.query, top_intent)

        report: Dict[str, Any] = {
            "ok": True,
            "dataset": str(args.dataset),
            "dataset_language": dataset.get("language"),
            "query": args.query,
            "intent_filter": intent_filters,
            "top_n": args.top_n,
            "random_state": args.random_state,
            "parse": parse_result,
            "get_intents": intents,
            "slots_for_top_intent": {
                "intentName": top_intent,
                "slots": slots,
            },
        }

        if args.persist_dir is not None:
            persist_dir = args.persist_dir
            if persist_dir.exists():
                return _emit(
                    {
                        "ok": False,
                        "stage": "persist_precheck",
                        "error": {
                            "type": "PersistingError",
                            "message": "persist directory already exists",
                        },
                        "persist_dir": str(persist_dir),
                        "next_steps": [
                            "Choose a fresh --persist-dir.",
                            "Remove or archive the existing directory only if overwriting is intended.",
                        ],
                    },
                    5,
                )
            engine.persist(persist_dir)
            loaded = SnipsNLUEngine.from_path(persist_dir)
            report["persist"] = {
                "path": str(persist_dir),
                "loaded_fitted": bool(loaded.fitted),
                "loaded_parse": loaded.parse(
                    args.query,
                    intents=intent_filters,
                    top_n=args.top_n,
                ),
            }

        return _emit(report, 0)

    except MissingResource as exc:
        language = dataset.get("language") or "<dataset-language>"
        payload = _exception_payload("resources", exc)
        payload["dataset_language"] = dataset.get("language")
        payload["next_steps"] = [
            f"Install/link Snips NLU resources for language '{language}'.",
            f"Typical command: python -m snips_nlu download {language}",
            "If using a custom resource package or directory, pass compatible resources in application code.",
        ]
        return _emit(payload, 4)
    except known_api_errors as exc:
        payload = _exception_payload("engine_api", exc)
        payload["next_steps"] = [
            "Check references/troubleshooting.md in the engine-api sub-skill.",
            "Verify the dataset language, intent names, fitted state, and persistence path.",
        ]
        return _emit(payload, 6)
    except Exception as exc:  # pylint: disable=broad-except
        payload = _exception_payload("unexpected", exc)
        payload["next_steps"] = [
            "Check package installation, Python version, dependency compatibility, and language resources.",
            "For snips-nlu 0.20.x, prefer a Python 3.8 CPU environment.",
        ]
        return _emit(payload, 7)


if __name__ == "__main__":
    sys.exit(main())
