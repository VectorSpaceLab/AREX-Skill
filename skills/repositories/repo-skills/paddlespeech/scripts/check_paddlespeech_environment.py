#!/usr/bin/env python3
"""Safe PaddleSpeech environment checker.

This helper performs imports, metadata lookups, CLI availability checks, and
optional config parsing. It does not download models, run inference, start
servers, or require the original source checkout.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
from pathlib import Path

MODULE_GROUPS = {
    "imports": [
        "paddle",
        "paddlespeech",
        "paddlespeech.cli.base_commands",
        "paddlespeech.resource.resource",
    ],
    "tasks": [
        "paddlespeech.cli.asr.infer",
        "paddlespeech.cli.tts.infer",
        "paddlespeech.cli.text.infer",
        "paddlespeech.cli.vector.infer",
        "paddlespeech.cli.cls.infer",
        "paddlespeech.cli.kws.infer",
        "paddlespeech.cli.ssl.infer",
        "paddlespeech.cli.whisper.infer",
    ],
    "server": [
        "paddlespeech.server.base_commands",
        "paddlespeech.server.bin.paddlespeech_server",
        "paddlespeech.server.bin.paddlespeech_client",
        "paddlespeech.server.utils.config",
    ],
}

DISTRIBUTIONS = [
    "paddlespeech",
    "paddlepaddle",
    "paddlenlp",
    "soundfile",
    "librosa",
    "onnxruntime",
    "fastapi",
    "uvicorn",
    "websockets",
]


def check_modules(groups: list[str]) -> list[dict[str, str]]:
    rows = []
    for group in groups:
        for mod in MODULE_GROUPS[group]:
            try:
                imported = importlib.import_module(mod)
                rows.append({"kind": "module", "name": mod, "status": "ok", "detail": getattr(imported, "__file__", "") or "built-in"})
            except Exception as exc:  # noqa: BLE001
                rows.append({"kind": "module", "name": mod, "status": "fail", "detail": f"{type(exc).__name__}: {exc}"})
    return rows


def check_metadata() -> list[dict[str, str]]:
    rows = []
    for dist in DISTRIBUTIONS:
        try:
            rows.append({"kind": "distribution", "name": dist, "status": "ok", "detail": metadata.version(dist)})
        except metadata.PackageNotFoundError:
            rows.append({"kind": "distribution", "name": dist, "status": "missing", "detail": "not installed"})
    return rows


def check_cli() -> list[dict[str, str]]:
    rows = []
    for exe, args in [
        ("paddlespeech", ["help"]),
        ("paddlespeech_server", ["help"]),
        ("paddlespeech_client", ["help"]),
    ]:
        path = shutil.which(exe)
        if not path:
            rows.append({"kind": "cli", "name": exe, "status": "missing", "detail": "not on PATH"})
            continue
        try:
            proc = subprocess.run([path, *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
            detail = (proc.stdout or proc.stderr).splitlines()[:8]
            rows.append({"kind": "cli", "name": exe, "status": "ok" if proc.returncode == 0 else "fail", "detail": " | ".join(detail)})
        except Exception as exc:  # noqa: BLE001
            rows.append({"kind": "cli", "name": exe, "status": "fail", "detail": f"{type(exc).__name__}: {exc}"})
    return rows


def parse_config(path: Path) -> dict[str, object]:
    import yaml  # imported only when needed
    data = yaml.safe_load(path.read_text())
    return {
        "host": data.get("host"),
        "port": data.get("port"),
        "protocol": data.get("protocol"),
        "engine_list": data.get("engine_list", []),
        "sections": sorted(k for k, v in data.items() if isinstance(v, dict)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe PaddleSpeech import/CLI/config checker")
    parser.add_argument("--check", action="append", choices=["imports", "tasks", "server", "metadata", "cli"], default=[])
    parser.add_argument("--server-config", type=Path, help="Optional PaddleSpeech server YAML to summarize")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args()

    checks = args.check or ["imports", "metadata", "cli"]
    rows: list[dict[str, str]] = []
    module_groups = [c for c in checks if c in MODULE_GROUPS]
    if module_groups:
        rows.extend(check_modules(module_groups))
    if "metadata" in checks:
        rows.extend(check_metadata())
    if "cli" in checks:
        rows.extend(check_cli())

    result: dict[str, object] = {"python": sys.version.split()[0], "checks": rows}
    if args.server_config:
        try:
            result["server_config"] = parse_config(args.server_config)
        except Exception as exc:  # noqa: BLE001
            result["server_config_error"] = f"{type(exc).__name__}: {exc}"

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Python: {result['python']}")
        for row in rows:
            print(f"[{row['status']}] {row['kind']} {row['name']}: {row['detail']}")
        if "server_config" in result:
            print("Server config:", json.dumps(result["server_config"], ensure_ascii=False))
        if "server_config_error" in result:
            print("Server config error:", result["server_config_error"])

    return 1 if any(row["status"] == "fail" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
