#!/usr/bin/env python3
"""Check the Paddle Inference Python API and optionally a static-file manifest.

The script does not create a predictor, execute a model, install dependencies,
read arbitrary checkpoint serialization, or write files. A model-prefix check
only verifies the three expected files are present and non-empty.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


STATIC_SUFFIXES = (".pdmodel", ".pdiparams", ".pdiparams.info")


def _file_record(path: Path) -> Dict[str, Any]:
    """Describe a path without opening its contents."""
    exists = path.is_file()
    size = path.stat().st_size if exists else None
    return {"path": str(path), "exists": exists, "nonempty": bool(size), "size": size}


def main() -> int:
    """Run the read-only Paddle Inference API check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-prefix",
        type=Path,
        help="optional static export prefix, without .pdmodel/.pdiparams suffix",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    report: Dict[str, Any] = {
        "import": {"ok": False},
        "static_manifest": None,
        "side_effects": "none: no network, model execution, writes, or environment mutation",
    }
    try:
        import paddle  # type: ignore
        import paddle.inference as paddle_infer  # type: ignore

        symbols = {
            "Config": hasattr(paddle_infer, "Config"),
            "create_predictor": hasattr(paddle_infer, "create_predictor"),
        }
        report["import"] = {
            "ok": all(symbols.values()),
            "paddle_version": getattr(paddle, "__version__", "unknown"),
            "symbols": symbols,
        }
    except Exception as exc:
        detail = str(exc).splitlines()[0] if str(exc) else "no detail"
        report["import"] = {
            "ok": False,
            "error": {"type": type(exc).__name__, "detail": detail[:500]},
        }

    if args.model_prefix:
        prefix = args.model_prefix
        if prefix.name.endswith(STATIC_SUFFIXES):
            report["static_manifest"] = {
                "ok": False,
                "error": "pass a prefix, not a path ending in .pdmodel/.pdiparams/.pdiparams.info",
            }
        else:
            files: List[Dict[str, Any]] = [
                _file_record(Path(str(prefix) + suffix)) for suffix in STATIC_SUFFIXES
            ]
            report["static_manifest"] = {"ok": all(f["exists"] and f["nonempty"] for f in files), "files": files}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Paddle Inference API probe (read-only)")
        print(f"Import: {report['import']}")
        if report["static_manifest"] is not None:
            print(f"Static manifest: {report['static_manifest']}")
        print(report["side_effects"])

    if not report["import"]["ok"]:
        return 2
    if report["static_manifest"] is not None and not report["static_manifest"]["ok"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
