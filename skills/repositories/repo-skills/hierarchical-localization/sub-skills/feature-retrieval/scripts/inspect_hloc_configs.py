#!/usr/bin/env python3
"""Inspect installed hloc feature/retrieval/matching config dictionaries.

This helper is intentionally read-only: it imports configuration dictionaries and
reports optional Torch/CUDA status, but it does not instantiate neural models,
load images, download weights, or require a source checkout.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from typing import Any, Dict, Iterable, Mapping

SECTION_CHOICES = ("all", "extract", "match", "dense", "torch")


class HlocInspectionError(RuntimeError):
    """Raised for expected import/inspection failures with user-facing text."""


def _jsonable(value: Any) -> Any:
    """Return a JSON-compatible copy of common config values."""
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _dist_version() -> str | None:
    """Best-effort distribution version without exposing installation paths."""
    for dist_name in ("hloc", "hierarchical-localization", "Hierarchical-Localization"):
        try:
            return metadata.version(dist_name)
        except metadata.PackageNotFoundError:
            continue
    return None


def _import_confs(module_name: str) -> Dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise HlocInspectionError(
            "Could not import installed hloc modules while reading config "
            f"dictionaries ({exc}). Install hloc and its base import "
            "dependencies in the active Python environment, then retry. "
            "This helper only inspects configs and does not download model weights."
        ) from None
    except Exception as exc:  # keep output concise and traceback-free
        raise HlocInspectionError(
            "Importing hloc config modules failed before inspection completed "
            f"({type(exc).__name__}: {exc}). Check the active environment's hloc "
            "installation and optional dependency set."
        ) from None

    confs = getattr(module, "confs", None)
    if not isinstance(confs, Mapping):
        raise HlocInspectionError(f"{module_name} does not expose a mapping named 'confs'.")
    return {str(name): _jsonable(conf) for name, conf in confs.items()}


def _torch_status() -> Dict[str, Any]:
    try:
        torch = importlib.import_module("torch")
    except ImportError as exc:
        return {"available": False, "error": str(exc)}
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    status: Dict[str, Any] = {
        "available": True,
        "version": getattr(torch, "__version__", None),
    }
    try:
        cuda_available = bool(torch.cuda.is_available())
        status["cuda_available"] = cuda_available
        status["cuda_device_count"] = int(torch.cuda.device_count()) if cuda_available else 0
        if cuda_available:
            status["cuda_devices"] = [
                torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
            ]
    except Exception as exc:
        status["cuda_error"] = f"{type(exc).__name__}: {exc}"
    return status


def _selected_sections(section: str) -> Iterable[str]:
    if section == "all":
        return ("extract", "match", "dense", "torch")
    return (section,)


def inspect(section: str) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "status": "ok",
        "package": {"version": _dist_version()},
        "sections": {},
    }
    for item in _selected_sections(section):
        if item == "extract":
            payload["sections"][item] = _import_confs("hloc.extract_features")
        elif item == "match":
            payload["sections"][item] = _import_confs("hloc.match_features")
        elif item == "dense":
            payload["sections"][item] = _import_confs("hloc.match_dense")
        elif item == "torch":
            payload["sections"][item] = _torch_status()
        else:  # argparse should prevent this
            raise HlocInspectionError(f"Unknown section: {item}")
    return payload


def _print_config_section(title: str, confs: Mapping[str, Any]) -> None:
    print(f"\n[{title}]")
    if not confs:
        print("  <none>")
        return
    for name in sorted(confs):
        conf = confs[name]
        output = conf.get("output", "<no output stem>") if isinstance(conf, Mapping) else "<unknown>"
        print(f"  {name}")
        print(f"    output: {output}")
        if isinstance(conf, Mapping):
            model = conf.get("model")
            preprocessing = conf.get("preprocessing")
            extra = {
                k: v
                for k, v in conf.items()
                if k not in {"output", "model", "preprocessing"}
            }
            if model is not None:
                print("    model: " + json.dumps(model, sort_keys=True))
            if preprocessing is not None:
                print("    preprocessing: " + json.dumps(preprocessing, sort_keys=True))
            if extra:
                print("    extra: " + json.dumps(extra, sort_keys=True))


def print_text(payload: Mapping[str, Any]) -> None:
    version = payload.get("package", {}).get("version") if isinstance(payload.get("package"), Mapping) else None
    print("hloc config inspection")
    print(f"package_version: {version or 'unknown'}")
    sections = payload.get("sections", {})
    if not isinstance(sections, Mapping):
        return
    for name in ("extract", "match", "dense"):
        if name in sections:
            _print_config_section(name, sections[name])
    if "torch" in sections:
        print("\n[torch]")
        print(json.dumps(sections["torch"], indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect installed hloc extract/match/dense config dictionaries and "
            "optional Torch/CUDA status without running models."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="emit machine-readable JSON instead of text",
    )
    parser.add_argument(
        "--section",
        choices=SECTION_CHOICES,
        default="all",
        help="which section to inspect (default: all)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = inspect(args.section)
    except HlocInspectionError as exc:
        if args.as_json:
            print(json.dumps({"status": "error", "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
