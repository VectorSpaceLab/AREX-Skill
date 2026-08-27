#!/usr/bin/env python3
"""Check a PettingZoo installation and optional family imports safely.

This helper performs import and metadata checks only by default. It does not
install packages, acquire ROMs, render GUI windows, run training, or mutate the
current environment.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys
from dataclasses import dataclass
from typing import Any

FAMILY_MODULES = {
    "classic": "pettingzoo.classic.rps_v2",
    "butterfly": "pettingzoo.butterfly.pistonball_v6",
    "atari": "pettingzoo.atari.space_invaders_v2",
    "sisl": "pettingzoo.sisl.multiwalker_v9",
}

FAMILY_EXTRAS = {
    "classic": "pettingzoo[classic]",
    "butterfly": "pettingzoo[butterfly]",
    "atari": "pettingzoo[atari] plus ROM setup when constructing Atari envs",
    "sisl": "pettingzoo[sisl]",
}


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    advice: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = {"name": self.name, "ok": self.ok, "detail": self.detail}
        if self.advice:
            payload["advice"] = self.advice
        return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely check PettingZoo base install and optional family imports.",
    )
    parser.add_argument(
        "--families",
        default="classic,butterfly,atari,sisl",
        help="Comma-separated optional family import probes to run, or 'none'.",
    )
    parser.add_argument(
        "--constructor-probe",
        action="store_true",
        help="Also call env() or parallel_env() without reset for imported family modules. This may surface ROM or optional dependency errors.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    return parser.parse_args()


def import_module(path: str) -> tuple[bool, str, str | None]:
    try:
        importlib.import_module(path)
    except ModuleNotFoundError as exc:
        missing = exc.name or "unknown"
        return False, f"missing module {missing!r}", missing
    except Exception as exc:  # keep import probe user-facing
        return False, f"{type(exc).__name__}: {exc}", None
    return True, "import ok", None


def check_base() -> list[CheckResult]:
    results: list[CheckResult] = []
    ok, detail, missing = import_module("pettingzoo")
    advice = None if ok else "Install base PettingZoo in this Python: pip install pettingzoo."
    if missing in {"numpy", "gymnasium"}:
        advice = "Base PettingZoo dependencies are missing; reinstall pettingzoo in this Python."
    results.append(CheckResult("import pettingzoo", ok, detail, advice))

    try:
        version = metadata.version("pettingzoo")
    except metadata.PackageNotFoundError:
        results.append(
            CheckResult(
                "distribution pettingzoo",
                False,
                "distribution metadata not found",
                "Install the pettingzoo distribution, not only a source directory on sys.path.",
            )
        )
    else:
        results.append(CheckResult("distribution pettingzoo", True, version))
    return results


def check_family(name: str, constructor_probe: bool) -> CheckResult:
    module_path = FAMILY_MODULES[name]
    ok, detail, missing = import_module(module_path)
    if not ok:
        advice = f"Install the matching optional extra: {FAMILY_EXTRAS[name]}."
        if name == "atari" and missing not in {"multi_agent_ale_py", "pygame", "pygame_ce"}:
            advice += " If import succeeds but construction fails later, check ROM setup separately."
        return CheckResult(f"family {name}", False, f"{module_path}: {detail}", advice)

    if not constructor_probe:
        return CheckResult(f"family {name}", True, f"{module_path}: import ok")

    try:
        module = importlib.import_module(module_path)
        factory = getattr(module, "parallel_env", None) or getattr(module, "env")
        env = factory()
        close = getattr(env, "close", None)
        if callable(close):
            close()
    except Exception as exc:
        advice = f"Import works, but constructor probe failed. Check optional runtime resources for {name}."
        if name == "atari":
            advice = "Import works, but Atari constructors may need ROMs via AutoROM, rom_path, or auto_rom_install_path."
        return CheckResult(f"family {name}", False, f"constructor failed: {type(exc).__name__}: {exc}", advice)
    return CheckResult(f"family {name}", True, f"{module_path}: constructor ok")


def main() -> int:
    args = parse_args()
    results = check_base()
    if args.families.lower() != "none":
        requested = [item.strip() for item in args.families.split(",") if item.strip()]
        unknown = [item for item in requested if item not in FAMILY_MODULES]
        if unknown:
            raise SystemExit(f"Unknown families: {', '.join(unknown)}")
        for family in requested:
            results.append(check_family(family, args.constructor_probe))

    if args.json:
        print(json.dumps([result.as_dict() for result in results], indent=2, sort_keys=True))
    else:
        for result in results:
            status = "OK" if result.ok else "FAIL"
            print(f"[{status}] {result.name}: {result.detail}")
            if result.advice:
                print(f"  advice: {result.advice}")

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
