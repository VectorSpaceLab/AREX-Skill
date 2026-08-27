#!/usr/bin/env python3
"""Scan Lightning-Hydra-Template YAML configs for _target_ imports."""

from __future__ import annotations

import argparse
import importlib
import os
import re
import sys
from pathlib import Path
from typing import Iterable

TARGET_RE = re.compile(r"^\s*_target_\s*:\s*['\"]?([^'\"#\s]+)", re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Target project root.")
    parser.add_argument(
        "--config",
        action="append",
        default=[],
        help="Config YAML path relative to repo root. Defaults to all configs/**/*.yaml.",
    )
    parser.add_argument("--allow-missing-optional", action="store_true", help="Warn instead of failing for logger callback targets with missing optional packages.")
    return parser.parse_args()


def iter_configs(root: Path, selected: Iterable[str]) -> list[Path]:
    if selected:
        return [root / p for p in selected]
    return sorted((root / "configs").glob("**/*.yaml"))


def import_target(target: str) -> tuple[bool, str]:
    module_name, _, attr = target.rpartition(".")
    if not module_name or not attr:
        return False, "target is not a dotted module attribute"
    try:
        module = importlib.import_module(module_name)
        getattr(module, attr)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    return True, "ok"


def main() -> None:
    args = parse_args()
    root = Path(args.repo_root).expanduser().resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.environ.setdefault("PROJECT_ROOT", str(root))
    configs = iter_configs(root, args.config)
    if not configs:
        raise SystemExit("No config YAML files found")

    failures = []
    for path in configs:
        rel = path.relative_to(root) if path.is_relative_to(root) else path
        text = path.read_text(encoding="utf-8")
        targets = TARGET_RE.findall(text)
        for target in targets:
            ok, msg = import_target(target)
            status = "OK" if ok else "FAIL"
            print(f"{status} {rel}: {target} ({msg})")
            if not ok:
                optional_surface = any(part in str(rel) for part in ["configs/logger", "configs/callbacks"])
                if args.allow_missing_optional and optional_surface:
                    continue
                failures.append((str(rel), target, msg))
    if failures:
        print("\nFailed targets:")
        for rel, target, msg in failures:
            print(f"- {rel}: {target}: {msg}")
        raise SystemExit(1)
    print("All discovered _target_ imports resolved.")


if __name__ == "__main__":
    main()
