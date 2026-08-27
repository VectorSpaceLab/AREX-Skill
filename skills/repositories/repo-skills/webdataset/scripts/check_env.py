#!/usr/bin/env python3
"""Check that a Python environment can use the WebDataset repo skill.

This helper is intentionally self-contained: it imports the installed
``webdataset`` package, reports optional dependency availability, and runs a
small local TarWriter/WebDataset round-trip without reading the original source
checkout or downloading data.
"""

from __future__ import annotations

import argparse
import importlib
import json
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict, List


def normalize(value: Any) -> Any:
    """Convert arrays/tensors and tuples into JSON-friendly values."""

    if isinstance(value, bytes):
        return value.decode("utf-8")
    if hasattr(value, "tolist") and not isinstance(value, (str, bytes)):
        return value.tolist()
    if isinstance(value, tuple):
        return [normalize(item) for item in value]
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    return value


def module_status(name: str) -> Dict[str, Any]:
    """Return import status and optional version for one module."""

    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "available": True,
        "version": getattr(module, "__version__", None),
    }


def roundtrip_check() -> Dict[str, Any]:
    """Write and read one tiny local WebDataset shard."""

    import webdataset as wds

    with tempfile.TemporaryDirectory(prefix="webdataset-env-check-") as tmp:
        tar_path = Path(tmp) / "tiny.tar"
        with wds.TarWriter(str(tar_path), mtime=0) as sink:
            sink.write({"__key__": "sample000", "txt": "hello", "json": {"label": 3}})
        row = normalize(next(iter(wds.WebDataset(str(tar_path), shardshuffle=False).decode().to_tuple("txt", "json"))))
    expected = ["hello", {"label": 3}]
    if row != expected:
        raise AssertionError(f"round-trip mismatch: expected {expected!r}, got {row!r}")
    return {"ok": True, "row": row}


def inspect_webdataset(skip_roundtrip: bool) -> Dict[str, Any]:
    """Collect package, optional dependency, and smoke-check facts."""

    summary: Dict[str, Any] = {"ok": True, "checks": {}}
    try:
        from importlib.metadata import version

        import webdataset as wds

        gopen_mod = importlib.import_module("webdataset.gopen")
        summary["webdataset"] = {
            "distribution_version": version("webdataset"),
            "module_version": getattr(wds, "__version__", None),
            "exports": {
                "WebDataset": hasattr(wds, "WebDataset"),
                "DataPipeline": hasattr(wds, "DataPipeline"),
                "WebLoader": hasattr(wds, "WebLoader"),
                "TarWriter": hasattr(wds, "TarWriter"),
                "ShardWriter": hasattr(wds, "ShardWriter"),
                "gopen": hasattr(wds, "gopen"),
            },
            "gopen_schemes": sorted(str(name) for name in gopen_mod.gopen_schemes.keys()),
        }
    except Exception as exc:
        summary["ok"] = False
        summary["checks"]["import_webdataset"] = {
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }
        return summary

    for module_name in ["numpy", "yaml", "braceexpand", "PIL", "torch", "imageio", "msgpack"]:
        summary.setdefault("optional_modules", {})[module_name] = module_status(module_name)

    if not skip_roundtrip:
        try:
            summary["checks"]["tiny_roundtrip"] = {"status": "ok", "result": roundtrip_check()}
        except Exception as exc:
            summary["ok"] = False
            summary["checks"]["tiny_roundtrip"] = {
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            }
    return summary


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check WebDataset importability and a tiny offline round-trip.")
    parser.add_argument("--skip-roundtrip", action="store_true", help="Only check imports and optional modules.")
    parser.add_argument("--require-torch", action="store_true", help="Exit non-zero when torch is unavailable.")
    args = parser.parse_args(argv)

    summary = inspect_webdataset(skip_roundtrip=args.skip_roundtrip)
    if args.require_torch and not summary.get("optional_modules", {}).get("torch", {}).get("available", False):
        summary["ok"] = False
        summary.setdefault("checks", {})["require_torch"] = {
            "status": "failed",
            "error": "torch is required by --require-torch but is not importable",
        }

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
