#!/usr/bin/env python3
"""Safe preflight checks for LitGPT evaluation and serving workflows.

This script performs deterministic local checks only. It does not download
models or datasets, load checkpoint weights, start a server, or run evaluation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import socket
import sys
from pathlib import Path
from typing import Any


OPTIONAL_MODULES = {
    "lm_eval": "required for litgpt evaluate task listing and benchmark runs",
    "litserve": "required for litgpt serve",
    "jinja2": "required for litgpt serve --openai_spec true chat-template rendering",
    "bitsandbytes": "required for --quantize bnb.* modes",
}


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def normalize_batch_size(value: str) -> tuple[bool, str]:
    if value.startswith("auto"):
        if value == "auto":
            return True, "auto batch-size selection"
        _, separator, suffix = value.partition(":")
        if separator and suffix.isdigit() and int(suffix) > 0:
            return True, "auto:N batch-size selection"
        return False, "auto batch size must be 'auto' or 'auto:N' with N > 0"
    try:
        parsed = int(value)
    except ValueError:
        return False, "batch_size must be a positive integer, 'auto', or 'auto:N'"
    if parsed <= 0:
        return False, "batch_size integer must be greater than zero"
    return True, "positive integer batch size"


def check_port_available(host: str, port: int) -> tuple[bool, str]:
    if port <= 0 or port > 65535:
        return False, "port must be between 1 and 65535"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.25)
    try:
        result = sock.connect_ex((host, port))
    finally:
        sock.close()
    if result == 0:
        return False, f"{host}:{port} appears to be in use"
    return True, f"{host}:{port} did not accept a TCP connection during the quick check"


def checkpoint_hints(path: Path | None, openai_spec: bool) -> dict[str, Any]:
    if path is None:
        return {"provided": False, "status": "not_checked", "hints": ["pass --checkpoint-dir to inspect local file hints"]}

    hints: list[str] = []
    files: dict[str, bool] = {}
    if not path.exists():
        return {
            "provided": True,
            "path_kind": "missing",
            "status": "fail",
            "hints": ["checkpoint path does not exist locally; it may be a model name or needs download/conversion"],
        }
    if not path.is_dir():
        return {
            "provided": True,
            "path_kind": "file",
            "status": "fail",
            "hints": ["checkpoint path should be a directory for litgpt evaluate/serve"],
        }

    expected = ["lit_model.pth", "model_config.yaml", "tokenizer.json", "tokenizer_config.json"]
    for filename in expected:
        files[filename] = (path / filename).is_file()

    if not files["lit_model.pth"]:
        hints.append("lit_model.pth not found; route checkpoint layout/conversion to checkpoint-conversion")
    if not files["model_config.yaml"]:
        hints.append("model_config.yaml not found; LitGPT config may be missing")
    if not files["tokenizer.json"]:
        hints.append("tokenizer.json not found; tokenizer files may need download/copy")
    if openai_spec and not files["tokenizer_config.json"]:
        hints.append("tokenizer_config.json not found; OpenAI spec mode needs tokenizer config for chat templates")
    elif not files["tokenizer_config.json"]:
        hints.append("tokenizer_config.json not found; some serving/chat flows may need it")

    return {
        "provided": True,
        "path_kind": "directory",
        "status": "ok" if not hints else "warn",
        "files": files,
        "hints": hints,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check optional LitGPT evaluation/serving dependencies and safe preconditions.")
    parser.add_argument("--mode", choices=["evaluate", "serve", "both"], default="both", help="workflow surface to check")
    parser.add_argument("--checkpoint-dir", type=Path, help="optional local checkpoint directory to inspect for readiness hints")
    parser.add_argument("--batch-size", default="1", help="evaluate batch_size value to validate; accepts positive int, auto, auto:N")
    parser.add_argument("--host", default="127.0.0.1", help="host used for the quick port availability check")
    parser.add_argument("--port", type=int, default=8000, help="port used for the quick serving availability check")
    parser.add_argument("--openai-spec", action="store_true", help="also check OpenAI-compatible serving requirements")
    parser.add_argument("--quantize", default=None, help="planned quantization value such as bnb.nf4; checks bitsandbytes when bnb.*")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    checks: list[dict[str, Any]] = []
    failures = 0
    warnings = 0

    def add_check(name: str, ok: bool, message: str, required: bool = True, details: Any = None) -> None:
        nonlocal failures, warnings
        status = "ok" if ok else "fail" if required else "warn"
        if not ok and required:
            failures += 1
        elif not ok:
            warnings += 1
        checks.append({"name": name, "status": status, "message": message, "details": details})

    if args.mode in {"evaluate", "both"}:
        available = module_available("lm_eval")
        add_check("lm_eval import", available, OPTIONAL_MODULES["lm_eval"], required=True)
        batch_ok, batch_message = normalize_batch_size(str(args.batch_size))
        add_check("batch_size", batch_ok, batch_message, required=True)

    if args.mode in {"serve", "both"}:
        available = module_available("litserve")
        add_check("litserve import", available, OPTIONAL_MODULES["litserve"], required=True)
        port_ok, port_message = check_port_available(args.host, args.port)
        add_check("port availability", port_ok, port_message, required=True)
        if args.openai_spec:
            jinja_available = module_available("jinja2")
            add_check("jinja2 import", jinja_available, OPTIONAL_MODULES["jinja2"], required=True)

    if args.quantize and args.quantize.startswith("bnb."):
        bnb_available = module_available("bitsandbytes")
        add_check("bitsandbytes import", bnb_available, OPTIONAL_MODULES["bitsandbytes"], required=True)

    checkpoint = checkpoint_hints(args.checkpoint_dir, args.openai_spec)
    if checkpoint["status"] == "fail":
        failures += 1
    elif checkpoint["status"] == "warn":
        warnings += 1
    checks.append({"name": "checkpoint hints", "status": checkpoint["status"], "message": "local checkpoint readiness hints", "details": checkpoint})

    result = {"ok": failures == 0, "failures": failures, "warnings": warnings, "checks": checks}

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"LitGPT evaluation/serving preflight: {'OK' if result['ok'] else 'FAILED'}")
        for check in checks:
            print(f"[{check['status']}] {check['name']}: {check['message']}")
            details = check.get("details")
            if isinstance(details, dict):
                for hint in details.get("hints", []):
                    print(f"  - {hint}")
        if failures:
            print("Resolve failed checks before running litgpt evaluate or litgpt serve.", file=sys.stderr)

    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
