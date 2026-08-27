#!/usr/bin/env python3
"""Offline probe for pymatgen external-data client imports and key shape.

This script intentionally performs no network calls. It imports the external
client classes, reports public constructor signatures, checks PMG_MAPI_KEY shape
without printing the key, and exercises OPTIMADE filter construction offline.
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import sys
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def _key_status() -> dict[str, object]:
    raw_key = os.environ.get("PMG_MAPI_KEY")
    if raw_key is None:
        return {"present": False, "length": 0, "valid_shape": False}

    key = raw_key.strip()
    return {"present": True, "length": len(key), "valid_shape": len(key) == 32}


def _key_status_text(status: dict[str, object]) -> str:
    return " ".join(f"{key}={value}" for key, value in status.items())


def _import_checks() -> list[CheckResult]:
    results: list[CheckResult] = []

    try:
        from pymatgen.ext.matproj import MPRester  # noqa: PLC0415

        results.append(CheckResult("MPRester import", True, str(inspect.signature(MPRester))))
    except Exception as exc:  # pragma: no cover - diagnostic path
        results.append(CheckResult("MPRester import", False, f"{type(exc).__name__}: {exc}"))

    try:
        from pymatgen.ext.cod import COD  # noqa: PLC0415

        results.append(CheckResult("COD import", True, str(inspect.signature(COD))))
    except Exception as exc:  # pragma: no cover - diagnostic path
        results.append(CheckResult("COD import", False, f"{type(exc).__name__}: {exc}"))

    try:
        from pymatgen.ext.optimade import OptimadeRester  # noqa: PLC0415

        results.append(CheckResult("OptimadeRester import", True, str(inspect.signature(OptimadeRester))))
        offline_filter = OptimadeRester._build_filter(elements=["Ga", "N"], nelements=2, nsites=(1, 100))
        results.append(CheckResult("OPTIMADE offline filter", True, offline_filter))
        aliases = ", ".join(
            sorted(alias for alias in OptimadeRester.aliases if alias in {"mp", "cod", "aflow", "oqmd", "jarvis"})
        )
        results.append(CheckResult("OPTIMADE common aliases", True, aliases or "no common aliases found"))
    except Exception as exc:  # pragma: no cover - diagnostic path
        results.append(CheckResult("OptimadeRester import/filter", False, f"{type(exc).__name__}: {exc}"))

    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline pymatgen external-data probe. Makes no network calls and prints no secrets.",
    )
    parser.add_argument(
        "--expect-mp-key",
        action="store_true",
        help="Return non-zero if PMG_MAPI_KEY is absent or not 32 characters after stripping whitespace.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args(argv)

    key_status = _key_status()
    results = _import_checks()
    failed = any(not result.ok for result in results)

    if args.expect_mp_key and not key_status["valid_shape"]:
        results.append(CheckResult("PMG_MAPI_KEY expected", False, "valid_shape=False"))
        failed = True

    report = {
        "network_calls": False,
        "pmg_mapi_key": key_status,
        "checks": [asdict(result) for result in results],
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("network_calls=False")
        print(f"PMG_MAPI_KEY {_key_status_text(key_status)}")
        for result in results:
            status = "ok" if result.ok else "FAIL"
            print(f"{status}: {result.name}: {result.detail}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
