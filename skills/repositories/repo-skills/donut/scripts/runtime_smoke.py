#!/usr/bin/env python3
"""Smoke-check a runtime environment for the Donut repo skill.

This helper is intentionally self-contained: it checks installed packages and
public Donut APIs without depending on the original repository checkout.
"""
from __future__ import annotations

import argparse
import inspect
import json
import sys
from typing import Any, Dict, Iterable, List

DEFAULT_CHECKS = ("imports", "signatures", "token-roundtrip")
ALL_CHECKS = ("imports", "signatures", "token-roundtrip", "cuda", "synthdog")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify Donut imports, public API signatures, token helpers, and optional backends."
    )
    parser.add_argument(
        "--check",
        action="append",
        choices=("all",) + ALL_CHECKS,
        help="Check group to run. Repeat the flag. Defaults to imports, signatures, and token-roundtrip.",
    )
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Fail if CUDA is unavailable. Use before training workflows that require CUDA.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the report as JSON instead of human-readable text.",
    )
    return parser


def selected_checks(values: Iterable[str] | None) -> List[str]:
    if not values:
        return list(DEFAULT_CHECKS)
    result: List[str] = []
    for value in values:
        if value == "all":
            result.extend(ALL_CHECKS)
        else:
            result.append(value)
    # preserve order while deduplicating
    return list(dict.fromkeys(result))


def package_version(dist_name: str) -> str:
    try:
        from importlib.metadata import version
    except ImportError:  # pragma: no cover - Python 3.7 fallback
        from importlib_metadata import version  # type: ignore

    try:
        return version(dist_name)
    except Exception:
        return "unknown"


def check_imports(report: Dict[str, Any]) -> None:
    import donut
    import torch
    import transformers

    report["imports"] = {
        "donut_module": getattr(donut, "__name__", "donut"),
        "donut_python_version": package_version("donut-python"),
        "torch": getattr(torch, "__version__", "unknown"),
        "transformers": getattr(transformers, "__version__", "unknown"),
    }


def check_signatures(report: Dict[str, Any]) -> None:
    from donut import DonutConfig, DonutDataset, DonutModel, JSONParseEvaluator

    report["signatures"] = {
        "DonutConfig": str(inspect.signature(DonutConfig)),
        "DonutModel": str(inspect.signature(DonutModel)),
        "DonutModel.from_pretrained": str(inspect.signature(DonutModel.from_pretrained)),
        "DonutModel.inference": str(inspect.signature(DonutModel.inference)),
        "DonutDataset": str(inspect.signature(DonutDataset)),
        "JSONParseEvaluator": str(inspect.signature(JSONParseEvaluator)),
    }


def check_token_roundtrip(report: Dict[str, Any]) -> None:
    from donut import DonutModel

    class DummyTokenizer:
        all_special_tokens = {"<sep/>"}

        def get_added_vocab(self) -> Dict[str, int]:
            return {}

    class DummyDecoder:
        def __init__(self) -> None:
            self.tokenizer = DummyTokenizer()
            self.added_tokens: List[str] = []

        def add_special_tokens(self, tokens: List[str]) -> None:
            self.added_tokens.extend(tokens)

    model = object.__new__(DonutModel)
    model.decoder = DummyDecoder()

    # Donut collapses a single-item list of nested dictionaries during token2json,
    # so use a nested dictionary fixture for an exact smoke round-trip.
    obj = {"menu": {"nm": "Tea", "cnt": "2"}, "total": {"total_price": "5.00"}}
    token_string = DonutModel.json2token(model, obj, update_special_tokens_for_json_key=True, sort_json_key=True)
    parsed = DonutModel.token2json(model, token_string)
    if parsed != obj:
        raise AssertionError(f"Token round-trip changed data: expected {obj!r}, got {parsed!r}")
    report["token_roundtrip"] = {
        "input": obj,
        "token_string": token_string,
        "parsed": parsed,
        "added_special_tokens": model.decoder.added_tokens,
    }


def check_cuda(report: Dict[str, Any], require_cuda: bool) -> None:
    import torch

    available = bool(torch.cuda.is_available())
    devices = []
    if available:
        devices = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    if require_cuda and not available:
        raise RuntimeError("CUDA is required for this check, but torch.cuda.is_available() is false.")
    report["cuda"] = {"available": available, "device_count": len(devices), "devices": devices}


def check_synthdog(report: Dict[str, Any]) -> None:
    import cv2
    import numpy as np
    import pytweening
    import synthtiger

    report["synthdog"] = {
        "synthtiger": getattr(synthtiger, "__version__", package_version("synthtiger")),
        "numpy": getattr(np, "__version__", "unknown"),
        "opencv": getattr(cv2, "__version__", "unknown"),
        "pytweening": getattr(pytweening, "__version__", package_version("pytweening")),
    }


def print_text(report: Dict[str, Any]) -> None:
    print("Donut runtime smoke report")
    for section, value in report.items():
        print(f"\n[{section}]")
        if isinstance(value, dict):
            for key, item in value.items():
                print(f"{key}: {item}")
        else:
            print(value)


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    checks = selected_checks(args.check)
    report: Dict[str, Any] = {"checks": checks}

    try:
        if "imports" in checks:
            check_imports(report)
        if "signatures" in checks:
            check_signatures(report)
        if "token-roundtrip" in checks:
            check_token_roundtrip(report)
        if "cuda" in checks or args.require_cuda:
            check_cuda(report, args.require_cuda)
        if "synthdog" in checks:
            check_synthdog(report)
    except Exception as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc), "partial_report": report}, indent=2), file=sys.stderr)
        else:
            print(f"Donut runtime smoke failed: {exc}", file=sys.stderr)
            if report:
                print_text(report)
        return 1

    report["ok"] = True
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
