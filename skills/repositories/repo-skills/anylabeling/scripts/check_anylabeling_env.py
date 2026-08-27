#!/usr/bin/env python3
"""Safe AnyLabeling installed-package diagnostics.

This script performs read-only checks. It does not launch the GUI event loop,
download models, mutate user config, or remove cache files.

Examples:
  python check_anylabeling_env.py
  python check_anylabeling_env.py --cli-help --startup-import --model-cache
  python check_anylabeling_env.py --json
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.resources as resources
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def add_check(report: dict[str, Any], name: str, ok: bool, detail: Any) -> None:
    report.setdefault("checks", []).append({"name": name, "ok": ok, "detail": detail})
    if not ok:
        report["ok"] = False


def check_distribution(report: dict[str, Any]) -> None:
    try:
        version = metadata.version("anylabeling")
        dist_meta = metadata.metadata("anylabeling")
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        add_check(report, "distribution", False, str(exc))
        return
    add_check(report, "distribution", True, {"name": dist_meta.get("Name"), "version": version})


def check_import(report: dict[str, Any]) -> None:
    try:
        pkg = importlib.import_module("anylabeling")
    except Exception as exc:  # noqa: BLE001
        add_check(report, "import anylabeling", False, str(exc))
        return
    add_check(report, "import anylabeling", True, {"version": getattr(pkg, "__version__", None)})


def check_cli_help(report: dict[str, Any], timeout: int) -> None:
    try:
        proc = subprocess.run(
            ["anylabeling", "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        add_check(report, "cli help", False, "console command 'anylabeling' was not found on PATH")
        return
    except Exception as exc:  # noqa: BLE001
        add_check(report, "cli help", False, str(exc))
        return
    text = (proc.stdout or proc.stderr).strip()
    ok = proc.returncode == 0 and "--config" in text and "--theme" in text
    add_check(report, "cli help", ok, {"exit_code": proc.returncode, "first_line": text.splitlines()[0] if text else ""})


def check_startup_import(report: dict[str, Any]) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        importlib.import_module("anylabeling.views.labeling.label_widget")
        importlib.import_module("anylabeling.app")
    except Exception as exc:  # noqa: BLE001
        add_check(report, "startup import", False, str(exc))
        return
    add_check(report, "startup import", True, "label_widget and app imported")


def check_config(report: dict[str, Any]) -> None:
    try:
        from anylabeling.config import get_config

        cfg = get_config(None, {})
    except Exception as exc:  # noqa: BLE001
        add_check(report, "default config", False, str(exc))
        return
    add_check(
        report,
        "default config",
        True,
        {
            "language": cfg.get("language"),
            "theme": cfg.get("theme"),
            "auto_save": cfg.get("auto_save"),
            "shortcut_count": len(cfg.get("shortcuts", {})),
        },
    )


def check_model_catalog(report: dict[str, Any]) -> None:
    try:
        import yaml  # type: ignore
        from anylabeling.configs import auto_labeling

        text = resources.files(auto_labeling).joinpath("models.yaml").read_text(encoding="utf-8")
        models = yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001
        add_check(report, "model catalog", False, str(exc))
        return
    if not isinstance(models, list):
        add_check(report, "model catalog", False, "models.yaml is not a list")
        return
    type_counts: dict[str, int] = {}
    sample_names = []
    errors = []
    for item in models:
        if not isinstance(item, dict):
            errors.append("non-mapping catalog entry")
            continue
        model_type = str(item.get("type"))
        type_counts[model_type] = type_counts.get(model_type, 0) + 1
        if len(sample_names) < 8:
            sample_names.append(item.get("name"))
        for field in ("name", "display_name", "download_url", "type"):
            if field not in item:
                errors.append(f"entry {item.get('name')!r} missing {field}")
    add_check(report, "model catalog", not errors, {"count": len(models), "type_counts": type_counts, "samples": sample_names, "errors": errors})


def check_registry(report: dict[str, Any]) -> None:
    try:
        import anylabeling.services.auto_labeling as _auto_labeling  # noqa: F401
        from anylabeling.services.auto_labeling import ModelRegistry

        names = sorted(ModelRegistry.list_models())
    except Exception as exc:  # noqa: BLE001
        add_check(report, "model registry", False, str(exc))
        return
    expected = {"segment_anything", "yolov5", "yolov8"}
    add_check(report, "model registry", expected.issubset(set(names)), names)


def check_onnxruntime(report: dict[str, Any]) -> None:
    try:
        import onnxruntime as ort  # type: ignore
    except Exception as exc:  # noqa: BLE001
        add_check(report, "onnxruntime", False, str(exc))
        return
    add_check(report, "onnxruntime", True, {"version": getattr(ort, "__version__", None), "providers": ort.get_available_providers()})


def check_model_cache(report: dict[str, Any], cache_root: str) -> None:
    root = Path(cache_root).expanduser()
    if not root.exists():
        add_check(report, "model cache", True, {"exists": False, "path": str(root)})
        return
    entries = []
    for child in sorted(root.iterdir())[:50]:
        if child.is_dir():
            cfg = child / "config.yaml"
            entries.append({"name": child.name, "has_config": cfg.is_file()})
    add_check(report, "model cache", True, {"exists": True, "path": str(root), "entry_count_sampled": len(entries), "entries": entries})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli-help", action="store_true", help="run 'anylabeling --help'")
    parser.add_argument("--startup-import", action="store_true", help="import UI startup modules with QT_QPA_PLATFORM defaulting to offscreen")
    parser.add_argument("--model-cache", action="store_true", help="inspect local model-cache directory names without downloading")
    parser.add_argument("--model-cache-root", default="~/anylabeling_data/models", help="model cache root to inspect with --model-cache")
    parser.add_argument("--skip-config", action="store_true", help="skip default config load")
    parser.add_argument("--timeout", type=int, default=20, help="timeout in seconds for CLI subprocess checks")
    parser.add_argument("--json", action="store_true", help="emit JSON report")
    args = parser.parse_args(argv)

    report: dict[str, Any] = {"ok": True, "python": sys.executable, "checks": []}
    check_distribution(report)
    check_import(report)
    if not args.skip_config:
        check_config(report)
    check_registry(report)
    check_model_catalog(report)
    check_onnxruntime(report)
    if args.cli_help:
        check_cli_help(report, args.timeout)
    if args.startup_import:
        check_startup_import(report)
    if args.model_cache:
        check_model_cache(report, args.model_cache_root)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("AnyLabeling environment check")
        for check in report["checks"]:
            status = "OK" if check["ok"] else "FAIL"
            print(f"{status} {check['name']}: {check['detail']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
