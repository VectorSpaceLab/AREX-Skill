#!/usr/bin/env python3
"""Safe top-level inspection for an installed deep-daze runtime.

This helper checks import identity, the `imagine` console entry point, available
CLIP model names, tokenizer shape, and Torch backend status. It never constructs
`Imagine`, never calls `deep_daze.clip.load`, never downloads CLIP checkpoints,
and never generates images.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
from typing import Any, Dict, List, Sequence


def collect() -> Dict[str, Any]:
    report: Dict[str, Any] = {"ok": True, "errors": [], "warnings": []}

    try:
        report["distribution_version"] = metadata.version("deep-daze")
    except metadata.PackageNotFoundError:
        report["ok"] = False
        report["errors"].append("distribution metadata for 'deep-daze' was not found")
        report["distribution_version"] = None

    try:
        deep_daze = importlib.import_module("deep_daze")
        report["exports"] = {
            "DeepDaze": hasattr(deep_daze, "DeepDaze"),
            "Imagine": hasattr(deep_daze, "Imagine"),
        }
        if not all(report["exports"].values()):
            report["ok"] = False
            report["errors"].append("deep_daze imported but did not export both DeepDaze and Imagine")
    except Exception as exc:  # noqa: BLE001 - diagnostics should report import failures concisely.
        report["ok"] = False
        report["errors"].append(f"import deep_daze failed: {exc.__class__.__name__}: {exc}")
        report["exports"] = {"DeepDaze": False, "Imagine": False}

    try:
        clip = importlib.import_module("deep_daze.clip")
        report["clip_models"] = list(clip.available_models())
        report["tokenize_a_house_shape"] = list(clip.tokenize("a house").shape)
    except Exception as exc:  # noqa: BLE001
        report["ok"] = False
        report["errors"].append(f"CLIP/tokenizer inspection failed: {exc.__class__.__name__}: {exc}")
        report["clip_models"] = []
        report["tokenize_a_house_shape"] = None

    try:
        entry_points = metadata.entry_points()
        if hasattr(entry_points, "select"):
            matches = list(entry_points.select(group="console_scripts", name="imagine"))
        else:  # pragma: no cover - compatibility with older importlib.metadata
            matches = [ep for ep in entry_points.get("console_scripts", []) if ep.name == "imagine"]
        report["imagine_entry_points"] = [getattr(ep, "value", "") for ep in matches]
        if "deep_daze.cli:main" not in report["imagine_entry_points"]:
            report["warnings"].append("console script 'imagine' was not found or points somewhere unexpected")
    except Exception as exc:  # noqa: BLE001
        report["warnings"].append(f"console entry-point inspection failed: {exc.__class__.__name__}: {exc}")
        report["imagine_entry_points"] = []

    try:
        torch = importlib.import_module("torch")
        cuda_available = bool(torch.cuda.is_available())
        report["torch"] = {
            "version": getattr(torch, "__version__", None),
            "cuda_version": getattr(torch.version, "cuda", None),
            "cuda_available": cuda_available,
            "cuda_device_count": int(torch.cuda.device_count()),
            "deep_daze_selected_device": "cuda" if cuda_available else "cpu",
            "imagine_default_jit_will_be_disabled": "1.7.1" not in str(getattr(torch, "__version__", "")),
        }
    except Exception as exc:  # noqa: BLE001
        report["ok"] = False
        report["errors"].append(f"torch inspection failed: {exc.__class__.__name__}: {exc}")
        report["torch"] = None

    return report


def print_text(report: Dict[str, Any]) -> None:
    print(f"deep-daze distribution: {report.get('distribution_version')}")
    print(f"exports: {report.get('exports')}")
    print(f"CLIP models: {', '.join(report.get('clip_models') or [])}")
    print(f"tokenize('a house') shape: {report.get('tokenize_a_house_shape')}")
    print(f"imagine entry points: {report.get('imagine_entry_points')}")
    print(f"torch: {report.get('torch')}")
    for warning in report.get("warnings", []):
        print(f"warning: {warning}")
    for error in report.get("errors", []):
        print(f"error: {error}")
    print("status: ok" if report.get("ok") else "status: failed")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safely inspect an installed deep-daze runtime without generation.")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="exit nonzero on warnings as well as errors")
    args = parser.parse_args(argv)

    report = collect()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    if not report.get("ok"):
        return 1
    if args.strict and report.get("warnings"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
