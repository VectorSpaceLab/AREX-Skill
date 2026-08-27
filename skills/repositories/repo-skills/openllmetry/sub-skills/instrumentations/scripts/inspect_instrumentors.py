#!/usr/bin/env python3
"""Inspect OpenLLMetry instrumentation packages from a checkout or installed metadata.

This helper is read-only. It parses local `pyproject.toml` files and, when asked,
reads installed distribution metadata through `importlib.metadata`. It never
installs packages, imports target clients, or uses the network.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise SystemExit("Python 3.11+ or the tomli package is required") from exc


@dataclass(slots=True)
class InstrumentorRecord:
    distribution: str
    package_dir: str
    version: str | None
    description: str | None
    import_module: str
    instrumentor_class: str
    entry_point_name: str
    entry_point_target: str
    instruments_extra: list[str]
    other_extras: dict[str, list[str]]
    installed_version: str | None = None
    installed_entry_points: dict[str, str] | None = None


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _walk_up_for_packages(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "packages").is_dir():
            return candidate
    return None


def _repo_root_from_args(repo_root_arg: Path | None) -> Path:
    if repo_root_arg is not None:
        resolved = repo_root_arg.expanduser().resolve()
        if not (resolved / "packages").is_dir():
            raise SystemExit("error: --repo-root must point to an OpenLLMetry checkout root")
        return resolved

    discovered = _walk_up_for_packages(Path.cwd().resolve())
    if discovered is not None:
        return discovered

    script_root = _walk_up_for_packages(Path(__file__).resolve().parent)
    if script_root is not None:
        return script_root

    raise SystemExit("error: could not locate an OpenLLMetry checkout; pass --repo-root")


def _collect_pyproject_records(repo_root: Path) -> list[InstrumentorRecord]:
    records: list[InstrumentorRecord] = []
    for package_dir in sorted((repo_root / "packages").glob("opentelemetry-instrumentation-*")):
        pyproject = package_dir / "pyproject.toml"
        if not pyproject.exists():
            continue
        data = _load_toml(pyproject)
        project = data.get("project", {})
        entry_points = project.get("entry-points", {}).get("opentelemetry_instrumentor", {})
        if not entry_points:
            continue
        entry_point_name, entry_point_target = next(iter(entry_points.items()))
        import_module, instrumentor_class = entry_point_target.split(":", 1)
        optional_dependencies = project.get("optional-dependencies", {})
        instruments_extra = list(optional_dependencies.get("instruments", []))
        other_extras = {
            name: list(values)
            for name, values in optional_dependencies.items()
            if name != "instruments"
        }
        records.append(
            InstrumentorRecord(
                distribution=project.get("name", package_dir.name),
                package_dir=package_dir.relative_to(repo_root).as_posix(),
                version=project.get("version"),
                description=project.get("description"),
                import_module=import_module,
                instrumentor_class=instrumentor_class,
                entry_point_name=entry_point_name,
                entry_point_target=entry_point_target,
                instruments_extra=instruments_extra,
                other_extras=other_extras,
            )
        )
    return records


def _installed_metadata(distribution: str) -> tuple[str | None, dict[str, str] | None]:
    try:
        dist = importlib_metadata.distribution(distribution)
    except importlib_metadata.PackageNotFoundError:
        return None, None

    installed_eps = {
        entry_point.name: f"{entry_point.value}"
        for entry_point in dist.entry_points
        if entry_point.group == "opentelemetry_instrumentor"
    }
    return dist.version, installed_eps or None


def _records_with_installed_metadata(records: list[InstrumentorRecord]) -> list[InstrumentorRecord]:
    augmented: list[InstrumentorRecord] = []
    for record in records:
        installed_version, installed_entry_points = _installed_metadata(record.distribution)
        augmented.append(
            InstrumentorRecord(
                **{
                    **asdict(record),
                    "installed_version": installed_version,
                    "installed_entry_points": installed_entry_points,
                }
            )
        )
    return augmented


def _summary(records: list[InstrumentorRecord]) -> dict[str, Any]:
    installed = sum(1 for record in records if record.installed_version)
    return {
        "package_count": len(records),
        "installed_count": installed,
        "missing_count": len(records) - installed,
    }


def _print_text(repo_root: Path, records: list[InstrumentorRecord]) -> None:
    summary = _summary(records)
    print(
        f"OpenLLMetry instrumentation packages: {summary['package_count']} found under {repo_root.as_posix()}"
    )
    print(
        f"Installed metadata available for {summary['installed_count']} packages; "
        f"{summary['missing_count']} are not installed in the current environment"
    )
    for record in records:
        extras = [", ".join(record.instruments_extra) if record.instruments_extra else "-"]
        for name, values in record.other_extras.items():
            extras.append(f"{name}: {', '.join(values)}")
        extras_text = "; ".join(extras)
        installed_text = f" [installed {record.installed_version}]" if record.installed_version else ""
        print()
        print(f"{record.distribution}{installed_text}")
        print(f"  package dir: {record.package_dir}")
        print(f"  import: {record.import_module}:{record.instrumentor_class}")
        print(f"  entry point: {record.entry_point_name} = {record.entry_point_target}")
        print(f"  extras: {extras_text}")
        if record.installed_entry_points:
            print("  installed instrumentor entry points:")
            for name, target in sorted(record.installed_entry_points.items()):
                print(f"    {name} = {target}")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect OpenLLMetry instrumentation packages from a checkout and/or installed metadata."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Path to the OpenLLMetry checkout root. If omitted, the script searches upward from the current directory.",
    )
    parser.add_argument(
        "--installed",
        action="store_true",
        help="Also inspect installed distribution metadata for each package.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = _repo_root_from_args(args.repo_root)
    records = _collect_pyproject_records(repo_root)
    if args.installed:
        records = _records_with_installed_metadata(records)
    else:
        records = [
            InstrumentorRecord(
                **{
                    **asdict(record),
                    "installed_version": None,
                    "installed_entry_points": None,
                }
            )
            for record in records
        ]

    if args.json:
        print(
            json.dumps(
                {
                    "repo_root": repo_root.as_posix(),
                    "summary": _summary(records),
                    "packages": [asdict(record) for record in records],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        _print_text(repo_root, records)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:  # pragma: no cover - friendly pipeline exit
        raise SystemExit(0)
