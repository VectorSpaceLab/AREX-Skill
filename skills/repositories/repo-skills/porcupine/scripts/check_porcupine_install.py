#!/usr/bin/env python3
"""Check a Porcupine Python installation without requiring an AccessKey.

This root helper is intentionally small and safe. It verifies that the
`pvporcupine` package imports, reports packaged built-in keywords, resolves the
native library/model assets, and can list available inference devices.
"""

from __future__ import annotations

import argparse
import json
import os
import sys


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Safe Porcupine Python install/device check")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of human-readable lines")
    parser.add_argument("--library-path", help="optional native library override for device enumeration")
    args = parser.parse_args(argv)

    try:
        import pvporcupine  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on caller env
        print(f"ERROR: could not import pvporcupine: {exc}", file=sys.stderr)
        return 1

    try:
        library_path = args.library_path or pvporcupine.pv_library_path()
        model_path = pvporcupine.pv_model_path()
        devices = list(pvporcupine.available_devices(library_path=library_path))
        result = {
            "package": "pvporcupine",
            "keywords_count": len(pvporcupine.KEYWORDS),
            "sample_keywords": sorted(pvporcupine.KEYWORDS)[:10],
            "library_exists": os.path.exists(library_path),
            "model_exists": os.path.exists(model_path),
            "devices": devices,
        }
    except Exception as exc:  # pragma: no cover - depends on native library state
        print(f"ERROR: pvporcupine imported but safe device/asset check failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("pvporcupine import: ok")
        print(f"built-in keywords: {result['keywords_count']} ({', '.join(result['sample_keywords'])})")
        print(f"native library exists: {result['library_exists']}")
        print(f"default model exists: {result['model_exists']}")
        print("available devices:")
        for device in devices:
            print(f"  - {device}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
