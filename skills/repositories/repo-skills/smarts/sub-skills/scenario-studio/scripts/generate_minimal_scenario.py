#!/usr/bin/env python3
"""Generate a bounded, local SMARTS map-only scenario into an explicit path.

The helper uses ``gen_scenario`` with a local MapSpec and no traffic, missions,
SUMO process, TraCI connection, network download, or package installation. It
generates in a temporary sibling directory and publishes only after generation
succeeds. A non-empty output is refused unless ``--force`` is explicit.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path


def _publish(staged: Path, output: Path, force: bool) -> None:
    backup: Path | None = None
    if output.exists():
        if not force:
            raise FileExistsError(
                f"output already exists (use --force to replace it): {output}"
            )
        if output.is_file():
            raise FileExistsError(f"output is a file, refusing to replace: {output}")
        backup = output.with_name(f".{output.name}.backup-{uuid.uuid4().hex[:8]}")
        output.rename(backup)
    try:
        staged.rename(output)
    except Exception:
        if backup is not None and not output.exists():
            backup.rename(output)
        raise
    if backup is not None:
        shutil.rmtree(backup)


def generate(map_path: Path, output: Path, seed: int, force: bool) -> None:
    if not map_path.exists() or not map_path.is_file():
        raise FileNotFoundError(f"local map file does not exist: {map_path}")
    if map_path.suffix.lower() not in {".xodr"} and not map_path.name.endswith(".net.xml"):
        raise ValueError(
            "--map must be a local .net.xml SUMO map or .xodr OpenDRIVE map; "
            "dataset and URI inputs are intentionally not accepted"
        )
    output = output.expanduser().resolve()
    map_path = map_path.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    # Import only after path checks so --help and invalid-input checks do not
    # require optional map backends.
    try:
        from smarts.sstudio import gen_scenario, types as t
    except Exception as exc:  # pragma: no cover - depends on installation
        raise RuntimeError(f"SMARTS Scenario Studio import failed: {exc}") from exc

    staged: Path | None = None
    try:
        with tempfile.TemporaryDirectory(
            prefix="scenario-studio-", dir=str(output.parent)
        ) as temp_dir:
            staged = Path(temp_dir) / "scenario"
            scenario = t.Scenario(map_spec=t.MapSpec(source=str(map_path)))
            try:
                gen_scenario(scenario, staged, seed=seed)
            except Exception as exc:
                raise RuntimeError(
                    "local map generation failed; check the map format and optional "
                    f"backend (no SUMO/TraCI service was started): {exc}"
                ) from exc
            required = [staged / "build" / "build.db", staged / "build" / "map" / "map.glb"]
            missing = [str(path.relative_to(staged)) for path in required if not path.is_file()]
            if missing:
                raise RuntimeError(
                    "generation returned without required artifacts: " + ", ".join(missing)
                )
            _publish(staged, output, force)
            staged = None
    finally:
        # TemporaryDirectory removes a failed or unpublished stage. This branch
        # is defensive if publishing raised after moving a partial directory.
        if staged is not None and staged.exists():
            shutil.rmtree(staged, ignore_errors=True)


def self_test() -> int:
    try:
        from smarts.sstudio import types as t

        spec = t.MapSpec(source="/tmp/example.map.xodr")
        scenario = t.Scenario(map_spec=spec)
        assert scenario.map_spec.source.endswith(".xodr")
    except Exception as exc:
        print(f"SELF-TEST FAILED: {exc}", file=sys.stderr)
        return 1
    print("SELF-TEST OK: Scenario and MapSpec constructors are importable")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a safe local SMARTS map-only scenario (no external service)."
    )
    parser.add_argument("--map", type=Path, help="explicit local .net.xml or .xodr map")
    parser.add_argument("--output", type=Path, help="explicit output scenario directory")
    parser.add_argument("--seed", type=int, default=42, help="generation seed (default: 42)")
    parser.add_argument("--force", action="store_true", help="replace an existing output directory")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="import and construct tiny DSL objects without generating files",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.map is None or args.output is None:
        parser.error("--map and --output are required unless --self-test is used")
    try:
        generate(args.map, args.output, args.seed, args.force)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"GENERATED: {args.output.expanduser().resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
