#!/usr/bin/env python3
"""Safely inspect optional Baleen imports without running retrieval."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


SYMBOL_CHECKS = [
    ("baleen.engine", "Baleen"),
    ("baleen.hop_searcher", "HopSearcher"),
    ("baleen.hop_searcher", "TextQueries"),
    ("baleen.condenser.condense", "Condenser"),
    ("baleen.condenser.model", "ElectraReader"),
    ("baleen.condenser.tokenization", "AnswerAwareTokenizer"),
    ("baleen.utils.loaders", "load_collectionX"),
    ("baleen.utils.loaders", "load_contexts"),
]


SIGNATURE_CHECKS = [
    ("baleen.engine", "Baleen"),
    ("baleen.engine", "Baleen.search"),
    ("baleen.hop_searcher", "HopSearcher"),
    ("baleen.hop_searcher", "HopSearcher.encode"),
    ("baleen.hop_searcher", "HopSearcher.search"),
    ("baleen.hop_searcher", "HopSearcher.search_all"),
    ("baleen.condenser.condense", "Condenser"),
    ("baleen.condenser.condense", "Condenser.condense"),
    ("baleen.condenser.tokenization", "AnswerAwareTokenizer"),
    ("baleen.utils.loaders", "load_collectionX"),
    ("baleen.utils.loaders", "load_contexts"),
]


def resolve_symbol(module: Any, dotted_name: str) -> Any:
    current = module
    for part in dotted_name.split("."):
        current = getattr(current, part)
    return current


def check_symbol(module_name: str, symbol_name: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "module": module_name,
        "symbol": symbol_name,
        "available": False,
    }

    try:
        module = importlib.import_module(module_name)
        resolve_symbol(module, symbol_name)
    except Exception as exc:  # noqa: BLE001 - diagnostics should report import-time failures.
        record["error_type"] = type(exc).__name__
        record["error"] = str(exc)
    else:
        record["available"] = True

    return record


def check_signature(module_name: str, symbol_name: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "module": module_name,
        "symbol": symbol_name,
        "available": False,
    }

    try:
        module = importlib.import_module(module_name)
        symbol = resolve_symbol(module, symbol_name)
        record["signature"] = str(inspect.signature(symbol))
    except Exception as exc:  # noqa: BLE001 - diagnostics should report all signature failures.
        record["error_type"] = type(exc).__name__
        record["error"] = str(exc)
    else:
        record["available"] = True

    return record


def run_tiny_fixture() -> dict[str, Any]:
    fixture: dict[str, Any] = {"ran": True, "ok": False}

    try:
        loaders = importlib.import_module("baleen.utils.loaders")
        load_collectionx = getattr(loaders, "load_collectionX")
        load_contexts = getattr(loaders, "load_contexts")
    except Exception as exc:  # noqa: BLE001
        fixture["error_type"] = type(exc).__name__
        fixture["error"] = str(exc)
        return fixture

    with tempfile.TemporaryDirectory(prefix="baleen-inspect-") as temp_dir:
        temp_path = Path(temp_dir)
        collection_path = temp_path / "collectionX.jsonl"
        contexts_path = temp_path / "contexts.jsonl"

        collection_rows = [
            {"pid": 0, "title": "Alpha", "text": ["Alpha supports beta.", "Beta supports gamma."]},
            {"pid": 1, "title": "Gamma", "text": ["Gamma supports delta."]},
        ]
        collection_path.write_text(
            "\n".join(json.dumps(row, sort_keys=True) for row in collection_rows) + "\n",
            encoding="utf-8",
        )
        contexts_path.write_text(json.dumps(["q1", [[0, 0], [1, 0]]]) + "\n", encoding="utf-8")

        try:
            flat_collection = load_collectionx(str(collection_path))
            nested_collection = load_collectionx(str(collection_path), dict_in_dict=True)
            contexts = load_contexts(str(contexts_path))
        except Exception as exc:  # noqa: BLE001
            fixture["error_type"] = type(exc).__name__
            fixture["error"] = str(exc)
            return fixture

    fixture.update(
        {
            "ok": True,
            "flat_collection_size": len(flat_collection),
            "nested_collection_pids": sorted(nested_collection.keys()),
            "sample_fact": flat_collection.get((0, 0)),
            "contexts": {str(key): value for key, value in contexts.items()},
        }
    )
    return fixture


def build_report(include_tiny_fixture: bool) -> dict[str, Any]:
    symbol_checks = [check_symbol(module_name, symbol_name) for module_name, symbol_name in SYMBOL_CHECKS]
    signature_checks = [check_signature(module_name, symbol_name) for module_name, symbol_name in SIGNATURE_CHECKS]
    report: dict[str, Any] = {
        "ok": all(check["available"] for check in symbol_checks + signature_checks),
        "symbols": symbol_checks,
        "signatures": signature_checks,
        "tiny_fixture": {"ran": False},
        "notes": [
            "This script does not instantiate HopSearcher or Condenser.",
            "This script does not load checkpoints, build indexes, run retrieval, download models, or create persistent files.",
            "Passing imports do not prove that user checkpoints, devices, indexes, or collectionX data are compatible.",
        ],
    }

    if include_tiny_fixture:
        report["tiny_fixture"] = run_tiny_fixture()
        report["ok"] = report["ok"] and bool(report["tiny_fixture"].get("ok"))

    return report


def print_text_report(report: dict[str, Any]) -> None:
    status = "OK" if report["ok"] else "ISSUES FOUND"
    print(f"Baleen import inspection: {status}")
    print()

    print("Symbols:")
    for check in report["symbols"]:
        marker = "ok" if check["available"] else "missing"
        print(f"  [{marker}] {check['module']}:{check['symbol']}")
        if not check["available"]:
            print(f"      {check.get('error_type', 'Error')}: {check.get('error', '')}")

    print()
    print("Signatures:")
    for check in report["signatures"]:
        marker = "ok" if check["available"] else "missing"
        signature = f" {check['signature']}" if check.get("signature") else ""
        print(f"  [{marker}] {check['module']}:{check['symbol']}{signature}")
        if not check["available"]:
            print(f"      {check.get('error_type', 'Error')}: {check.get('error', '')}")

    fixture = report["tiny_fixture"]
    if fixture.get("ran"):
        print()
        marker = "ok" if fixture.get("ok") else "failed"
        print(f"Tiny fixture: {marker}")
        if fixture.get("ok"):
            print(f"  flat_collection_size={fixture['flat_collection_size']}")
            print(f"  nested_collection_pids={fixture['nested_collection_pids']}")
            print(f"  sample_fact={fixture['sample_fact']!r}")
            print(f"  contexts={fixture['contexts']}")
        else:
            print(f"  {fixture.get('error_type', 'Error')}: {fixture.get('error', '')}")

    print()
    for note in report["notes"]:
        print(f"note: {note}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely inspect optional Baleen imports without running ColBERT retrieval or loading condenser checkpoints."
    )
    parser.add_argument(
        "--tiny-fixture",
        action="store_true",
        help="also validate Baleen loader behavior on temporary tiny JSONL files",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit a machine-readable JSON report",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(include_tiny_fixture=args.tiny_fixture)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
