#!/usr/bin/env python3
"""Check an installed Fengshenbang-LM/Fengshen package without running models."""
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys

MODULES = [
    "fengshen",
    "fengshen.cli.fengshen_pipeline",
    "fengshen.pipelines.text_classification",
    "fengshen.pipelines.sequence_tagging",
    "fengshen.metric.utils_ner",
    "fengshen.models.model_utils",
]


def try_import(name: str) -> dict:
    try:
        module = importlib.import_module(name)
        return {"module": name, "ok": True, "file": getattr(module, "__file__", None)}
    except Exception as exc:
        return {"module": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Import-check Fengshen package and optionally inspect CLI help.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    parser.add_argument("--check-cli-help", action="store_true", help="Run fengshen-pipeline text_classification predict --help.")
    args = parser.parse_args()

    results = [try_import(name) for name in MODULES]
    cli = None
    if args.check_cli_help:
        exe = shutil.which("fengshen-pipeline")
        if not exe:
            cli = {"ok": False, "error": "fengshen-pipeline not found on PATH"}
        else:
            proc = subprocess.run([exe, "text_classification", "predict", "--help"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            cli = {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout_head": proc.stdout.splitlines()[:12], "stderr_head": proc.stderr.splitlines()[:12]}

    report = {"python": sys.version, "imports": results, "cli_help": cli}
    ok = all(item["ok"] for item in results) and (cli is None or cli.get("ok"))
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for item in results:
            print(f"{item['module']}: {'OK' if item['ok'] else 'FAIL'}")
            if not item["ok"]:
                print(f"  {item['error']}")
        if cli is not None:
            print(f"cli_help: {'OK' if cli.get('ok') else 'FAIL'}")
            if not cli.get("ok"):
                print(f"  {cli.get('error') or cli.get('stderr_head')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
