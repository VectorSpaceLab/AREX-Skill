#!/usr/bin/env python3
"""Inspect installed MarkItDown plugin entry points.

This checker uses installed package metadata. It does not read any MarkItDown
source checkout or sample plugin source tree. By default it does not import the
plugin target; pass --import-module when import/register diagnostics are needed.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from dataclasses import dataclass
from importlib import metadata
from types import ModuleType
from typing import Iterable, Sequence

PLUGIN_GROUP = "markitdown.plugin"


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect installed MarkItDown plugin entry points."
    )
    parser.add_argument(
        "--plugin",
        help="Entry point name to inspect, such as sample_plugin or ocr.",
    )
    parser.add_argument(
        "--module",
        help="Expected import target module, such as my_markitdown_plugin.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all installed MarkItDown plugin entry points.",
    )
    parser.add_argument(
        "--import-module",
        action="store_true",
        help="Import the selected entry point target and inspect plugin hooks.",
    )
    parser.add_argument(
        "--check-register",
        action="store_true",
        help="Also verify that the imported module exposes a callable register_converters hook. Does not call the hook.",
    )
    parser.add_argument(
        "--expect-interface-version",
        type=int,
        default=1,
        help="Expected __plugin_interface_version__ value when the module is imported. Default: 1.",
    )
    return parser.parse_args(argv)


def plugin_entry_points() -> list[metadata.EntryPoint]:
    return list(metadata.entry_points(group=PLUGIN_GROUP))


def module_from_value(value: str) -> str:
    module_name = value.split(":", 1)[0]
    module_name = module_name.split("[", 1)[0]
    return module_name.strip()


def find_entry_point(
    entry_points: Iterable[metadata.EntryPoint], plugin: str | None
) -> metadata.EntryPoint | None:
    if plugin is None:
        return None
    for entry_point in entry_points:
        if entry_point.name == plugin:
            return entry_point
    return None


def print_entry_points(entry_points: Sequence[metadata.EntryPoint]) -> None:
    if not entry_points:
        print(f"No installed entry points found in group {PLUGIN_GROUP!r}.")
        return
    print(f"Installed {PLUGIN_GROUP} entry points:")
    for entry_point in sorted(entry_points, key=lambda item: item.name):
        dist_name = "unknown distribution"
        if entry_point.dist is not None:
            dist_name = entry_point.dist.metadata.get("Name", dist_name)
        print(f"  - {entry_point.name}: {entry_point.value} ({dist_name})")


def import_entry_point(entry_point: metadata.EntryPoint) -> tuple[ModuleType | object | None, str | None]:
    try:
        loaded = entry_point.load()
    except Exception as exc:  # noqa: BLE001 - diagnostic command should report any import/load failure.
        return None, f"entry point load failed: {exc}"
    return loaded, None


def import_expected_module(module_name: str) -> tuple[ModuleType | None, str | None]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostic command should report any import failure.
        return None, f"module import failed: {exc}"
    return module, None


def inspect_loaded_plugin(
    plugin_object: object,
    expected_interface_version: int,
    check_register: bool,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    interface_version = getattr(plugin_object, "__plugin_interface_version__", None)
    if interface_version == expected_interface_version:
        results.append(
            CheckResult(
                "interface version",
                True,
                f"__plugin_interface_version__ is {expected_interface_version}",
            )
        )
    else:
        results.append(
            CheckResult(
                "interface version",
                False,
                f"expected {expected_interface_version}, got {interface_version!r}",
            )
        )

    register_converters = getattr(plugin_object, "register_converters", None)
    if callable(register_converters):
        results.append(
            CheckResult("register hook", True, "register_converters is callable")
        )
    elif check_register:
        results.append(
            CheckResult("register hook", False, "register_converters is missing or not callable")
        )
    else:
        results.append(
            CheckResult(
                "register hook",
                True,
                "register_converters is missing or not callable; informational unless --check-register is set",
            )
        )
    return results


def print_results(results: Iterable[CheckResult]) -> bool:
    ok = True
    for result in results:
        status = "OK" if result.ok else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
        ok = ok and result.ok
    return ok


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    entry_points = plugin_entry_points()

    if args.list or (args.plugin is None and args.module is None):
        print_entry_points(entry_points)
        if args.plugin is None and args.module is None:
            return 0

    results: list[CheckResult] = []

    selected_entry_point = find_entry_point(entry_points, args.plugin)
    if args.plugin is not None:
        if selected_entry_point is None:
            available = ", ".join(sorted(item.name for item in entry_points)) or "none"
            results.append(
                CheckResult(
                    "entry point",
                    False,
                    f"{args.plugin!r} not found in group {PLUGIN_GROUP!r}; available: {available}",
                )
            )
        else:
            results.append(
                CheckResult(
                    "entry point",
                    True,
                    f"{selected_entry_point.name} = {selected_entry_point.value}",
                )
            )
            if args.module is not None:
                actual_module = module_from_value(selected_entry_point.value)
                results.append(
                    CheckResult(
                        "entry point target",
                        actual_module == args.module,
                        f"expected {args.module!r}, found {actual_module!r}",
                    )
                )

    plugin_object: object | None = None
    import_error: str | None = None
    if args.import_module or args.check_register:
        if selected_entry_point is not None:
            plugin_object, import_error = import_entry_point(selected_entry_point)
            import_name = selected_entry_point.value
        elif args.module is not None:
            plugin_object, import_error = import_expected_module(args.module)
            import_name = args.module
        else:
            import_name = ""
            import_error = "provide --plugin or --module with --import-module"

        if import_error is not None:
            results.append(CheckResult("import", False, import_error))
        else:
            results.append(CheckResult("import", True, f"loaded {import_name}"))
            if plugin_object is not None:
                results.extend(
                    inspect_loaded_plugin(
                        plugin_object,
                        args.expect_interface_version,
                        check_register=args.check_register,
                    )
                )

    ok = print_results(results)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
