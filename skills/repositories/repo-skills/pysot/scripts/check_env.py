#!/usr/bin/env python3
"""Safe PySOT environment/import preflight.

This helper checks whether a Python process can import PySOT's public modules,
the toolkit distribution, the legacy region extension, and optionally a config
file. It is intentionally read-only: it does not download models/data, open
video devices, load snapshots, run tracking, train, or evaluate benchmarks.

Example:
    python scripts/check_env.py --repo-root /path/to/pysot --config /path/to/config.yaml
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from pathlib import Path
from typing import Any


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check PySOT importability and safe config/model smoke prerequisites.")
    parser.add_argument(
        "--repo-root",
        help=(
            "Optional PySOT checkout root to prepend to sys.path when the `pysot` package "
            "is not installed as an importable module."
        ),
    )
    parser.add_argument("--config", help="Optional PySOT YAML config to load with cfg.merge_from_file.")
    parser.add_argument(
        "--model-smoke",
        action="store_true",
        help="After loading --config, instantiate ModelBuilder() and build_tracker(model) without loading weights.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary.")
    return parser.parse_args(argv)


def add_repo_root(repo_root: str | None, errors: list[str]) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        errors.append(f"repo root does not exist: {root}")
        return
    if not (root / "pysot").is_dir() or not (root / "toolkit").is_dir():
        errors.append(f"repo root should contain pysot/ and toolkit/: {root}")
        return
    sys.path.insert(0, str(root))


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None
    except Exception as exc:
        return f"error: {type(exc).__name__}: {exc}"


def import_module(name: str) -> tuple[bool, str]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    location = getattr(module, "__file__", "built-in")
    return True, str(location)


def load_config(config_path: str | None, errors: list[str], warnings: list[str], summary: dict[str, Any]) -> Any | None:
    if not config_path:
        return None
    path = Path(config_path).expanduser().resolve()
    if not path.is_file():
        errors.append(f"config file does not exist: {path}")
        return None
    try:
        from pysot.core.config import cfg
    except Exception as exc:
        errors.append(f"could not import pysot.core.config.cfg: {type(exc).__name__}: {exc}")
        return None
    try:
        cfg.merge_from_file(str(path))
    except Exception as exc:
        errors.append(f"cfg.merge_from_file failed: {type(exc).__name__}: {exc}")
        return None
    summary["config"] = {
        "meta_arc": str(getattr(cfg, "META_ARC", "")),
        "tracker_type": str(cfg.TRACK.TYPE),
        "backbone_type": str(cfg.BACKBONE.TYPE),
        "cuda_flag": bool(cfg.CUDA),
    }
    if cfg.ANCHOR.ANCHOR_NUM != len(list(cfg.ANCHOR.RATIOS)) * len(list(cfg.ANCHOR.SCALES)):
        errors.append("ANCHOR.ANCHOR_NUM does not match len(RATIOS) * len(SCALES)")
    if cfg.TRACK.TYPE not in {"SiamRPNTracker", "SiamMaskTracker", "SiamRPNLTTracker"}:
        errors.append(f"unsupported TRACK.TYPE={cfg.TRACK.TYPE!r}")
    if cfg.CUDA:
        warnings.append("cfg.CUDA is true; safe checks do not prove CUDA benchmark/training readiness")
    return cfg


def model_smoke(enabled: bool, cfg: Any | None, errors: list[str], summary: dict[str, Any]) -> None:
    if not enabled:
        return
    if cfg is None:
        errors.append("--model-smoke requires --config so PySOT component choices are loaded first")
        return
    try:
        from pysot.models.model_builder import ModelBuilder
        from pysot.tracker.tracker_builder import build_tracker
    except Exception as exc:
        errors.append(f"could not import model/tracker builders: {type(exc).__name__}: {exc}")
        return
    try:
        cfg.CUDA = False
        model = ModelBuilder()
        tracker = build_tracker(model)
    except Exception as exc:
        errors.append(f"ModelBuilder/build_tracker smoke failed: {type(exc).__name__}: {exc}")
        return
    summary["model_smoke"] = {"model": type(model).__name__, "tracker": type(tracker).__name__}


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []
    summary: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distributions": {name: dist_version(name) for name in ["toolkit", "torch", "opencv-python", "yacs", "Cython", "numpy"]},
        "imports": {},
    }

    add_repo_root(args.repo_root, errors)

    for module_name in [
        "pysot",
        "pysot.core.config",
        "pysot.models.model_builder",
        "pysot.tracker.tracker_builder",
        "toolkit",
        "toolkit.datasets",
        "toolkit.evaluation",
        "toolkit.utils.region",
    ]:
        ok, detail = import_module(module_name)
        summary["imports"][module_name] = {"ok": ok, "detail": detail}
        if not ok:
            errors.append(f"import failed for {module_name}: {detail}")

    cfg = load_config(args.config, errors, warnings, summary)
    model_smoke(args.model_smoke, cfg, errors, summary)

    summary["warnings"] = warnings
    summary["errors"] = errors
    summary["ok"] = not errors

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("PySOT environment check")
        print(f"  Python: {summary['python']}")
        for name, version in summary["distributions"].items():
            print(f"  distribution {name}: {version or 'not found'}")
        for name, result in summary["imports"].items():
            print(f"  import {name}: {'OK' if result['ok'] else 'FAIL'}")
        if "config" in summary:
            cfgs = summary["config"]
            print(f"  config: META_ARC={cfgs['meta_arc']} TRACK.TYPE={cfgs['tracker_type']} BACKBONE.TYPE={cfgs['backbone_type']}")
        if "model_smoke" in summary:
            ms = summary["model_smoke"]
            print(f"  model smoke: {ms['model']} -> {ms['tracker']}")
        for warning in warnings:
            print(f"  warning: {warning}")
        for error in errors:
            print(f"  error: {error}")
        print("  result:", "PASS" if not errors else "FAIL")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
