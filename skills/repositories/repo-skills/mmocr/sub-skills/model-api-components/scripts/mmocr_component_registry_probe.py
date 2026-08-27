#!/usr/bin/env python3
"""Probe MMOCR component registries and dictionary files.

This helper is intentionally read-only. It does not require an MMOCR source
checkout; it inspects the MMOCR package importable in the active Python
environment and, when requested, a caller-provided dictionary directory.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

REGISTRY_NAMES = [
    "RUNNERS",
    "RUNNER_CONSTRUCTORS",
    "LOOPS",
    "HOOKS",
    "DATASETS",
    "DATA_SAMPLERS",
    "TRANSFORMS",
    "MODELS",
    "MODEL_WRAPPERS",
    "WEIGHT_INITIALIZERS",
    "OPTIMIZERS",
    "OPTIM_WRAPPERS",
    "OPTIM_WRAPPER_CONSTRUCTORS",
    "PARAM_SCHEDULERS",
    "METRICS",
    "EVALUATOR",
    "TASK_UTILS",
    "VISUALIZERS",
    "VISBACKENDS",
    "LOG_PROCESSORS",
    "DATA_OBTAINERS",
    "DATA_GATHERERS",
    "DATA_PARSERS",
    "DATA_PACKERS",
    "DATA_DUMPERS",
    "CFG_GENERATORS",
]

DATA_SAMPLE_NAMES = [
    "TextDetDataSample",
    "TextRecogDataSample",
    "KIEDataSample",
    "TextSpottingDataSample",
]


def _safe_registry_count(registry: Any) -> int | None:
    module_dict = getattr(registry, "module_dict", None)
    if module_dict is None:
        return None
    try:
        return len(module_dict)
    except TypeError:
        return None


def _registry_preview(registry: Any, limit: int) -> List[str]:
    module_dict = getattr(registry, "module_dict", None)
    if not module_dict:
        return []
    try:
        return sorted(str(key) for key in module_dict.keys())[:limit]
    except Exception:
        return []


def _probe_mmocr(register_all: bool, preview_limit: int) -> Tuple[Dict[str, Any], List[str]]:
    warnings: List[str] = []
    result: Dict[str, Any] = {
        "mmocr_imported": False,
        "mmocr_version": None,
        "register_all_modules_called": False,
        "registries": {},
        "data_samples": {},
    }

    try:
        import mmocr  # type: ignore
        from mmocr import registry as mmocr_registry  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Failed to import MMOCR. Install MMOCR with compatible OpenMMLab "
            "dependencies, then rerun this probe. Original error: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    result["mmocr_imported"] = True
    result["mmocr_version"] = getattr(mmocr, "__version__", None)

    if register_all:
        try:
            from mmocr.utils import register_all_modules  # type: ignore

            register_all_modules(init_default_scope=False)
            result["register_all_modules_called"] = True
        except Exception as exc:  # pragma: no cover - dependency/project dependent
            warnings.append(
                "register_all_modules(init_default_scope=False) failed: "
                f"{type(exc).__name__}: {exc}"
            )

    for name in REGISTRY_NAMES:
        registry = getattr(mmocr_registry, name, None)
        if registry is None:
            result["registries"][name] = {"available": False}
            continue
        result["registries"][name] = {
            "available": True,
            "name": getattr(registry, "name", None),
            "scope": getattr(registry, "scope", None),
            "count": _safe_registry_count(registry),
            "preview": _registry_preview(registry, preview_limit),
        }

    try:
        import mmocr.structures as structures  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        warnings.append(
            "Failed to import mmocr.structures: " f"{type(exc).__name__}: {exc}"
        )
    else:
        for name in DATA_SAMPLE_NAMES:
            cls = getattr(structures, name, None)
            result["data_samples"][name] = {
                "available": cls is not None,
                "module": getattr(cls, "__module__", None) if cls is not None else None,
            }

    return result, warnings


def _read_dictionary(path: Path) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "file": path.name,
        "characters": 0,
        "blank_lines": 0,
        "invalid_multichar_lines": [],
        "duplicates": [],
    }
    seen: Dict[str, int] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    for line_number, raw_line in enumerate(lines, start=1):
        char = raw_line.rstrip("\r\n")
        if char == "":
            info["blank_lines"] += 1
            continue
        if len(char) != 1:
            info["invalid_multichar_lines"].append(line_number)
        if char in seen:
            info["duplicates"].append({"character": char, "first_line": seen[char], "line": line_number})
        else:
            seen[char] = line_number
        info["characters"] += 1
    return info


def _list_dicts(directory: str) -> List[Dict[str, Any]]:
    root = Path(directory).expanduser()
    if not root.exists():
        raise FileNotFoundError(f"Dictionary directory does not exist: {directory}")
    if not root.is_dir():
        raise NotADirectoryError(f"Dictionary path is not a directory: {directory}")
    return [_read_dictionary(path) for path in sorted(root.glob("*.txt"))]


def _print_text(result: Dict[str, Any], warnings: Iterable[str]) -> None:
    print("MMOCR component registry probe")
    print(f"mmocr_imported: {result.get('mmocr_imported')}")
    print(f"mmocr_version: {result.get('mmocr_version')}")
    print(f"register_all_modules_called: {result.get('register_all_modules_called')}")

    if result.get("registries"):
        print("\nRegistries:")
        for name, info in result["registries"].items():
            if not info.get("available"):
                print(f"- {name}: unavailable")
                continue
            print(
                f"- {name}: registry_name={info.get('name')!r}, "
                f"scope={info.get('scope')!r}, count={info.get('count')}"
            )
            preview = info.get("preview") or []
            if preview:
                print(f"  preview: {', '.join(preview)}")

    if result.get("data_samples"):
        print("\nDataSample classes:")
        for name, info in result["data_samples"].items():
            print(f"- {name}: available={info.get('available')}, module={info.get('module')}")

    if "dictionaries" in result:
        print("\nDictionary files:")
        dictionaries = result["dictionaries"]
        if not dictionaries:
            print("- none found")
        for info in dictionaries:
            problems = []
            if info["invalid_multichar_lines"]:
                problems.append(f"invalid_multichar_lines={info['invalid_multichar_lines']}")
            if info["duplicates"]:
                dup_chars = [entry["character"] for entry in info["duplicates"]]
                problems.append(f"duplicates={dup_chars}")
            suffix = f" ({'; '.join(problems)})" if problems else ""
            print(
                f"- {info['file']}: characters={info['characters']}, "
                f"blank_lines={info['blank_lines']}{suffix}"
            )

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-register-all",
        action="store_true",
        help="Do not call mmocr.utils.register_all_modules before counting registries.",
    )
    parser.add_argument(
        "--preview-limit",
        type=int,
        default=12,
        help="Maximum registered names to preview per registry.",
    )
    parser.add_argument(
        "--list-dicts",
        metavar="DIR",
        help="List and validate .txt dictionary files from this directory.",
    )
    parser.add_argument(
        "--only-list-dicts",
        action="store_true",
        help="List dictionary files without importing MMOCR.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    warnings: List[str] = []
    result: Dict[str, Any] = {}

    if not args.only_list_dicts:
        try:
            result, warnings = _probe_mmocr(
                register_all=not args.no_register_all,
                preview_limit=max(args.preview_limit, 0),
            )
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            if not args.list_dicts:
                return 2
            warnings.append(str(exc))
            result = {
                "mmocr_imported": False,
                "registries": {},
                "data_samples": {},
            }

    if args.list_dicts:
        try:
            result["dictionaries"] = _list_dicts(args.list_dicts)
        except Exception as exc:
            print(f"Failed to list dictionaries: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 3

    if args.json:
        print(json.dumps({"result": result, "warnings": warnings}, indent=2, sort_keys=True))
    else:
        _print_text(result, warnings)

    missing_samples = [
        name
        for name, info in result.get("data_samples", {}).items()
        if not info.get("available")
    ]
    return 1 if missing_samples else 0


if __name__ == "__main__":
    raise SystemExit(main())
