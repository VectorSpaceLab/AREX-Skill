#!/usr/bin/env python3
"""Inspect the installed RecBole model registry.

This helper is intentionally read-only. It imports the active RecBole package,
resolves model names through recbole.utils.get_model, and reports package-level
class/trainer/property information without relying on a source checkout.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _version_from_metadata() -> Optional[str]:
    try:
        from importlib import metadata
    except Exception:  # pragma: no cover - old Python fallback only
        try:
            import importlib_metadata as metadata  # type: ignore
        except Exception:
            return None
    for dist_name in ("recbole", "RecBole"):
        try:
            return metadata.version(dist_name)
        except Exception:
            continue
    return None


def _import_recbole() -> Tuple[Any, Any, Any, Optional[str]]:
    version = _version_from_metadata()
    try:
        import recbole  # type: ignore
        from recbole.utils import get_model, get_trainer  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "Could not import RecBole and recbole.utils.get_model. "
            "Install RecBole and its runtime dependencies in the active environment. "
            f"Original error: {type(exc).__name__}: {exc}"
        ) from exc
    version = getattr(recbole, "__version__", None) or version
    return recbole, get_model, get_trainer, version


def _enum_name(value: Any) -> Optional[str]:
    if value is None:
        return None
    name = getattr(value, "name", None)
    if name is not None:
        return str(name)
    return str(value)


def _property_candidates(model_name: str, class_name: Optional[str]) -> List[str]:
    raw = [model_name]
    if class_name:
        raw.append(class_name)
    raw.extend([model_name.lower()])
    if class_name:
        raw.append(class_name.lower())
    seen = set()
    out: List[str] = []
    for stem in raw:
        filename = stem if stem.endswith(".yaml") else f"{stem}.yaml"
        if filename not in seen:
            seen.add(filename)
            out.append(filename)
    return out


def _package_properties_dir(recbole_module: Any) -> Optional[Path]:
    package_file = getattr(recbole_module, "__file__", None)
    if not package_file:
        return None
    candidate = Path(package_file).resolve().parent / "properties" / "model"
    return candidate if candidate.is_dir() else None


def _find_property_yaml(
    candidates: Iterable[str], properties_dir: Optional[Path], recbole_module: Any
) -> Tuple[Optional[str], List[str], str]:
    candidate_list = list(candidates)
    search_dir = properties_dir if properties_dir else _package_properties_dir(recbole_module)
    source = "provided" if properties_dir else "installed-package"
    if search_dir and search_dir.is_dir():
        for filename in candidate_list:
            if (search_dir / filename).is_file():
                return filename, candidate_list, source
    return None, candidate_list, source


def _constructor_signature(cls: Any) -> Optional[str]:
    try:
        return str(inspect.signature(cls.__init__))
    except Exception:
        try:
            return str(inspect.signature(cls))
        except Exception:
            return None


def _mro(cls: Any) -> List[str]:
    try:
        return [c.__name__ for c in cls.__mro__ if c is not object]
    except Exception:
        return []


def inspect_one(
    model_name: str,
    recbole_module: Any,
    get_model: Any,
    get_trainer: Any,
    properties_dir: Optional[Path],
    details: bool,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {"query": model_name, "ok": False}
    try:
        cls = get_model(model_name)
    except Exception as exc:
        result.update(
            {
                "error_type": type(exc).__name__,
                "error": str(exc),
                "property_candidates": _property_candidates(model_name, None),
            }
        )
        return result

    class_name = getattr(cls, "__name__", str(cls))
    model_type = getattr(cls, "type", None)
    input_type = getattr(cls, "input_type", None)
    prop, candidates, prop_source = _find_property_yaml(
        _property_candidates(model_name, class_name), properties_dir, recbole_module
    )
    result.update(
        {
            "ok": True,
            "class": class_name,
            "module": getattr(cls, "__module__", None),
            "model_type": _enum_name(model_type),
            "input_type": _enum_name(input_type),
            "property_yaml": prop,
            "property_source": prop_source,
            "property_candidates": candidates,
        }
    )

    try:
        trainer_cls = get_trainer(model_type, class_name)
        result["trainer"] = getattr(trainer_cls, "__name__", str(trainer_cls))
        result["trainer_module"] = getattr(trainer_cls, "__module__", None)
    except Exception as exc:
        result["trainer_error"] = f"{type(exc).__name__}: {exc}"

    if details:
        result["constructor_signature"] = _constructor_signature(cls)
        result["mro"] = _mro(cls)

    return result


def print_text(version: Optional[str], results: List[Dict[str, Any]]) -> None:
    print(f"RecBole version: {version or 'unknown'}")
    if not results:
        print("No model names were provided; pass one or more names to resolve them.")
        return
    for item in results:
        print(f"\n{item['query']}:")
        if not item.get("ok"):
            print(f"  status: ERROR ({item.get('error_type')})")
            print(f"  error: {item.get('error')}")
            print("  property_candidates: " + ", ".join(item.get("property_candidates", [])))
            continue
        print("  status: OK")
        print(f"  class: {item.get('class')}")
        print(f"  module: {item.get('module')}")
        print(f"  model_type: {item.get('model_type')}")
        print(f"  input_type: {item.get('input_type')}")
        if item.get("trainer_error"):
            print(f"  trainer_error: {item.get('trainer_error')}")
        else:
            print(f"  trainer: {item.get('trainer')} ({item.get('trainer_module')})")
        prop = item.get("property_yaml")
        if prop:
            print(f"  property_yaml: {prop} [{item.get('property_source')}]")
        else:
            print(
                "  property_yaml: not found; candidates: "
                + ", ".join(item.get("property_candidates", []))
            )
        if "constructor_signature" in item:
            print(f"  constructor_signature: {item.get('constructor_signature')}")
        if "mro" in item:
            print("  mro: " + " -> ".join(item.get("mro") or []))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect installed RecBole model registry resolution.",
    )
    parser.add_argument(
        "models",
        nargs="*",
        help="One or more RecBole model names, for example BPR SASRec FM KGAT.",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Print constructor signature and MRO for resolved model classes.",
    )
    parser.add_argument(
        "--properties-dir",
        type=Path,
        default=None,
        help="Optional directory containing RecBole model-property YAML files.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        recbole_module, get_model, get_trainer, version = _import_recbole()
    except RuntimeError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    results = [
        inspect_one(
            model_name,
            recbole_module,
            get_model,
            get_trainer,
            args.properties_dir,
            args.details,
        )
        for model_name in args.models
    ]
    if args.json:
        print(json.dumps({"ok": True, "recbole_version": version, "models": results}, indent=2))
    else:
        print_text(version, results)
    return 0 if all(item.get("ok") for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
