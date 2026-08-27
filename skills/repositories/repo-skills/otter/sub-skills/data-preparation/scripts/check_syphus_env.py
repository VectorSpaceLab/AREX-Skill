#!/usr/bin/env python3
"""No-network Syphus environment and input preflight.

This script checks dependency imports, expected environment variables, adapter
names, and optional prompt/query JSON files. It never calls an API endpoint.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

AVAILABLE_DATASETS = {
    "change.SpotTheDifference",
    "change.CocoSpotTheDifference",
    "video.DenseCaptions",
    "video.TVCaptions",
    "video.VisualStoryTelling",
    "3d.SceneNavigation",
    "funqa.FunQA_translation",
    "funqa.FunQA_mcqa",
    "funqa.FunQA_dia",
    "fpv.EGO4D",
    "translate.Translation",
}

ENV_VARS = (
    "OPENAI_API_TYPE",
    "OPENAI_API_BASE",
    "OPENAI_API_VERSION",
    "OPENAI_API_KEY",
    "OPENAI_API_ENGINE",
)

DEFAULTS = {
    "OPENAI_API_TYPE": "local",
    "OPENAI_API_BASE": "http://localhost:8000",
    "OPENAI_API_VERSION": "2020-04-01",
    "OPENAI_API_KEY": "",
    "OPENAI_API_ENGINE": "davinci",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def check_import(module: str) -> tuple[bool, str]:
    spec = importlib.util.find_spec(module)
    if spec is None:
        return False, f"missing module: {module}"
    return True, f"found module: {module}"


def validate_prompt(path: Path) -> list[str]:
    messages: list[str] = []
    try:
        data = load_json(path)
    except Exception as exc:
        return [f"ERROR prompt: could not parse JSON: {exc}"]
    if not isinstance(data, dict):
        return ["ERROR prompt: top-level value must be an object"]
    if not isinstance(data.get("system_message"), str):
        messages.append("ERROR prompt: missing string system_message")
    in_context = data.get("in_context")
    if not isinstance(in_context, list):
        messages.append("ERROR prompt: missing list in_context")
    else:
        for idx, item in enumerate(in_context[:20]):
            if not isinstance(item, dict):
                messages.append(f"ERROR prompt.in_context[{idx}]: item must be an object")
                continue
            if item.get("role") not in {"user", "assistant"}:
                messages.append(f"ERROR prompt.in_context[{idx}]: role must be user or assistant")
            if "content" not in item:
                messages.append(f"ERROR prompt.in_context[{idx}]: missing content")
    if not messages:
        messages.append("OK prompt: schema looks valid")
    return messages


def iter_query_items(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("data"), list):
            return data["data"]
        return list(data.values())
    return []


def validate_query_inputs(path: Path) -> list[str]:
    messages: list[str] = []
    try:
        data = load_json(path)
    except Exception as exc:
        return [f"ERROR query-inputs: could not parse JSON: {exc}"]
    items = iter_query_items(data)
    if not items:
        return ["ERROR query-inputs: expected a non-empty list, object values, or object with data list"]
    for idx, item in enumerate(items[:20]):
        if not isinstance(item, dict):
            messages.append(f"ERROR query-inputs[{idx}]: item must be an object")
            continue
        if not isinstance(item.get("id"), str):
            messages.append(f"ERROR query-inputs[{idx}]: missing string id")
        if not isinstance(item.get("sentences"), str):
            messages.append(f"ERROR query-inputs[{idx}]: missing string sentences")
    if not messages:
        messages.append(f"OK query-inputs: inspected {min(len(items), 20)} of {len(items)} item(s)")
    return messages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Syphus dependencies, env vars, adapter name, and optional input JSONs without network calls.")
    parser.add_argument("--dataset-name", help="Syphus adapter id, for example video.DenseCaptions")
    parser.add_argument("--prompt-path", help="Optional prompt JSON to validate")
    parser.add_argument("--query-inputs-path", help="Optional query input JSON to validate")
    parser.add_argument("--allow-missing-key-for-local", action="store_true", help="Do not fail when OPENAI_API_KEY is empty and OPENAI_API_BASE is localhost")
    parser.add_argument("--json", action="store_true", help="Emit a JSON report")
    args = parser.parse_args(argv)

    messages: list[dict[str, str]] = []

    for module in ("litellm", "openai"):
        ok, msg = check_import(module)
        messages.append({"level": "OK" if ok else "ERROR", "where": "dependency", "message": msg})

    if args.dataset_name:
        if args.dataset_name in AVAILABLE_DATASETS:
            messages.append({"level": "OK", "where": "dataset-name", "message": f"recognized adapter: {args.dataset_name}"})
        else:
            messages.append({"level": "ERROR", "where": "dataset-name", "message": f"unknown adapter: {args.dataset_name}; expected one of {sorted(AVAILABLE_DATASETS)}"})

    env = {name: os.environ.get(name, DEFAULTS[name]) for name in ENV_VARS}
    for name in ENV_VARS:
        value = os.environ.get(name)
        if value is None:
            level = "WARN"
            msg = f"not set; Syphus source default would be {DEFAULTS[name]!r}"
        elif value == "" and name == "OPENAI_API_KEY":
            level = "WARN"
            msg = "set but empty"
        else:
            level = "OK"
            msg = "set"
        messages.append({"level": level, "where": name, "message": msg})

    base = env["OPENAI_API_BASE"]
    key = env["OPENAI_API_KEY"]
    if not key:
        localhost = base.startswith("http://localhost") or base.startswith("http://127.0.0.1")
        if localhost and args.allow_missing_key_for_local:
            messages.append({"level": "WARN", "where": "OPENAI_API_KEY", "message": "empty key allowed by flag for local endpoint; confirm endpoint policy before running"})
        else:
            messages.append({"level": "ERROR", "where": "OPENAI_API_KEY", "message": "empty API key; remote providers usually require a key"})
    if not env["OPENAI_API_ENGINE"]:
        messages.append({"level": "ERROR", "where": "OPENAI_API_ENGINE", "message": "engine/model/deployment name is empty"})

    if args.prompt_path:
        p = Path(args.prompt_path).expanduser()
        if not p.exists():
            messages.append({"level": "ERROR", "where": "prompt", "message": f"file does not exist: {p}"})
        else:
            for line in validate_prompt(p):
                level, _, message = line.partition(" ")
                messages.append({"level": level.rstrip(":"), "where": "prompt", "message": message})

    if args.query_inputs_path:
        p = Path(args.query_inputs_path).expanduser()
        if not p.exists():
            messages.append({"level": "ERROR", "where": "query-inputs", "message": f"file does not exist: {p}"})
        else:
            for line in validate_query_inputs(p):
                level, _, message = line.partition(" ")
                messages.append({"level": level.rstrip(":"), "where": "query-inputs", "message": message})

    has_error = any(item["level"] == "ERROR" for item in messages)
    if args.json:
        print(json.dumps({"ok": not has_error, "messages": messages}, indent=2))
    else:
        for item in messages:
            print(f"{item['level']:5s} [{item['where']}]: {item['message']}")
        if not has_error:
            print("OK: Syphus preflight completed; no network calls were made")
    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
