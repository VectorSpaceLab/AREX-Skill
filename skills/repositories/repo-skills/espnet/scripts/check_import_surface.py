#!/usr/bin/env python3
"""Safely import selected ESPnet modules without running models or downloads."""
from __future__ import annotations
import argparse
import contextlib
import importlib
import io
import json
import sys
from typing import Any

DEFAULT_MODULES = [
    "espnet2",
    "espnet3",
    "espnet2.bin.asr_train",
    "espnet2.bin.asr_inference",
    "espnet2.bin.tokenize_text",
    "espnet3.utils.stages_utils",
]


def import_with_capture(name: str) -> dict[str, Any]:
    captured_out = io.StringIO()
    captured_err = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_out), contextlib.redirect_stderr(captured_err):
            importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic tool should report any import failure.
        result: dict[str, Any] = {"module": name, "status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    else:
        result = {"module": name, "status": "PASS"}
    messages = (captured_out.getvalue() + captured_err.getvalue()).strip()
    if messages:
        result["messages"] = messages
    return result


def check(modules: list[str]) -> list[dict[str, Any]]:
    return [import_with_capture(name) for name in modules]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check importability of selected ESPnet modules.")
    parser.add_argument("--modules", nargs="+", default=DEFAULT_MODULES)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results = check(args.modules)
    ok = all(item["status"] == "PASS" for item in results)
    if args.json:
        print(json.dumps({"ok": ok, "results": results}, indent=2))
    else:
        for item in results:
            message = f"[{item['status']}] {item['module']}"
            if "error" in item:
                message += f" :: {item['error']}"
            print(message)
            if "messages" in item:
                print(item["messages"], file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
