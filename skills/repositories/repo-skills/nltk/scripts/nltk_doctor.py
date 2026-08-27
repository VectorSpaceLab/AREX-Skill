#!/usr/bin/env python3
"""Read-only NLTK package/data/CLI diagnostic.

By default this script imports NLTK, reports version and data paths, checks the
console/downloader help commands, and probes targeted NLTK data resources. It
calls nltk.download() only for package IDs explicitly supplied with --download.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

RESOURCE_PROBES: dict[str, list[str]] = {
    "punkt_tab": ["tokenizers/punkt_tab/english/", "tokenizers/punkt_tab.zip/punkt_tab/english/"],
    "averaged_perceptron_tagger_eng": ["taggers/averaged_perceptron_tagger_eng/", "taggers/averaged_perceptron_tagger_eng.zip/averaged_perceptron_tagger_eng/"],
    "averaged_perceptron_tagger_rus": ["taggers/averaged_perceptron_tagger_rus/", "taggers/averaged_perceptron_tagger_rus.zip/averaged_perceptron_tagger_rus/"],
    "universal_tagset": ["taggers/universal_tagset/", "taggers/universal_tagset.zip/universal_tagset/"],
    "wordnet": ["corpora/wordnet/", "corpora/wordnet.zip/wordnet/"],
    "omw-2.0": ["corpora/omw-2.0/", "corpora/omw-2.0.zip/omw-2.0/"],
    "vader_lexicon": ["sentiment/vader_lexicon.zip/vader_lexicon/vader_lexicon.txt", "sentiment/vader_lexicon/vader_lexicon.txt"],
    "brown": ["corpora/brown/", "corpora/brown.zip/brown/"],
    "treebank": ["corpora/treebank/combined/", "corpora/treebank.zip/treebank/combined/", "corpora/treebank/", "corpora/treebank.zip/treebank/"],
    "reuters": ["corpora/reuters/", "corpora/reuters.zip/reuters/"],
    "comtrans": ["corpora/comtrans/", "corpora/comtrans.zip/comtrans/"],
}


def _console_command() -> str | None:
    found = shutil.which("nltk")
    if found:
        return found
    sibling = Path(sys.executable).with_name("nltk")
    if sibling.exists():
        return str(sibling)
    sibling_exe = sibling.with_suffix(".exe")
    if sibling_exe.exists():
        return str(sibling_exe)
    return None


def _run_help(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=20, check=False)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "command": command}
    output = (result.stdout + result.stderr).strip()
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "command": command,
        "first_lines": output.splitlines()[:12],
    }


def _apply_data_dirs(nltk, data_dirs: list[str]) -> None:
    for data_dir in reversed(data_dirs):
        expanded = os.path.abspath(os.path.expanduser(data_dir))
        if expanded not in nltk.data.path:
            nltk.data.path.insert(0, expanded)


def _probe(nltk, package: str) -> dict[str, Any]:
    probes = RESOURCE_PROBES.get(package, [f"corpora/{package}/", f"corpora/{package}.zip/{package}/"])
    errors: list[str] = []
    for resource in probes:
        try:
            ptr = nltk.data.find(resource)
        except Exception as exc:
            errors.append(f"{resource}: {type(exc).__name__}: {str(exc).strip().splitlines()[0] if str(exc).strip() else exc}")
            continue
        return {"present": True, "matched": resource, "pointer_type": type(ptr).__name__, "pointer": str(ptr)}
    return {"present": False, "probes": probes, "errors": errors[-3:]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Diagnose NLTK import, CLI, and targeted data resources.")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--data-dir", action="append", default=[], help="top-level nltk_data directory to prepend before probing; repeatable")
    parser.add_argument("--package", action="append", default=[], help="data package/resource group to probe; repeatable")
    parser.add_argument("--download", action="append", default=[], help="explicit package ID to download before probing; repeatable")
    parser.add_argument("--download-dir", help="directory passed to nltk.download for --download packages")
    parser.add_argument("--quiet-download", action="store_true", help="pass quiet=True for explicit downloads")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        import nltk
    except Exception as exc:
        print(f"nltk_doctor: FAIL import nltk: {exc}", file=sys.stderr)
        return 3

    _apply_data_dirs(nltk, args.data_dir)

    downloads: dict[str, bool] = {}
    for package in args.download:
        try:
            downloads[package] = bool(nltk.download(package, download_dir=args.download_dir, quiet=args.quiet_download, halt_on_error=True))
        except Exception:
            downloads[package] = False

    packages = args.package or [
        "punkt_tab",
        "averaged_perceptron_tagger_eng",
        "wordnet",
        "vader_lexicon",
        "universal_tagset",
    ]
    if args.download_dir:
        _apply_data_dirs(nltk, [args.download_dir])

    console = _console_command()
    cli_help = _run_help([console, "--help"]) if console else {"ok": False, "error": "nltk console script not found"}
    tokenize_help = _run_help([console, "tokenize", "--help"]) if console else {"ok": False, "error": "nltk console script not found"}
    downloader_help = _run_help([sys.executable, "-m", "nltk.downloader", "--help"])

    payload = {
        "status": "ok",
        "python": platform.python_version(),
        "executable": sys.executable,
        "nltk_version": getattr(nltk, "__version__", "unknown"),
        "nltk_data_env": os.environ.get("NLTK_DATA"),
        "nltk_data_path": list(nltk.data.path),
        "downloads_requested": args.download,
        "download_results": downloads,
        "console_command": console,
        "cli_help": cli_help,
        "tokenize_help": tokenize_help,
        "downloader_help": downloader_help,
        "resource_checks": {package: _probe(nltk, package) for package in packages},
    }
    if downloads and not all(downloads.values()):
        payload["status"] = "download_failed"

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"NLTK {payload['nltk_version']} on Python {payload['python']}")
        print(f"NLTK_DATA={payload['nltk_data_env']}")
        print("nltk.data.path:")
        for item in payload["nltk_data_path"]:
            print(f"  - {item}")
        print(f"nltk console: {console or 'not found'}")
        print(f"CLI help: {'ok' if cli_help.get('ok') else 'failed'}")
        print(f"tokenize help: {'ok' if tokenize_help.get('ok') else 'failed'}")
        print(f"downloader help: {'ok' if downloader_help.get('ok') else 'failed'}")
        if downloads:
            print("downloads:")
            for package, ok in downloads.items():
                print(f"  - {package}: {'ok' if ok else 'failed'}")
        print("resources:")
        for package, result in payload["resource_checks"].items():
            print(f"  - {package}: {'present' if result.get('present') else 'missing'}")
            if result.get("matched"):
                print(f"      matched: {result['matched']}")
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
